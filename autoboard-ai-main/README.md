# 🤖 AutoBoard AI

### Autonomous Multimodal Business Intelligence with LLM Agents, LangGraph & Vision-Based Chart QA

<p align="center">
  <strong>Upload a dataset → discover insights → generate charts → visually validate them → produce an executive report.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LangGraph-Agentic%20Workflow-FF6B35" alt="LangGraph">
  <img src="https://img.shields.io/badge/Ollama-LLM%20Inference-000000?logo=ollama&logoColor=white" alt="Ollama">
  <img src="https://img.shields.io/badge/Plotly-Visualization-3F4F75?logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 📌 Overview

**AutoBoard AI** is an agentic business-intelligence system that turns structured datasets such as CSV files into an automatically generated analytical report.

Instead of asking an LLM a single question and returning a text response, AutoBoard AI uses a **stateful LangGraph workflow** in which specialized components collaborate to:

- understand and profile the dataset,
- retrieve relevant context from previous analyses,
- identify meaningful analytical questions,
- plan a set of complementary visualizations,
- generate executable Plotly code,
- execute and render charts,
- inspect rendered charts with a multimodal/vision model,
- revise or retry weak visualizations,
- synthesize findings into an executive report, and
- retain useful information for future analyses.

The goal is to move from **"LLM generates a chart"** toward **"LLM plans, generates, evaluates, corrects, and learns from the analytical workflow."**

---

## ✨ Why AutoBoard AI?

Traditional BI workflows often require a user to manually:

1. inspect a dataset,
2. decide which questions are worth investigating,
3. select chart types,
4. write or configure visualizations,
5. inspect charts for errors,
6. correct poor visualizations, and
7. summarize the findings.

AutoBoard AI attempts to automate this process through a coordinated agentic workflow.

### Core idea

```text
                    ┌──────────────────────┐
                    │      Dataset         │
                    │     CSV / XLSX       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Memory & Context   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Data Profiling    │
                    │   + Cleaning/Schema  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Insight Planning   │
                    │ Questions + Charts   │
                    └──────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │      Visualization Loop   │
                  │                            │
                  │ Validate → Generate → Run │
                  │      ↓                     │
                  │ Visual QA → Fix / Retry   │
                  └─────────────┬──────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Executive Report   │
                    │ KPIs + Findings +    │
                    │ Charts + Takeaways   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Memory / Reflection│
                    └──────────────────────┘
```

---

# 🧠 Agentic Workflow

AutoBoard AI is implemented as a **stateful LangGraph workflow** with conditional routing and iterative chart generation.

### 1. Memory Router
Determines what contextual information is relevant to the current analysis.

### 2. Memory Recall
Retrieves useful information from previous runs, including analytical context and chart-related patterns.

### 3. Data Cleaner / Profiler
Builds an understanding of the dataset:

- column types,
- numerical and categorical features,
- missing values,
- dataset statistics,
- correlations,
- schema information,
- data previews, and
- cleaning diagnostics.

### 4. Insight Planner
Uses the dataset profile to develop a strategic set of analytical questions and visualization ideas rather than generating arbitrary charts.

### 5. Chart Validator
Checks whether a proposed visualization is feasible and consistent with the available data.

### 6. Chart Architect
Generates Plotly-based visualization code according to the selected analytical objective.

### 7. Sandbox Executor
Runs generated chart code with execution controls and timeout handling.

### 8. Visual Critic
The rendered chart is inspected by a multimodal/vision-capable model.

The critic can evaluate aspects such as:

- readability,
- labels,
- visual clarity,
- chart suitability,
- overlapping elements,
- empty or broken plots,
- misleading presentation, and
- whether the visualization answers the intended question.

### 9. Chart Editor / Retry Loop
Rejected or failed charts can be revised and regenerated instead of immediately being returned to the user.

### 10. Chart Progress / Skip
Controls progression through the planned analytical angles and handles cases where a chart cannot be generated successfully.

### 11. Report Writer
Combines the generated findings and visualizations into an executive-style analytical report.

