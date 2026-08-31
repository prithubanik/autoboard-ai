# 🤖 AutoBoard AI

**Autonomous Business Intelligence Dashboard powered by LLM Agents**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-green.svg)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Upload a dataset. Get an executive dashboard. Zero manual work.

AutoBoard AI is a multi-agent system that autonomously performs end-to-end business intelligence using **LangGraph** and **Ollama**. It handles data profiling, insight discovery, visualization generation, vision-based quality validation, and executive reporting—all automated.

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/prithubanik/autoboard-ai.git
cd autoboard-ai
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install and start Ollama
# Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh
# Windows: Download from https://ollama.com/download
ollama serve

# 4. Pull required models
ollama pull gemma4:31b-cloud  # Main LLM
ollama pull llava             # Vision model for chart review

# 5. Run the autonomous analyst
python main.py
```

That's it. The system will analyze your dataset and generate charts automatically.

---

## ✨ What It Does

### Autonomous Analysis Pipeline

1. **Memory & Context** - Retrieves insights from prior analyses
2. **Data Profiling** - Auto-detects types, handles missing values, profiles features
3. **Insight Planning** - Creates a strategic 3-5 chart plan based on correlations
4. **Chart Generation Loop** (for each chart):
   - Generates Plotly code using LLM
   - Executes in sandboxed subprocess
   - **Vision model reviews the rendered chart** (approves or rejects)
   - Auto-fixes errors or retries (max 3 attempts)
5. **Executive Report** - Synthesizes findings into markdown with KPIs and takeaways
6. **Memory Persistence** - Saves learnings for future runs

### Key Features

- 🧠 **12 Specialized Agents** - Memory, planning, charting, validation, reflection
- 👁️ **Visual Critic** - Vision model (llava) reviews every chart before approval
- 💾 **Persistent Memory** - SQLite-backed context that learns from every run
- 🛡️ **Sandboxed Execution** - Secure code execution with 90s timeout
- 📊 **Production Charts** - Clean Plotly Express/Graph Objects visualizations
- 🔁 **Auto-Retry Logic** - Intelligent error correction and fallback handling

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    User Uploads Dataset                      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Memory Router → Recall → Data Cleaner → Insight Planner    │
│  (Context)      (History)  (Profile)     (Chart Plan)       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│         Chart Loop: Validator → Architect → Sandbox         │
│                      → Visual Critic → Progress             │
│                      (Vision QA, approve/reject)            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Report Writer → Memory Retain → Reflection → Dashboard     │
│  (Summary)     (Persist)    (Learn)     (Output)            │
└──────────────────────────────────────────────────────────────┘
```

### Agent Workflow (LangGraph)

The system uses a **stateful LangGraph workflow** with conditional routing:

1. **Entry Point**: Memory Router accepts request
2. **Context Loading**: Recall fetches relevant prior analyses from SQLite
3. **Data Understanding**: Senior Data Cleaner profiles the dataset
4. **Strategy**: Insight Planner creates 3-5 unique chart plan
5. **Chart Loop** (per angle):
   - Chart Validator confirms spec feasibility
   - Chart Architect generates Plotly Python code
   - Sandbox Executor runs code in isolated subprocess
   - **Visual Critic (llava)** reviews rendered PNG image
   - If REJECTED → Chart Editor fixes or retry (max 3)
   - If APPROVED → Chart Progress moves to next angle
6. **Synthesis**: Report Writer compiles executive markdown summary
7. **Learning**: Memory Retain persists outcomes, Reflection generates insights

---

## 📁 Project Structure

```
autoboard-ai/
├── main.py                    # Entry point - run this!
├── graph.py                   # LangGraph workflow definition
├── state.py                   # TypedDict state for agent communication
│
├── agents/
│   ├── data_cleaner.py        # Data profiling and cleaning
│   ├── insight_planner.py     # Strategic chart planning
│   ├── chart_validator.py     # Chart specification validator
│   ├── chart_architect.py     # Plotly code generation
│   ├── sandbox_executor.py    # Secure code execution
│   ├── chart_editor.py        # Code refinement
│   ├── chart_progress.py      # Iteration tracker
│   ├── chart_skip.py          # Failure handling
│   ├── visual_critic.py       # Vision-based quality reviewer ⭐
│   ├── report_writer.py       # Executive summary generator
│   │
│   └── memory/
│       ├── memory_router.py   # Memory context selector
│       ├── memory_recall.py   # Historical retriever
│       ├── memory_store.py    # Persistence layer
│       ├── memory_retain.py   # Post-run memory writer
│       └── vector_db_client.py # Vector DB client (optional)
│
├── reflection_node.py         # Learning and synthesis
├── requirements.txt           # Python dependencies
└── setup_guide.md            # Detailed setup instructions
```

---

## 🛠️ Installation

### Prerequisites

- **Python 3.10+**
- **Ollama** (local LLM inference)
- **System**: 8GB+ RAM recommended for vision models

### Step-by-Step

