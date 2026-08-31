# agents/sandbox_executor.py

import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict

from state import AnalysisState

USE_E2B = False

try:
    from e2b_code_interpreter import Sandbox
except Exception:
    Sandbox = None


def _warm_up_kaleido():
    """Pre-launch Chromium once so later chart renders don't cold-start
    (a common cause of Kaleido hanging on the first write_image call)."""
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(x=[1], y=[1])])
        fig.write_image(os.path.join(tempfile.gettempdir(), "_kaleido_warmup.png"))
    except Exception as e:
        print(f"Sandbox Executor: Kaleido warm-up failed (non-fatal): {e}", flush=True)


class SandboxExecutorNode:
    """Runs LLM-generated chart code and extracts artifacts.

    IMPORTANT: this node runs on EVERY pass through the chart loop
    (once per chart, plus once per retry). It must return ONLY the keys
    it actually changed (rendered_image_path, execution_error,
    retry_count, artifact_warning) -- never the full state dict, and
    never final_ui_blocks/code_history/report_findings. Those use
    additive reducers in state.py; re-returning them here would double
    them on every single retry, which is what was causing the pipeline
    to stall after 2-3 charts.
    """

    def __init__(self, scratchpad_dir: str = "artifacts/scratchpad", timeout_seconds: int = 90):
        self.scratchpad_dir = scratchpad_dir
        self.timeout_seconds = timeout_seconds
        os.makedirs(self.scratchpad_dir, exist_ok=True)
        os.makedirs(os.path.join("artifacts", "charts"), exist_ok=True)
        _warm_up_kaleido()

    def _safe_remove(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def _cleanup_previous_artifacts(self) -> None:
        for file_name in ["latest_render.png", "latest_render.json"]:
            self._safe_remove(os.path.join(self.scratchpad_dir, file_name))

    def _extract_local_artifacts(self, current_chart_index: int) -> Dict[str, Any]:
        """Persists per-chart artifacts to disk and returns ONLY the
        lightweight file-path delta, keeping the LangGraph checkpoint
        payload small."""
        json_src = os.path.join(self.scratchpad_dir, "latest_render.json")
        png_src = os.path.join(self.scratchpad_dir, "latest_render.png")

        json_exists = os.path.exists(json_src)
        png_exists = os.path.exists(png_src)

        if not json_exists and not png_exists:
            raise Exception("Script executed but failed to save chart artifacts.")

        out_dir = os.path.join("artifacts", "charts")
        os.makedirs(out_dir, exist_ok=True)

        delta: Dict[str, Any] = {}

        if json_exists:
            json_dst = os.path.join(out_dir, f"chart_{current_chart_index}.json")
            os.replace(json_src, json_dst)
            delta["rendered_json_path"] = json_dst
        else:
            delta["rendered_json_path"] = None
            delta["artifact_warning"] = "PNG exists but Plotly JSON artifact is missing."

        if png_exists:
            png_dst = os.path.join(out_dir, f"chart_{current_chart_index}.png")
            os.replace(png_src, png_dst)
            delta["rendered_image_path"] = png_dst
        else:
            delta["rendered_image_path"] = None

        return delta

    def _extract_missing_modules(self, error_text: str) -> list:
        matches = re.findall(r"No module named ['\"]([^'\"]+)['\"]", error_text or "")
        return list(dict.fromkeys(matches)) if matches else []

    def _run_subprocess_with_hard_timeout(self, script_path: str):
        """Runs the script in its own process group so the ENTIRE tree
        (including any Chromium/Kaleido child) can be killed on timeout."""
        is_posix = os.name == "posix"

        popen_kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if is_posix:
            popen_kwargs["start_new_session"] = True
        else:
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen([sys.executable, script_path], **popen_kwargs)

        try:
            stdout, stderr = proc.communicate(timeout=self.timeout_seconds)
            return proc.returncode, stdout, stderr, False
        except subprocess.TimeoutExpired:
            print("Sandbox Executor: Timeout hit -> killing entire process tree.", flush=True)
            try:
                if is_posix:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.send_signal(signal.CTRL_BREAK_EVENT)
                    proc.kill()
            except Exception as kill_err:
                print(f"Sandbox Executor: Failed to kill process tree: {kill_err}", flush=True)

            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:
                stdout, stderr = "", ""
            return -1, stdout, stderr, True

    def _run_local(self, code_to_run: str, current_chart_index: int, retry_count: int) -> Dict[str, Any]:
        print("Sandbox Executor: Running LOCAL execution path...", flush=True)

        fd, script_path = tempfile.mkstemp(prefix="agent_exec_", suffix=".py")
        os.close(fd)
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code_to_run)

            start = time.time()
            print("Sandbox Executor: Subprocess started...", flush=True)
            returncode, stdout, stderr, timed_out = self._run_subprocess_with_hard_timeout(script_path)
            elapsed = time.time() - start
            print(f"Sandbox Executor: Subprocess finished in {elapsed:.1f}s (timed_out={timed_out})", flush=True)

            if timed_out:
                error = (
                    f"Local Runtime Timeout after {self.timeout_seconds}s (process tree killed).\n"
                    f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}\n\n"
                    "Likely cause: Kaleido/Chromium hung during fig.write_image()."
                )
                print(f"Sandbox Executor ERROR: {error}", flush=True)
                return {"execution_error": error, "retry_count": retry_count + 1}

            if returncode != 0:
                missing_modules = self._extract_missing_modules(stderr + "\n" + stdout)
                if missing_modules:
                    print(
                        f"Sandbox Executor: Missing Python packages detected: {missing_modules}. Installing automatically.",
                        flush=True,
                    )
                    install_start = time.time()
                    install_result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--quiet", *missing_modules],
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    print(f"Sandbox Executor: Pip install finished in {time.time() - install_start:.1f}s", flush=True)

                    if install_result.returncode == 0:
                        returncode, stdout, stderr, timed_out = self._run_subprocess_with_hard_timeout(script_path)
                    else:
                        error = (
                            f"Local Runtime Error:\nSTDOUT:\n{stdout.strip()}\n\n"
                            f"STDERR:\n{stderr.strip()}\n\n"
                            f"PIP INSTALL ERROR:\n{install_result.stdout.strip()}\n\n{install_result.stderr.strip()}"
                        )
                        print(f"Sandbox Executor ERROR: {error}", flush=True)
                        return {"execution_error": error, "retry_count": retry_count + 1}

            if returncode != 0:
                error = f"Local Runtime Error:\nSTDOUT:\n{stdout.strip()}\n\nSTDERR:\n{stderr.strip()}"
                print(f"Sandbox Executor ERROR: {error}", flush=True)
                return {"execution_error": error, "retry_count": retry_count + 1}

            artifact_delta = self._extract_local_artifacts(current_chart_index)
            print("Sandbox Executor: Local artifacts successfully extracted.", flush=True)
            return {**artifact_delta, "execution_error": None}

        finally:
            self._safe_remove(script_path)

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        code_to_run = state.get("current_code", "")
        current_chart_index = state.get("current_chart_index", 0)
        retry_count = state.get("retry_count", 0)
        print("Sandbox Executor: Starting execution...", flush=True)

        if not code_to_run:
            return {"execution_error": "No code provided.", "retry_count": retry_count + 1}

        self._cleanup_previous_artifacts()

        if USE_E2B and Sandbox is not None:
            try:
                print("Sandbox Executor: Trying E2B path...", flush=True)
                with Sandbox() as sandbox:
                    sandbox.commands.run("pip install -q duckdb pandas plotly kaleido openpyxl statsmodels")
                    sandbox.commands.run("mkdir -p data artifacts/scratchpad")

                    db_path = "data/analytics_engine.duckdb"
                    if os.path.exists(db_path):
                        with open(db_path, "rb") as f:
                            sandbox.files.write("data/analytics_engine.duckdb", f.read())

                    execution = (
                        sandbox.notebook.exec_cell(code_to_run)
                        if hasattr(sandbox, "notebook")
                        else sandbox.run_code(code_to_run)
                    )

                    if getattr(execution, "error", None):
                        error = execution.error
                        raise Exception(f"{error.name}: {error.value}\n{error.traceback}")

                    b64_cmd = sandbox.commands.run("base64 -w 0 artifacts/scratchpad/latest_render.png")
                    json_cmd = sandbox.commands.run("cat artifacts/scratchpad/latest_render.json")

                    if b64_cmd.error or json_cmd.error:
                        raise Exception("Remote artifact extraction failed.")

                    out_dir = os.path.join("artifacts", "charts")
                    os.makedirs(out_dir, exist_ok=True)

                    png_dst = os.path.join(out_dir, f"chart_{current_chart_index}.png")
                    json_dst = os.path.join(out_dir, f"chart_{current_chart_index}.json")

                    import base64
                    with open(png_dst, "wb") as f:
                        f.write(base64.b64decode(b64_cmd.stdout.strip()))
                    with open(json_dst, "w", encoding="utf-8") as f:
                        f.write(json_cmd.stdout.strip())

                    print("Sandbox Executor: E2B execution succeeded.", flush=True)
                    return {
                        "rendered_image_path": png_dst,
                        "rendered_json_path": json_dst,
                        "execution_error": None,
                        "retry_count": 0,
                    }

            except Exception as e:
                print(f"Sandbox Executor: E2B failed, falling back to local -> {str(e)}", flush=True)

        return self._run_local(code_to_run, current_chart_index, retry_count)

    def shutdown(self):
        # No long-lived resources; included for API teardown compatibility.
        pass