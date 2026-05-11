# Quick Reference Card

## Setup (5 minutes)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env - add OPENAI_API_KEY=sk-...

# 3. Test
python quickstart.py
```

## Usage Patterns

### Pattern 1: Non-Interactive (Script)
```python
from pathlib import Path
from agent.powerbi_agent import PowerBIAgent

agent = PowerBIAgent(Path("."))

result = agent.process_request(
    "Add Total Revenue KPI",
    auto_execute=True
)

if result["success"]:
    print("✓ Done!")
else:
    print(f"✗ Error: {result['error']}")
```

### Pattern 2: Interactive Mode
```python
from agent.powerbi_agent import PowerBIAgent
from pathlib import Path

agent = PowerBIAgent(Path("."))
agent.interactive_mode()

# Type requests:
# 📊 Request: List all measures
# 📊 Request: Add KPI card
# 📊 Request: exit
```

### Pattern 3: Plan-First Execution
```python
# Generate plan without executing
result = agent.process_request(request, auto_execute=False)
plan = result["plan"]

# Review plan
print(f"Steps: {len(plan.steps)}")
for step in plan.steps:
    print(f"  - {step.step_name}")

# Then execute it
execution = agent.execute_plan(plan)
```

### Pattern 4: MCP Server
```bash
# Terminal 1: Start server
python server/server.py

# Terminal 2: Make requests
curl http://localhost:8000/tool/list_pages
curl -X POST http://localhost:8000/tool/validate_report
```

## Common Requests

```python
agent.process_request("Show me all pages in this report", auto_execute=True)
agent.process_request("List all measures in FactOrders", auto_execute=True)
agent.process_request("Create Total Revenue measure", auto_execute=True)
agent.process_request("Add KPI card to Executive Dashboard", auto_execute=True)
agent.process_request("Replace pie charts with bar charts", auto_execute=True)
agent.process_request("Validate the report", auto_execute=True)
agent.process_request("Show recent commits", auto_execute=True)
```

## MCP Tools Quick Access

### Inspection
```python
from server.metadata_tools import MetadataTools

metadata = MetadataTools(Path("."))

metadata.list_pages()           # Get pages
metadata.list_visuals(page_id)  # Get visuals
metadata.list_tables()          # Get tables
metadata.list_measures()        # Get measures
metadata.search_visuals(term)   # Find visuals
metadata.get_report_summary()   # Overview
```

### DAX
```python
from server.dax_tools import DAXTools

dax = DAXTools(Path("."))

dax.create_measure(...)        # Create measure
dax.validate_dax(expression)   # Validate
dax.get_common_dax_patterns()  # Get templates
```

### Visuals
```python
from server.visual_tools import VisualTools

visuals = VisualTools(Path("."))

visuals.add_kpi_card(...)        # Add KPI
visuals.replace_visual(...)      # Change type
visuals.move_visual(...)         # Move visual
visuals.auto_arrange_visuals(..) # Grid layout
```

### Git
```python
from server.git_tools import GitTools

git = GitTools(Path("."))

git.git_commit(message)        # Create commit
git.get_status()               # Git status
git.get_commit_history()       # View history
git.rollback_changes()         # Undo changes
```

### Validation
```python
from server.validator import ValidatorTools

validator = ValidatorTools(Path("."))

validator.validate_report()    # Full validation
validator.validate_measure()   # Measure check
validator.validate_visual()    # Visual check
```

## MCP Tools Complete List

**Metadata** (12):
- hello, list_pages, list_visuals, list_tables, list_measures, list_columns
- get_visual_details, get_table_details, get_measure_details
- search_visuals, search_measures, get_report_summary

**DAX** (6):
- create_measure, update_measure, validate_dax
- get_common_dax_patterns, extract_dax_functions, get_dax_dependencies

**Visuals** (10):
- add_kpi_card, update_visual_title, move_visual, resize_visual
- replace_visual, duplicate_visual, delete_visual, batch_update_visuals
- get_visual_layout_info, auto_arrange_visuals

**Git** (9):
- git_commit, get_status, get_commit_history
- create_branch, switch_branch, list_branches
- rollback_changes, tag_release, get_diff

**Validation** (5):
- validate_report, validate_visual, validate_measure, validate_table
- get_validation_summary

**Total: 52 tools**

## Debugging

```bash
# Check dependencies
python -m pip list | grep -E "mcp|pydantic|openai"

# Test agent setup
python -c "from agent.powerbi_agent import PowerBIAgent; print('✓ OK')"

# Check environment
python -c "import os; print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"

# Test MCP tools
python -c "from server.metadata_tools import MetadataTools; m=MetadataTools('.'); print(m.hello())"

# View logs
tail -f agent.log
```

## Configuration

**Key environment variables:**

```bash
OPENAI_API_KEY=sk-...           # Required!
PBIP_ROOT=.                      # PBIP directory
MCP_PORT=8000                    # Server port
GIT_AUTHOR=Power BI Agent        # Commit author
AUTO_VALIDATE=true               # Validate after changes
AUTO_COMMIT=true                 # Auto-commit
```

## Architecture Diagram

```
┌─────────────────┐
│ User Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ Planner Agent       │ ← GPT-4 reasoning
│ (GPT-4 Turbo)       │
└────────┬────────────┘
         │ JSON Plan
         ▼
┌─────────────────────┐
│ Workflow Engine     │ ← Step execution
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Tool Router         │ ← MCP tool routing
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ MCP Tools (52)      │ ← Metadata, DAX, Visual, Git, Validation
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ PBIP Modifications  │ ← Files updated
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Validation          │ ← Report integrity check
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Git Commit          │ ← Version control
└─────────────────────┘
```

## Workflow Execution States

```
pending  → running → completed ✓
                  ↓
                failed  → rollback → reverted
                ↑
              error handling
```

## Performance Tips

1. **Batch operations**: Group related requests
2. **Plan review**: Use `auto_execute=False` first
3. **Caching**: Reuse agent instance
4. **Validation**: Check critical changes manually
5. **Commits**: Group into logical batches

## Error Handling

```python
try:
    result = agent.process_request(request, auto_execute=True)
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    
if not result.get("success"):
    errors = result.get("error")
    print(f"Execution failed: {errors}")
```

## File Locations

```
Project Root: ~/powerbi-mcp-agent/
PBIP Files: ./Sales_report_PBIP/
Logs: ./agent.log
Config: ./.env
```

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: mcp` | `pip install -r requirements.txt` |
| `OPENAI_API_KEY not set` | Edit `.env` file |
| `PBIP not found` | Check `PBIP_ROOT` in `.env` |
| `Git error` | Run `git init` in PBIP folder |
| `Permission denied` | Check file permissions |

## Support Resources

- **README.md** - Full documentation
- **GETTING_STARTED.md** - Setup guide
- **server/server.py** - API docs at `/docs`
- **agent/prompts.py** - AI system prompts
- **BUILD_SUMMARY.md** - Architecture overview

## One-Liners

```bash
# Start interactive mode
python -c "from agent.powerbi_agent import PowerBIAgent; from pathlib import Path; PowerBIAgent(Path('.')).interactive_mode()"

# Quick validation
python -c "from agent.powerbi_agent import PowerBIAgent; from pathlib import Path; print(PowerBIAgent(Path('.')).validate_report())"

# Get report summary
python -c "from agent.powerbi_agent import PowerBIAgent; from pathlib import Path; print(PowerBIAgent(Path('.')).get_report_summary())"

# Start MCP server
python server/server.py
```

---

**Last Updated**: 2024-05-10
**Version**: 1.0.0
**Status**: Production Ready ✅