### 12. Memory Retention
Persists useful information from completed analyses for later retrieval.

### 13. Reflection
Generates higher-level observations from the completed workflow that can improve future runs.

---

# 🔄 Visualization Quality-Control Loop

One of the main ideas behind AutoBoard AI is that **chart generation and chart evaluation are separate steps**.

```text
                 Chart Plan
                    │
                    ▼
             ┌──────────────┐
             │   Validator  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │   Architect  │
             │ Generate Code│
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │   Executor   │
             │ Render Chart │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ Visual Critic│
             │  Vision QA   │
             └──────┬───────┘
                    │
             ┌──────┴───────┐
             │              │
          APPROVE         REJECT
             │              │
             ▼              ▼
        Next Chart     Chart Editor
                            │
                            ▼
                         Retry
```

This creates a **generate → execute → inspect → correct** loop instead of assuming that the first LLM-generated visualization is correct.

---

# 🏗️ System Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                         Streamlit UI                          │
│                Dataset Upload + Live Results                  │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                          FastAPI                               │
│                    Streaming Analysis API                     │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────┐
│                         LangGraph                             │
│                 Stateful Agent Orchestration                  │
├───────────────────────────────────────────────────────────────┤
│ Memory → Profiling → Planning → Validation → Charting → QA   │
│                                                   ↓           │
│                                          Retry / Correction   │
│                                                   ↓           │
│                                  Reporting → Reflection      │
└───────────────┬───────────────────────┬───────────────────────┘
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌─────────────────┐
        │    Ollama    │        │ Memory / Vector │
        │ LLM + Vision │        │    Backends     │
        └──────────────┘        └─────────────────┘
                │
                ▼
        ┌─────────────────┐
        │ Plotly / Python │
        │ Chart Rendering │
        └─────────────────┘
```

---

# 🛠️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Agent orchestration | **LangGraph** | Stateful workflow and conditional routing |
| LLM inference | **Ollama** | Local/self-hosted model interface |
| Language model | **Gemma 4** *(configurable)* | Planning, reasoning, code generation and reporting |
| Vision model | **Vision-capable model** *(configurable)* | Rendered chart quality assessment |
| Data processing | **Pandas / NumPy** | Profiling and analytical preparation |
| Analytical SQL | **DuckDB** | Fast local analytical queries |
| Visualization | **Plotly** | Interactive charts and rendering |
| API | **FastAPI** | Streaming backend |
| Frontend | **Streamlit** | Interactive dashboard |
| Persistent memory | **SQLite** | Run and memory persistence |
| Optional vector memory | **ChromaDB** | Semantic retrieval experiments |
| Code execution | **Controlled subprocess / sandbox backend** | Generated chart execution |

> Model names and execution backends are intentionally configurable. The repository may evolve as the model and sandbox configuration is refined.

---

# 📂 Project Structure

The repository is being organized toward the following structure:

```text
autoboard-ai/
│
├── agents/
│   ├── __init__.py
│   │
│   ├── data_cleaner.py
│   ├── insight_planner.py
│   ├── chart_validator.py
│   ├── chart_architect.py
│   ├── sandbox_executor.py
│   ├── chart_editor.py
│   ├── chart_progress.py
│   ├── chart_skip.py
│   ├── visual_critic.py
│   ├── report_writer.py
│   ├── reflection_node.py
│   │
│   └── memory/
│       ├── __init__.py
│       ├── memory_router.py
│       ├── memory_recall.py
│       ├── memory_store.py
│       ├── memory_retain.py
│       └── vector_db_client.py
│
├── api.py
├── app.py
├── graph.py
├── main.py
├── state.py
│
├── data/
│   └── sample.csv
│
├── artifacts/
│   ├── charts/
│   └── scratchpad/
│
├── database/
│
├── tests/
│   ├── test_data_cleaner.py
│   ├── test_chart_validator.py
│   ├── test_memory_store.py
│   └── test_workflow.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

> **Note:** The current prototype may temporarily contain modules at the repository root. The structure above is the intended cleaned-up GitHub layout.

---

