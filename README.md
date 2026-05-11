# Power BI Agentic AI Engineering System

A production-grade autonomous AI system for intelligent Power BI PBIP project modifications using MCP (Model Context Protocol), OpenAI GPT-4, and Python.

## 🎯 Overview

This system implements a TRUE agentic architecture where:

1. **AI Planner** analyzes user requests and generates detailed execution plans
2. **MCP Tool Router** directs plans to appropriate PBIP modification tools
3. **Workflow Engine** executes plans with error handling and retries
4. **Validation Layer** ensures changes maintain report integrity
5. **Git Integration** tracks all modifications with automatic commits

```
User Request
    ↓
AI Planner (GPT-4)
    ↓
Workflow Plan
    ↓
MCP Tool Router
    ↓
Tool Execution
    ↓
Validation
    ↓
Git Commit
    ↓
Power BI Refresh
```

## 📦 Project Structure

```
powerbi-mcp-agent/
├── server/                          # MCP Server & Tools
│   ├── server.py                    # FastMCP server (entry point)
│   ├── models.py                    # Data models & schemas
│   ├── pbip_parser.py              # PBIP structure parser
│   ├── metadata_tools.py           # Inspection tools
│   ├── dax_tools.py                # DAX/measure tools
│   ├── visual_tools.py             # Visual modification tools
│   ├── git_tools.py                # Version control tools
│   └── validator.py                # Validation tools
│
├── agent/                           # AI Agent & Orchestration
│   ├── powerbi_agent.py            # Main agent orchestrator
│   ├── planner_agent.py            # GPT-4 planning engine
│   ├── workflow_engine.py          # Workflow execution
│   ├── tool_router.py              # MCP tool routing
│   └── prompts.py                  # System prompts
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
└── README.md                        # This file
```

## ⚙️ Installation

### Prerequisites

- Python 3.10+
- Power BI PBIP project
- OpenAI API key (GPT-4 access)
- Git (for version control)

### Setup

1. **Clone/download the project**

```bash
cd powerbi-mcp-agent
```

2. **Create Python virtual environment**

```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

5. **Initialize git repository** (if not already)

```bash
cd Sales_report_PBIP
git init
git add .
git commit -m "Initial commit"
```

## 🚀 Usage

### Starting the MCP Server

```bash
python server/server.py
```

Server starts on `http://localhost:8000`
API docs available at `http://localhost:8000/docs`

### Using the Agent in Python

```python
from pathlib import Path
from agent.powerbi_agent import PowerBIAgent

# Initialize agent
pbip_root = Path("./Sales_report_PBIP")
agent = PowerBIAgent(pbip_root)

# Process request
result = agent.process_request(
    "Add Gross Margin KPI card to Executive Dashboard",
    auto_execute=True
)

# Check result
if result["success"]:
    print("✓ Request completed!")
else:
    print(f"✗ Error: {result['error']}")
```

### Interactive Mode

```python
agent.interactive_mode()
```

Then enter your requests:
```
📊 Request: Add Total Revenue measure to FactOrders table
📊 Request: Replace pie charts with bar charts
📊 Request: Add dark theme to report
📊 Request: exit
```

### Command Line

```bash
# Run agent with a specific request
python -m agent.powerbi_agent --request "Add Gross Margin KPI"

# Interactive mode
python -m agent.powerbi_agent --interactive

# Validate report
python -m agent.powerbi_agent --validate
```

## 🛠️ MCP Tools Reference

### Metadata Tools (Inspection)

**list_pages()** - List all report pages
```python
pages = mcp.list_pages()
# Returns: { "pages": [...], "count": 2 }
```

**list_visuals(page_id)** - List visuals on a page
```python
visuals = mcp.list_visuals("e9d880b5977088da6d5a")
```

**list_tables()** - List semantic model tables
```python
tables = mcp.list_tables()
```

**list_measures(table_name)** - List measures
```python
measures = mcp.list_measures("FactOrders")
```

**search_visuals(search_term)** - Find visuals by name
```python
results = mcp.search_visuals("Executive Dashboard")
```

### DAX Tools (Measures)

**create_measure()** - Create new measure
```python
result = mcp.create_measure(
    measure_name="Gross Margin",
    expression="SUMX(FactOrders, FactOrders[Quantity] * FactOrders[UnitPrice]) - SUM(FactOrders[Cost])",
    table_name="FactOrders",
    description="Gross margin calculation",
    format_string="$#,##0.00"
)
```

**update_measure()** - Update measure
```python
result = mcp.update_measure(
    measure_name="Gross Margin",
    format_string="0.00%"
)
```

**validate_dax(expression)** - Validate DAX
```python
validation = mcp.validate_dax("SUM(FactOrders[Amount])")
# Returns: { "is_valid": true, "errors": [], "warnings": [] }
```

