# 🤖 AutoBoard AI

**Autonomous Business Intelligence Dashboard powered by LLM Agents**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Upload a dataset. Get an executive dashboard. Zero manual work.

AutoBoard AI is a multi-agent system that autonomously performs end-to-end business intelligence: data profiling, insight discovery, visualization generation, quality validation, and executive reporting—all driven by LLM agents with vision-based quality control.

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/autoboard-ai.git
cd autoboard-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Ollama (required for LLM agents)
ollama pull gemma4:31b-cloud
ollama pull llava

# Run the web interface
python api.py              # Terminal 1: Backend API
streamlit run app.py       # Terminal 2: Frontend UI
```

Then open `http://localhost:8501` and upload your CSV/Excel file.

---

## ✨ Features

### 🧠 Intelligent Multi-Agent Pipeline

- **Memory Router & Recall** - Retrieves context from prior analyses and business definitions
- **Senior Data Cleaner** - Auto-profiles datasets, detects types, handles missing values
- **Insight Planner** - Creates strategic 3-5 chart storytelling plans based on correlations
- **Chart Architect** - Generates clean Plotly Express/Graph Objects code
- **Sandbox Executor** - Secure code execution with 90s timeout and auto-dependency install
- **Visual Critic** - Vision model reviews rendered charts, approves or rejects with feedback
- **Chart Editor** - Refines code based on execution errors or visual feedback
- **Report Writer** - Synthesizes findings into executive markdown summaries
- **Memory Retain & Reflection** - Persists outcomes and generates reusable insights

### 📊 Production-Ready Outputs

- **MetricGridBlock** - KPI cards with values and deltas
- **VisualizationBlock** - Interactive Plotly charts with business questions and AI-generated takeaways
- **DataFrameBlock** - Schema previews and data tables
- **AnomalyCalloutBlock** - High-severity outlier and anomaly alerts
- **MarkdownBlock** - Executive summary sections

### 🛡️ Enterprise-Grade Reliability

- **Sandboxed Execution** - Process group isolation with hard timeouts
- **Visual Quality Gate** - No chart reaches the dashboard without vision model approval
- **Persistent Memory** - SQLite-backed context that learns from every run
- **Real-Time Streaming** - Server-sent events (SSE) for live progress updates
- **Automatic Retry Logic** - Up to 3 attempts per chart with intelligent error correction

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Uploads Dataset                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Memory Router → Recall → Data Cleaner → Insight Planner       │
│  (Context)      (History)  (Profile)     (Chart Plan)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           Chart Generation Loop (per angle, 3-5 charts)         │
│  Validator → Architect → Sandbox → Visual Critic → Progress    │
│  (Spec)      (Code)      (Execute)  (Vision QA)   (Next)       │
│                              ↑                                  │
│                              └────── Retry (max 3) ────────────┤
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Report Writer → Memory Retain → Reflection → Final Dashboard  │
│  (Summary)     (Persist)    (Learn)     (UI Blocks)            │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Workflow (LangGraph)

The system uses a stateful LangGraph workflow with conditional routing:

1. **Entry**: Memory Router accepts request
2. **Context Loading**: Recall fetches relevant prior analyses
3. **Data Understanding**: Senior Data Cleaner profiles the dataset
4. **Strategy**: Insight Planner creates chart plan (3-5 unique chart types)
5. **Loop** (for each chart):
   - Chart Validator confirms spec feasibility
   - Chart Architect generates Plotly code
   - Sandbox Executor runs code in isolated subprocess
   - Visual Critic (vision model) reviews rendered PNG
   - If REJECTED → Chart Editor fixes or retry (max 3)
   - If APPROVED → Chart Progress moves to next angle
6. **Synthesis**: Report Writer compiles executive summary
7. **Learning**: Memory Retain persists outcomes, Reflection generates insights

---

## 📁 Project Structure

```
autoboard-ai/
├── api.py                    # FastAPI backend with SSE streaming
├── app.py                    # Streamlit frontend interface
├── main.py                   # Standalone execution entry point
├── graph.py                  # LangGraph workflow definition
├── state.py                  # TypedDict state schema for agent communication
│
├── agents/
│   ├── data_cleaner.py       # Data profiling and cleaning agent
│   ├── insight_planner.py    # Strategic chart planning agent
│   ├── chart_validator.py    # Chart specification validator
│   ├── chart_architect.py    # Plotly code generation agent
│   ├── sandbox_executor.py   # Secure code execution with timeout
│   ├── chart_editor.py       # Code refinement agent
│   ├── chart_progress.py     # Chart iteration tracker
│   ├── chart_skip.py         # Failure handling agent
│   ├── visual_critic.py      # Vision-based chart quality reviewer
│   ├── report_writer.py      # Executive summary generator
│   │
│   └── memory/
│       ├── memory_router.py  # Memory context selector
│       ├── memory_recall.py  # Historical analysis retriever
│       ├── memory_store.py   # Memory persistence layer
│       ├── memory_retain.py  # Post-run memory writer
│       └── memory_db_client.py # Vector database client (optional)
│
├── reflection_node.py        # Learning and synthesis agent
├── requirements.txt          # Python dependencies
├── setup_guide.md            # Detailed setup instructions
└── examples/
    └── example_usage.py      # Programmatic usage example
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10+**
- **Ollama** with vision-capable models
- **System packages**: `graphviz` (optional, for workflow visualization)

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/autoboard-ai.git
cd autoboard-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install and start Ollama
# Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh
# Windows: Download from https://ollama.com/download
ollama serve

# 5. Pull required models
ollama pull gemma4:31b-cloud  # Main LLM for all agents
ollama pull llava             # Vision model for Visual Critic

# 6. Create required directories
mkdir -p data artifacts/charts artifacts/scratchpad database output
```