# 🚀 Getting Started

## Prerequisites

Before running AutoBoard AI, install:

- Python **3.10+**
- Ollama
- Git
- A model supported by your configured Ollama setup
- Sufficient CPU/GPU/RAM for the selected model

For larger multimodal models, more system resources may be required.

---

## 1. Clone the repository

```bash
git clone https://github.com/prithubanik/autoboard-ai.git
cd autoboard-ai
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> `requirements.txt` will be maintained alongside the repository so that the project can be reproduced from a clean environment.

---

## 4. Configure Ollama

Install Ollama and make sure its service is available.

```bash
ollama serve
```

Then pull the model configured by the project.

Example:

```bash
ollama pull gemma4:31b-cloud
```

If a different model is configured, replace the model name accordingly.

---

## 5. Prepare directories

```text
data/
artifacts/charts/
artifacts/scratchpad/
database/
```

A small synthetic/sample dataset should be included under `data/` for reproducible testing.

---

# ▶️ Running the Application

AutoBoard AI supports a programmatic workflow as well as a web interface.

## Option A — Streamlit + FastAPI

Start the API:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

In another terminal, start the frontend:

```bash
streamlit run app.py
```

Then open the Streamlit URL shown in the terminal.

The frontend communicates with the FastAPI streaming endpoint:

```text
POST /api/v1/analyze/stream
```

---

## Option B — Python API

The workflow can also be called programmatically:

```python
from main import run_autonomous_analyst

blocks = run_autonomous_analyst(
    csv_file_path="data/sample.csv",
    thread_id="session_001",
)

for block in blocks:
    print(block)
```

This is useful for experiments, notebooks, automated pipelines, and future integration with other applications.

---

# 📊 Output

The system produces structured analytical blocks that can be rendered by the UI.

Typical output categories include:

| Block | Purpose |
|---|---|
| `VisualizationBlock` | Chart + analytical takeaway |
| `MetricGridBlock` | KPIs and key metrics |
| `DataFrameBlock` | Dataset previews / tables |
| `AnomalyCalloutBlock` | Important anomalies or warnings |
| `MarkdownBlock` | Executive report sections |

Example:

```json
{
  "type": "VisualizationBlock",
  "title": "Analysis Angle #1",
  "business_question": "What is the relationship between Age and Credit Limit?",
  "takeaway": "The analysis identifies a positive relationship between the selected variables.",
  "image_path": "artifacts/charts/chart_0.png"
}
```

---

# 🧠 Memory System

AutoBoard AI is designed with persistent analytical memory.

The memory layer can retain information such as:

- previous analysis summaries,
- useful chart patterns,
- business definitions,
- analytical context,
- run-level metadata, and
- reflection results.

The current implementation uses **SQLite-backed persistence**, with an optional vector database client available for semantic retrieval experiments.

This allows the project to evolve from:

```text
Stateless analysis
```

toward:

```text
Analysis
   ↓
Memory
   ↓
Future analysis
   ↓
Better context
```

---

# 🔐 Reliability & Safety

Generated visualization code is executed through a controlled execution path with safeguards such as:

- execution timeouts,
- subprocess isolation,
- error capture,
- retry handling,
- chart validation,
- visual quality checks, and
- separation of large artifacts from the LangGraph state.

### Important security note

AutoBoard AI is an experimental research/engineering project.

**Generated Python code should not be treated as inherently safe.** The local execution path is not equivalent to a hardened security sandbox. For untrusted users or production deployment, an appropriately isolated execution environment should be used.

---

# 🔁 Failure Recovery

The workflow is designed to avoid failing on the first chart-generation error.

A typical recovery path is:

```text
Generate
   ↓
Execute
   ├── Success → Visual Critic
   │                  ├── Approve → Continue
   │                  └── Reject → Edit → Retry
   │
   └── Failure → Edit / Retry
                    ↓
                  Retry
                    ↓
              Skip if necessary