### Visual Tools (Modifications)

**add_kpi_card()** - Add KPI visual
```python
result = mcp.add_kpi_card(
    page_id="e9d880b5977088da6d5a",
    title="Total Revenue",
    measure_name="Total Revenue",
    table_name="FactOrders",
    x=0, y=0, width=250, height=250,
    color="#0078D4"
)
```

**replace_visual()** - Change chart type
```python
result = mcp.replace_visual(
    page_id="e9d880b5977088da6d5a",
    visual_id="9b04c5f13045851cae59",
    new_visual_type="clusteredBar",
    preserve_bindings=True
)
```

**move_visual()** - Reposition visual
```python
result = mcp.move_visual(
    page_id="e9d880b5977088da6d5a",
    visual_id="9b04c5f13045851cae59",
    x=300, y=100
)
```

**auto_arrange_visuals()** - Grid layout
```python
result = mcp.auto_arrange_visuals(
    page_id="e9d880b5977088da6d5a",
    columns=2,
    padding=20
)
```

### Git Tools (Version Control)

**git_commit()** - Create commit
```python
result = mcp.git_commit(
    message="Add Gross Margin measure and KPI",
    files=None,  # None = all changes
    author="Power BI Agent",
    email="agent@powerbi.local"
)
```

**get_status()** - Git status
```python
status = mcp.get_status()
# Returns: { "branch": "main", "staged_count": 3, "changed_count": 2 }
```

**get_commit_history()** - View commits
```python
history = mcp.get_commit_history(max_commits=10)
```

### Validation Tools

**validate_report()** - Full validation
```python
result = mcp.validate_report()
# Returns: { "is_valid": true, "errors": [], "warnings": [...] }
```

**validate_measure(measure_name)** - Measure validation
```python
result = mcp.validate_measure("Gross Margin")
```

**validate_visual(page_id, visual_id)** - Visual validation
```python
result = mcp.validate_visual("e9d880b5977088da6d5a", "9b04c5f13045851cae59")
```

## 🤖 Agent Capabilities

The AI agent can autonomously:

### Inspection & Analysis
- List and analyze report pages
- Inspect visual configurations and bindings
- Scan semantic model structure
- Search for specific components
- Validate report integrity

### Measure Creation
- Create DAX measures from natural language
- Validate DAX syntax and logic
- Handle complex calculations (YTD, growth rates, etc.)
- Format measures appropriately

### Visual Modifications
- Add KPI cards with data bindings
- Replace chart types (pie → bar, column → line)
- Reorganize layout (grid, cascade)
- Update titles and labels
- Duplicate visuals

### Layout Design
- Auto-arrange visuals in grid layout
- Calculate optimal positions
- Preserve alignment and spacing
- Batch update multiple visuals

### Validation & Testing
- Validate report structure
- Check data bindings
- Verify measure expressions
- Detect conflicts and errors

### Version Control
- Create descriptive commits
- Create release tags
- Track changes over time
- Rollback modifications if needed

## 📋 Example Workflows

### Example 1: Add KPI Dashboard

```python
request = "Add Gross Margin KPI card to Executive Dashboard"

agent.process_request(request, auto_execute=True)
```

Agent will:
1. Search for "Executive Dashboard" page
2. Check if "Gross Margin" measure exists
3. Create measure if missing
4. Add KPI card with formatting
5. Validate visual and bindings
6. Commit: "Add Gross Margin KPI to Executive Dashboard"

### Example 2: Replace Chart Types

```python
request = "Replace all pie charts with clustered bar charts"

agent.process_request(request, auto_execute=True)
```

Agent will:
1. List all visuals across all pages
2. Identify pie charts
3. For each pie chart:
   - Get visual details and bindings
   - Replace with bar chart
   - Preserve data mappings
4. Validate all replacements
5. Commit: "Replace pie charts with bar charts"

### Example 3: Apply Theme

```python
request = "Apply dark executive theme with blue accents"

agent.process_request(request, auto_execute=True)
```

Agent will:
1. Get current theme settings
2. Create dark color palette
3. Update report styling
4. Apply to all visuals
5. Validate appearance
6. Commit: "Apply dark executive theme"

## 🔄 Workflow Architecture

### Planning Phase

```
User Request
    ↓
GPT-4 Planner
    ↓
Analyzes request
    ↓
Generates JSON Plan
{
  "goal": "...",
  "steps": [
    {
      "step_id": "step_1",
      "tool_name": "list_pages",
      "tool_params": {},
      "depends_on": []
    },
    ...
  ]
}
```

### Validation Phase

```
Generated Plan
    ↓
Tool Feasibility Check
    ↓
Parameter Validation
    ↓
Dependency Resolution
    ↓
Confidence Scoring
```

