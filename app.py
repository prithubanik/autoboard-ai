import json
import requests
import streamlit as st
import plotly.io as pio
import pandas as pd

API_URL = "http://localhost:8000/api/v1/analyze/stream"

st.set_page_config(page_title="Executive Multimodal Analytics", layout="wide")

if "report_blocks" not in st.session_state:
    st.session_state.report_blocks = []
if "seen_block_ids" not in st.session_state:
    st.session_state.seen_block_ids = set()
if "run_nonce" not in st.session_state:
    st.session_state.run_nonce = 0
if "render_counter" not in st.session_state:
    st.session_state.render_counter = 0


def reset_run_state():
    st.session_state.report_blocks = []
    st.session_state.seen_block_ids = set()
    st.session_state.run_nonce += 1
    st.session_state.render_counter = 0


def add_blocks(blocks):
    new_blocks = []
    for block in blocks:
        block_id = block.get("id")
        if block_id and block_id not in st.session_state.seen_block_ids:
            st.session_state.seen_block_ids.add(block_id)
            st.session_state.report_blocks.append(block)
            new_blocks.append(block)
    return new_blocks


def render_single_block(block):
    st.session_state.render_counter += 1
    seq = st.session_state.render_counter
    block_type = block.get("type", "")

    if block_type == "MarkdownBlock":
        st.subheader(block.get("title", "Report Section"))
        st.markdown(block.get("content", ""))
        st.divider()
        return

    if block_type == "MetricGridBlock":
        st.subheader(block.get("title", "Key Metrics"))
        metrics = block.get("metrics", [])
        if metrics:
            cols = st.columns(min(4, len(metrics)))
            for i, metric in enumerate(metrics):
                with cols[i % len(cols)]:
                    st.metric(metric.get("label", "Metric"), metric.get("value", "-"), metric.get("delta"))
        st.divider()
        return

    if block_type == "DataFrameBlock":
        st.subheader(block.get("title", "Preview"))
        rows = block.get("rows", [])
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.divider()
        return

    if block_type == "VisualizationBlock":
        st.subheader(block.get("title", "Chart"))

        takeaway = block.get("takeaway")
        if takeaway:
            st.caption(takeaway)

        business_question = block.get("business_question")
        if business_question:
            st.markdown(f"**Business question:** {business_question}")

        plotly_json = block.get("plotly_json")
        image_path = block.get("image_path")
        widget_key = f"{st.session_state.run_nonce}-{block.get('render_key', block.get('id', 'plot'))}-{seq}"

        if plotly_json:
            try:
                fig = pio.from_json(plotly_json)
                st.plotly_chart(fig, use_container_width=True, key=widget_key)
            except Exception as e:
                st.warning(f"Interactive plot failed, using image fallback. Error: {e}")
                if image_path and image_path.startswith("artifacts/"):
                    st.image(f"http://localhost:8000/{image_path}", use_container_width=True)
        elif image_path and image_path.startswith("artifacts/"):
            st.image(f"http://localhost:8000/{image_path}", use_container_width=True)

        st.divider()
        return

    if block_type == "AnomalyCalloutBlock":
        st.error(block.get("content", "Anomaly detected."))
        return


st.title("📊 Autonomous Executive Dashboard")
st.markdown("Business-grade data understanding first, then evidence-based visualization and interpretation.")

with st.sidebar:
    st.title("⚙️ Data Ingestion")
    uploaded_file = st.file_uploader("Upload dataset", type=["csv", "xlsx"])
    run_btn = st.button("Generate Executive Briefing", type="primary", use_container_width=True)

st.markdown(
    """
    <style>
    @keyframes pulse {
        0% { opacity: 0.35; transform: scale(0.98); }
        50% { opacity: 1; transform: scale(1); }
        100% { opacity: 0.35; transform: scale(0.98); }
    }
    .live-status {
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        background: rgba(20, 133, 255, 0.08);
        border: 1px solid rgba(20, 133, 255, 0.2);
        animation: pulse 1.6s ease-in-out infinite;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

progress_bar = st.progress(0)
status_container = st.empty()
report_container = st.container()

if uploaded_file and run_btn:
    reset_run_state()
    progress_bar.progress(5)
    status_container.markdown('<div class="live-status">Uploading dataset and starting analysis...</div>', unsafe_allow_html=True)

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }

    try:
        with requests.post(API_URL, files=files, stream=True, timeout=300) as response:
            response.raise_for_status()

            with report_container:
                st.subheader("Executive Report")
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line or not raw_line.startswith("data: "):
                        continue

                    payload = json.loads(raw_line[6:])
                    event_type = payload.get("type")

                    if event_type == "log":
                        status_container.markdown(
                            f'<div class="live-status">{payload.get("message", "Processing...")}</div>',
                            unsafe_allow_html=True,
                        )

                    elif event_type == "partial_blocks":
                        new_blocks = add_blocks(payload.get("blocks", []))
                        for block in new_blocks:
                            render_single_block(block)
                        progress_bar.progress(min(95, 10 + len(st.session_state.report_blocks) * 5))

                    elif event_type == "complete":
                        final_blocks = add_blocks(payload.get("report_blocks", []))
                        for block in final_blocks:
                            render_single_block(block)
                        progress_bar.progress(100)
                        status_container.markdown(
                            '<div class="live-status">Analysis complete. Final insights and business summary are ready.</div>',
                            unsafe_allow_html=True,
                        )

    except Exception as e:
        status_container.error(f"Run failed: {e}")