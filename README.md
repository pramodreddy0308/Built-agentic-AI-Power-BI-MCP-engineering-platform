# 🚀 Agentic AI Power BI Engineering Platform

An autonomous AI-powered engineering system for modifying, validating, and orchestrating Power BI PBIP reports using MCP (Model Context Protocol), OpenAI, Python, and Git-based workflows.

---

# 📌 Project Overview

This project demonstrates a TRUE Agentic AI architecture for Power BI engineering.

Instead of manually editing reports inside Power BI Desktop, users can provide natural language prompts such as:

* “Replace line chart with area chart”
* “Add Gross Margin KPI card”
* “Apply executive dark theme”
* “Rearrange visuals into a clean grid layout”

The AI system:

1. Understands the request
2. Generates an execution plan
3. Routes tasks through MCP tools
4. Modifies PBIP report metadata
5. Validates report integrity
6. Tracks changes with Git
7. Reopens Power BI Desktop automatically

---

# 🧠 Core Architecture

```text
User Prompt
    ↓
AI Planning Engine (GPT-4o)
    ↓
Workflow Generator
    ↓
MCP Tool Router
    ↓
PBIP Modification Engine
    ↓
Validation Layer
    ↓
Git Versioning
    ↓
Power BI Desktop Launcher
```

---

# ⚡ Key Features

## ✅ Agentic AI Workflow Engine

* Natural language Power BI modifications
* Multi-step autonomous execution
* AI-generated execution plans
* Retry handling and workflow orchestration

## ✅ MCP (Model Context Protocol) Architecture

* Modular Power BI tooling system
* Dynamic tool routing
* Extensible engineering framework
* Structured tool contracts

## ✅ Power BI PBIP Engineering

* PBIP report parsing
* Semantic model discovery
* Visual metadata inspection
* Layout automation
* Visual transformations
* DAX measure support

## ✅ Visual Automation

* Replace chart types automatically
* Add KPI cards
* Rearrange layouts
* Update titles and labels
* Theme modifications

## ✅ Git-Based Version Control

* Automatic commits
* Change tracking
* Rollback support
* Portfolio-grade engineering workflow

## ✅ Power BI Launcher Integration

* Opens PBIP directly in Power BI Desktop
* Supports automatic refresh workflow
* Desktop restart support

---

# 🏗️ Tech Stack

| Technology     | Purpose                   |
| -------------- | ------------------------- |
| Python         | Core engineering platform |
| OpenAI GPT-4o  | AI planning + reasoning   |
| MCP            | Tool orchestration        |
| Power BI PBIP  | Report engineering format |
| FastMCP        | MCP server framework      |
| Git            | Version control           |
| VS Code        | Development environment   |
| GitHub Copilot | AI-assisted development   |

---

# 📂 Project Structure

```text
powerbi-mcp-agent/
│
├── agent/                         # AI orchestration layer
│   ├── powerbi_agent.py
│   ├── planner_agent.py
│   ├── workflow_engine.py
│   ├── tool_router.py
│   └── prompts.py
│
├── server/                        # MCP tools + infrastructure
│   ├── config.py
│   ├── server.py
│   ├── pbip_parser.py
│   ├── metadata_tools.py
│   ├── visual_tools.py
│   ├── dax_tools.py
│   ├── validator.py
│   ├── git_tools.py
│   └── powerbi_launcher.py
│
├── Sales_report_PBIP.Report/
├── Sales_report_PBIP.SemanticModel/
├── Sales_report_PBIP.pbip
│
├── quickstart.py
├── requirements.txt
├── .env.example
└── README.md
```

---

# 🚀 Example AI Requests

## Replace Visual Type

```text
Replace line chart with area chart
```

## Add KPI Card

```text
Add Total Revenue KPI to Executive Dashboard
```

## Reorganize Layout

```text
Arrange all visuals in a 2-column executive layout
```

## Apply Theme

```text
Apply dark executive theme with blue accents
```

---

# ⚙️ Setup

## 1. Clone Repository

```bash
git clone https://github.com/your-username/powerbi-mcp-agent.git
cd powerbi-mcp-agent
```

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

## 3. Activate Environment

### Windows

```powershell
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Configure Environment

Create `.env` file:

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
```

---

# ▶️ Run the System

```bash
python quickstart.py
```

You can then:

1. Start Interactive Agent Mode
2. Start MCP Server
3. Run Test Requests

---

# 🔄 Example Workflow

## User Request

```text
Replace all pie charts with bar charts
```

## AI Workflow

* Discover report pages
* Scan visuals
* Detect pie charts
* Generate replacement plan
* Modify PBIP visual JSON
* Validate report structure
* Commit changes to Git
* Launch updated report in Power BI Desktop

---

# 🧪 Validation System

The platform validates:

* Report structure
* Visual metadata
* DAX measures
* Page integrity
* Semantic model consistency
* Visual bindings

---

# 🔐 Security

* `.env` excluded from Git
* API keys protected
* Local PBIP execution
* Git rollback support
* Validation before commits

---

# 📈 Portfolio Highlights

This project demonstrates:

* AI Agent Engineering
* MCP Architecture
* Autonomous Workflow Design
* Power BI Automation
* Production-Style Python Engineering
* GitOps Workflows
* AI Planning Systems
* Metadata Engineering
* Tool-Oriented AI Systems

---

# 🎯 Future Enhancements

* Multi-agent orchestration
* Local LLM support (Ollama)
* Azure OpenAI integration
* Semantic visual recommendations
* Automated dashboard generation
* RAG-powered Power BI assistant
* Live Power BI API integration

---

# 👨‍💻 Author

Pramod Reddy

AI + Data + Power BI Engineering

---

# ⭐ Project Vision

This project explores the future of AI-powered BI engineering where dashboards evolve through natural language interaction and autonomous AI workflows.

Instead of manually editing reports, AI agents become intelligent Power BI engineers.