```

This makes the system more resilient to:

- invalid Plotly code,
- incompatible columns,
- unsupported chart specifications,
- rendering failures,
- empty visualizations, and
- visual quality problems.

---

# 🧪 Testing

Tests are being added as the repository is cleaned up.

The intended test structure is:

```bash
pytest -v
```

Individual components can also be tested separately:

```bash
pytest tests/test_data_cleaner.py -v
pytest tests/test_chart_validator.py -v
pytest tests/test_memory_store.py -v
```

Before considering a release stable, the project should verify:

- dataset ingestion,
- profiling,
- state transitions,
- chart generation,
- chart validation,
- retry routing,
- memory persistence, and
- end-to-end workflow execution.

---

# 📈 Example Use Cases

AutoBoard AI can be adapted to datasets such as:

- sales and revenue data,
- customer analytics,
- marketing campaigns,
- financial datasets,
- operational KPIs,
- product analytics,
- experiment results,
- manufacturing measurements, and
- other structured tabular datasets.

The workflow is intentionally domain-agnostic; the analytical prompts, business rules, and chart strategy can be extended for specific domains.

---

# 🔬 Research / Engineering Focus

AutoBoard AI explores several important ideas in modern AI systems:

### Agentic AI

Multiple specialized components collaborate through a stateful workflow instead of relying on a single LLM call.

### Multimodal Evaluation

Charts are evaluated as **rendered visual artifacts**, not only as Python code or metadata.

### Self-Correction

Failed or visually weak outputs can be revised through an iterative feedback loop.

### Persistent Memory

Previous analytical runs can provide context for future analyses.

### Tool-Augmented Reasoning

The system combines LLM reasoning with:

- Python execution,
- Pandas,
- DuckDB,
- Plotly,
- SQLite,
- vector retrieval, and
- visualization rendering.

---

# 🗺️ Roadmap

- [x] Stateful LangGraph workflow
- [x] Automated dataset profiling
- [x] Insight / chart planning
- [x] LLM-generated Plotly visualizations
- [x] Chart execution and rendering
- [x] Vision-based chart review
- [x] Retry and correction loop
- [x] Executive report generation
- [x] Persistent run memory
- [x] Streamlit frontend
- [x] FastAPI streaming backend
- [ ] Clean modular package structure
- [ ] Reproducible `requirements.txt`
- [ ] Automated unit/integration test suite
- [ ] Improved vector-memory integration
- [ ] Multi-dataset comparison
- [ ] Export reports to PDF / PowerPoint
- [ ] Authentication and multi-user support
- [ ] Production-grade isolated code execution
- [ ] Evaluation benchmark for chart quality
- [ ] Human feedback loop
- [ ] Docker / Compose deployment
- [ ] CI/CD with GitHub Actions

---

# 🤝 Contributing

Contributions, ideas, and experiments are welcome.

A typical contribution workflow:

```bash
git checkout -b feature/your-feature
git add .
git commit -m "Add your feature"
git push origin feature/your-feature
```

Then open a Pull Request.

### Good areas for contribution

- New analytical agents
- Additional chart types
- Better chart-quality evaluation
- Domain-specific business rules
- Vector-memory improvements
- Evaluation datasets
- Safer execution environments
- UI improvements
- Testing and observability

---

# 📜 License

This project is released under the **MIT License**.

See [`LICENSE`](LICENSE) for details.

---

# 🙏 Acknowledgements

AutoBoard AI builds on the work of several open-source technologies:

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent/workflow orchestration
- [Ollama](https://ollama.com/) — model serving
- [Plotly](https://plotly.com/) — visualization
- [Pandas](https://pandas.pydata.org/) — data analysis
- [DuckDB](https://duckdb.org/) — analytical SQL
- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [Streamlit](https://streamlit.io/) — application UI
- [ChromaDB](https://www.trychroma.com/) — vector storage experiments

---

# 📬 Contact

**Prithu Banik**

GitHub: [@prithubanik](https://github.com/prithubanik)

For bugs, feature requests, or technical discussions, please use the repository's GitHub Issues.

---

<p align="center">
  <strong>AutoBoard AI</strong><br>
  From raw data to validated insights — autonomously.
</p>