### Verify Installation

```bash
# Test Plotly + Kaleido
python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.write_image('test.png'); print('✅ Plotly + Kaleido working')"

# Test Ollama connection
python -c "from langchain_ollama import ChatOllama; llm = ChatOllama(model='gemma4:31b-cloud'); print('✅ Ollama connection successful')"
```

---

## 🚀 Usage

### Option 1: Web Interface (Recommended)

```bash
# Terminal 1: Start API server
python api.py

# Terminal 2: Start Streamlit frontend
streamlit run app.py
```

Navigate to `http://localhost:8501`, upload your CSV/Excel file, and click "Generate Executive Briefing".

### Option 2: Standalone Execution

```python
from main import run_autonomous_analyst

blocks = run_autonomous_analyst("data/your_dataset.csv", thread_id="session_001")
for block in blocks:
    print(block)
```

### Option 3: Direct API Call

```bash
curl -X POST http://localhost:8000/api/v1/analyze/stream \
  -F "file=@data/your_dataset.csv" \
  --output response.json
```

---

## 📊 Example Output

The system generates structured UI blocks:

```json
{
  "id": "session_001-block-viz-0",
  "type": "VisualizationBlock",
  "title": "Analysis Angle #1",
  "business_question": "What is the relationship between Age and Credit Limit?",
  "takeaway": "Positive correlation observed: older customers tend to have higher credit limits.",
  "plotly_json": "{...}",
  "image_path": "artifacts/charts/chart_0.png"
}
```

### Output Block Types

| Block Type | Description | Use Case |
|------------|-------------|----------|
| `MetricGridBlock` | KPI cards with labels, values, deltas | Executive summary metrics |
| `VisualizationBlock` | Interactive Plotly charts with takeaways | Core data visualizations |
| `DataFrameBlock` | Preview tables with schema info | Data exploration |
| `AnomalyCalloutBlock` | High-severity alerts | Outlier detection |
| `MarkdownBlock` | Rich text sections | Narrative insights |

---

## 🧠 Agent Specifications

| Agent | Model | Responsibility |
|-------|-------|----------------|
| Memory Router | gemma4:31b-cloud | Selects relevant memory context |
| Recall | SQLite + embeddings | Retrieves prior analyses |
| Data Cleaner | Rule-based + pandas | Profiles and cleans data |
| Insight Planner | gemma4:31b-cloud | Creates chart strategy |
| Chart Validator | gemma4:31b-cloud | Validates chart specs |
| Chart Architect | gemma4:31b-cloud | Generates Plotly code |
| Sandbox Executor | Local subprocess | Executes code securely |
| Visual Critic | llava (vision) | Reviews chart quality |
| Chart Editor | gemma4:31b-cloud | Refines failed code |
| Report Writer | gemma4:31b-cloud | Synthesizes findings |
| Memory Retain | SQLite | Persists run outcomes |
| Reflection | gemma4:31b-cloud | Generates reusable insights |

---

## 🔐 Security & Sandboxing

- **Process Group Isolation** - Each chart executes in a separate process group
- **Hard Timeout** - 90-second limit prevents hangs (especially Kaleido/Chromium)
- **Automatic Dependency Installation** - Missing modules are auto-installed via pip
- **No Network Access** - Sandboxed code cannot make external requests
- **Path Restrictions** - Artifacts limited to `artifacts/` directory
- **State Bloat Prevention** - Large artifacts (base64, JSON) excluded from LangGraph state; only file paths persisted

---

## 🧪 Testing

```bash
# Run with sample data
python examples/example_usage.py

# Test specific agent
python -m pytest tests/test_chart_architect.py -v

# Validate workflow graph
python -c "from graph import build_analyst_graph; app = build_analyst_graph(); print(app)"
```

---

## 🐛 Troubleshooting

### Charts not rendering

```bash
# Ensure Kaleido is installed
pip install kaleido

# Test Plotly rendering
python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.write_image('test.png')"
```

### Vision model errors

```bash
# Verify Ollama vision model
ollama run llava "describe this image" <<< "test.png"

# Check model supports vision
ollama show llava | grep -i "vision\|multimodal"
```

### Timeout issues

- Increase `timeout_seconds` in `SandboxExecutorNode` (default 90s)
- Reduce chart complexity or dataset size
- Ensure sufficient system RAM (Chromium can be memory-intensive)

### Memory/State bloat

- Clear old memory: `rm database/agent_memory.sqlite`
- Reduce target plots in `main.py`: `"target_plots_count": 6`

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Add support for additional chart types (treemap, sunburst, funnel)
- [ ] Integrate vector database for semantic memory search
- [ ] Multi-dataset comparison mode
- [ ] Chart export to PowerPoint/PDF
- [ ] User feedback loop for continuous learning

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📈 Performance Considerations

- **Custom Checkpointer** - `TimedMemorySaver` logs slow checkpoint writes for debugging state bloat
- **Kaleido Warm-up** - Pre-launches Chromium to avoid cold-start delays on first chart
- **Recursion Limit** - Configurable limit (default 100) for deep agent loops
- **Artifact Streaming** - Large files written to disk, not stored in state

---

## 📄 License

This project is licensed under the MIT License—see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangGraph** - Agent workflow framework
- **Plotly** - Interactive visualization library
- **Ollama** - Local LLM inference
- **FastAPI** - High-performance API
- **Streamlit** - Data app frontend

---

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/autoboard-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/autoboard-ai/discussions)

---

**Built with ❤️ for autonomous business intelligence**

*Made by a AI Engineer who believes AI agents should do the heavy lifting.*