```bash
# 1. Clone repository
git clone https://github.com/prithubanik/autoboard-ai.git
cd autoboard-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Ollama
# Linux/macOS:
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download

# 5. Start Ollama server
ollama serve

# 6. Pull required models (in a new terminal)
ollama pull gemma4:31b-cloud  # Main LLM for all agents
ollama pull llava             # Vision model for Visual Critic

# 7. Create required directories
mkdir -p data artifacts/charts artifacts/scratchpad database
```

### Verify Installation

```bash
# Test Plotly + Kaleido (chart rendering)
python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.write_image('test.png'); print('✅ Plotly working')"

# Test Ollama connection
python -c "from langchain_ollama import ChatOllama; llm = ChatOllama(model='gemma4:31b-cloud'); print('✅ Ollama connected')"
```

---

## 🚀 Usage

### Basic Usage

```python
# main.py
from main import run_autonomous_analyst

blocks = run_autonomous_analyst(
    csv_file_path="data/your_dataset.csv",
    thread_id="session_001"
)

for block in blocks:
    print(block)
```

### With Custom Dataset

```bash
# Place your CSV file in data/ folder
python -c "from main import run_autonomous_analyst; run_autonomous_analyst('data/sales_data.csv')"
```

### Example Output

The system returns structured UI blocks:

```json
{
  "type": "VisualizationBlock",
  "title": "Analysis Angle #1",
  "business_question": "What is the relationship between Age and Credit Limit?",
  "takeaway": "Positive correlation: older customers have higher credit limits.",
  "image_path": "artifacts/charts/chart_0.png"
}
```

### Output Block Types

| Type | Description |
|------|-------------|
| `VisualizationBlock` | Interactive Plotly charts with AI takeaways |
| `MetricGridBlock` | KPI cards with values and deltas |
| `DataFrameBlock` | Data previews and schema tables |
| `AnomalyCalloutBlock` | High-severity outlier alerts |
| `MarkdownBlock` | Executive summary sections |

---

## 🧠 Agents

| Agent | Model | Responsibility |
|-------|-------|----------------|
| Memory Router | gemma4:31b-cloud | Selects relevant memory context |
| Recall | SQLite + embeddings | Retrieves prior analyses |
| Data Cleaner | Rule-based + pandas | Profiles and cleans data |
| **Insight Planner** | gemma4:31b-cloud | Creates 3-5 chart strategy |
| Chart Validator | gemma4:31b-cloud | Validates chart specs |
| Chart Architect | gemma4:31b-cloud | Generates Plotly code |
| Sandbox Executor | Local subprocess | Executes code securely |
| **Visual Critic** ⭐ | llava (vision) | Reviews chart quality |
| Chart Editor | gemma4:31b-cloud | Refines failed code |
| Report Writer | gemma4:31b-cloud | Synthesizes findings |
| Memory Retain | SQLite | Persists run outcomes |
| Reflection | gemma4:31b-cloud | Generates reusable insights |

---

## 🔐 Security & Reliability

- **Process Group Isolation** - Each chart executes in separate subprocess
- **Hard 90s Timeout** - Prevents hangs (especially Kaleido/Chromium)
- **Auto Dependency Install** - Missing Python packages installed automatically
- **No Network Access** - Sandboxed code cannot make external requests
- **State Optimization** - Large artifacts stored on disk, not in memory
- **Custom Checkpointer** - Logs slow checkpoint writes for debugging

---

## 🧪 Testing

```bash
# Run with sample data
python -c "from main import run_autonomous_analyst; run_autonomous_analyst('data/sample.csv')"

# Test specific agent
python -m pytest tests/test_chart_architect.py -v

# Validate workflow
python -c "from graph import build_analyst_graph; app = build_analyst_graph(); print(app)"
```

---

## 🐛 Troubleshooting

### Charts not rendering

```bash
# Ensure Kaleido is installed
pip install kaleido

# Test rendering
python -c "import plotly.graph_objects as go; fig = go.Figure(); fig.write_image('test.png')"
```

### Vision model errors

```bash
# Verify llava is working
ollama run llava "describe this image" <<< "test.png"

# Check model supports vision
ollama show llava | grep -i vision
```

### Timeout during execution

- Increase `timeout_seconds` in `sandbox_executor.py` (default 90s)
- Reduce chart complexity or dataset size
- Ensure 8GB+ RAM available

### Memory issues

```bash
# Clear old memory
rm database/agent_memory.sqlite

# Reduce target plots in main.py
"target_plots_count": 6  # Instead of 10
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Additional chart types (treemap, sunburst, funnel)
- [ ] Vector database integration for semantic search
- [ ] Multi-dataset comparison mode
- [ ] Export to PowerPoint/PDF
- [ ] User feedback loop for continuous learning

### How to Contribute

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **LangGraph** - Agent workflow framework
- **Plotly** - Interactive visualization
- **Ollama** - Local LLM inference
- **DuckDB** - Fast analytical database

---

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/prithubanik/autoboard-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/prithubanik/autoboard-ai/discussions)

---

**Built with ❤️ by [@prithubanik](https://github.com/prithubanik)**

*Autonomous business intelligence for everyone.*