### Execution Phase

```
For each step:
  ├─ Check dependencies
  ├─ Prepare parameters
  ├─ Execute MCP tool
  ├─ Handle result
  ├─ Retry if needed (3 max)
  └─ Store result

On success:
  ├─ Validate report
  ├─ Git commit
  └─ Report completion
```

## ⚙️ Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# PBIP Project
PBIP_ROOT=.
PBIP_PROJECT_NAME=Sales_report_PBIP

# MCP Server
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Agent
AUTO_VALIDATE=true
AUTO_COMMIT=true
GIT_AUTHOR=Power BI Agent
GIT_EMAIL=agent@powerbi.local
```

### Logging

Edit `agent/powerbi_agent.py` to configure logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
```

## 🧪 Testing

### Test Agent Planning

```python
from agent.powerbi_agent import PowerBIAgent

agent = PowerBIAgent(pbip_root)

# Generate plan without execution
result = agent.process_request(
    "Add KPI card",
    auto_execute=False
)

plan = result["plan"]
print(f"Plan ID: {plan.plan_id}")
print(f"Steps: {len(plan.steps)}")
print(f"Reasoning: {plan.reasoning}")
```

### Test Tool Execution

```python
from server.metadata_tools import MetadataTools

metadata = MetadataTools(pbip_root)

# Test inspection tools
pages = metadata.list_pages()
print(f"Pages: {len(pages['pages'])}")

measures = metadata.list_measures()
print(f"Measures: {len(measures['measures'])}")
```

### Test Validation

```python
from server.validator import ValidatorTools

validator = ValidatorTools(pbip_root)

# Validate full report
result = validator.validate_report()
print(f"Valid: {result['is_valid']}")
print(f"Errors: {result['errors']}")
```

## 🐛 Troubleshooting

### "OpenAI API key not found"

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Or in .env file
OPENAI_API_KEY=sk-...
```

### "PBIP project not found"

```bash
# Ensure PBIP_ROOT points to correct directory
cd powerbi-mcp-agent
export PBIP_ROOT=.
```

### "Tool execution failed"

```python
# Check tool availability
info = agent.tool_router.get_tool_info("tool_name")

# Verify parameters
validation = agent.tool_router.validate_step_feasibility(step)

# Check MCP server logs
tail -f server.log
```

### "Git commit failed"

```bash
# Initialize git repo
cd Sales_report_PBIP
git init
git config user.name "Agent"
git config user.email "agent@powerbi.local"
```

## 📚 Advanced Usage

### Custom Tool Integration

```python
from server.metadata_tools import MetadataTools

class CustomTools(MetadataTools):
    def custom_operation(self):
        # Your custom logic
        pass

# Use custom tools
custom = CustomTools(pbip_root)
```

### Workflow State Monitoring

```python
# Get workflow status
status = agent.workflow_engine.get_execution_status(workflow_id)
print(f"Progress: {status['progress_percent']}%")
print(f"Current step: {status['current_step']}")

# Get workflow history
history = agent.workflow_engine.get_workflow_history(limit=10)
for workflow in history["workflows"]:
    print(f"{workflow['workflow_id']}: {workflow['status']}")
```

### Plan Refinement

```python
# Generate initial plan
plan = agent.planner.plan_workflow(request)

# Get feedback
feedback = "The plan doesn't handle missing measures. Add a creation step."

# Refine plan
refined = agent.planner.refine_plan(plan, feedback)

# Execute refined plan
agent.execute_plan(refined)
```

## 🔐 Security Considerations

1. **API Keys**: Never commit .env file with real API keys
2. **Git History**: Power BI projects may contain sensitive data
3. **Access Control**: Run MCP server on localhost or secure network
4. **Validation**: Always validate changes before auto-commit
5. **Backups**: Keep backups before agent makes major modifications

## 📝 License

This project is provided as-is for Power BI engineering.

## 🤝 Contributing

Contributions welcome! Please:

1. Test changes thoroughly
2. Update documentation
3. Add type hints
4. Follow existing code style
5. Create descriptive commits

## 📞 Support

For issues or questions:

1. Check logs: `tail -f agent.log`
2. Validate PBIP structure: `python -c "from server.pbip_parser import PBIPParser; p = PBIPParser('.')"`
3. Test MCP tools: Visit `http://localhost:8000/docs`
4. Review prompt system: Check `agent/prompts.py`

## 🎓 Learning Resources

- [Power BI PBIP Format](https://docs.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [DAX Language](https://dax.guide/)
- [MCP Protocol](https://modelcontextprotocol.io)
- [OpenAI API](https://platform.openai.com/docs/)

---

**Build the future of Power BI automation with AI agents!** 🚀
