# Getting Started Guide

Complete setup and first-use guide for the Power BI Agentic AI System.

## Step 1: Prerequisites

Ensure you have:
- Python 3.10 or higher
- pip (Python package manager)
- A Power BI PBIP project directory
- OpenAI API key (GPT-4 access)
- Git installed and configured

### Check Python version

```bash
python --version
# Should output Python 3.10.x or higher
```

### Check Git

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Step 2: Clone/Download Project

```bash
# Navigate to your workspace
cd ~/Documents/NIT\ task

# Download the project
git clone <repo-url> powerbi-mcp-agent
cd powerbi-mcp-agent
```

## Step 3: Install Dependencies

### Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

This installs:
- `mcp` - Model Context Protocol
- `fastmcp` - FastMCP server framework
- `openai` - OpenAI Python SDK
- `pydantic` - Data validation
- `gitpython` - Git operations
- `python-dotenv` - Environment configuration

## Step 4: Configure Environment

### Create .env File

```bash
cp .env.example .env
```

### Edit .env with Your Settings

```bash
# Get your API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-key-here

# Point to your PBIP project root
PBIP_ROOT=./Sales_report_PBIP

# Other settings (optional)
MCP_PORT=8000
GIT_AUTHOR=Power BI Agent
```

**Important**: Never commit `.env` with real API keys!

## Step 5: Prepare PBIP Project

### Initialize Git

If your PBIP project isn't in git yet:

```bash
cd Sales_report_PBIP
git init
git config user.email "agent@powerbi.local"
git add .
git commit -m "Initial Power BI project"
cd ..
```

### Verify Structure

```bash
# Should see these folders
ls -la Sales_report_PBIP/
# Output should include:
# - Sales_report_PBIP.Report/
# - Sales_report_PBIP.SemanticModel/
```

## Step 6: Run Quick Start

```bash
python quickstart.py
```

This will:
1. ✓ Check all dependencies
2. ✓ Verify environment configuration
3. ✓ Test agent initialization
4. ✓ Display report summary
5. ✓ Offer interactive options

## Step 7: First Request

### Option A: Interactive Mode

```bash
python quickstart.py
# Select option 1: Start interactive agent mode

# Then type your request:
📊 Request: Provide a summary of the current report
📊 Request: List all measures in FactOrders table
📊 Request: exit
```

### Option B: Python Script

```python
from pathlib import Path
from agent.powerbi_agent import PowerBIAgent

# Initialize
agent = PowerBIAgent(Path("."))

# Make request
result = agent.process_request(
    "List all measures in the semantic model",
    auto_execute=True
)

# Check result
if result["success"]:
    print("✓ Success!")
    print(result)
else:
    print(f"✗ Error: {result['error']}")
```

### Option C: MCP Server

```bash
# Start server
python server/server.py

# In another terminal, test an endpoint
curl http://localhost:8000/tool/hello
```

## Common First Tasks

### Task 1: Inspect Your Report

```python
from pathlib import Path
from agent.powerbi_agent import PowerBIAgent

agent = PowerBIAgent(Path("."))

# Get pages
pages = agent.get_report_summary()
print(f"Pages: {pages['pages_count']}")
print(f"Visuals: {pages['visuals_count']}")
print(f"Measures: {pages['measures_count']}")
```

### Task 2: List Pages

```python
request = "Show me all pages in this report"
result = agent.process_request(request, auto_execute=False)
plan = result["plan"]
# Shows execution plan without running it
```

### Task 3: Create a Measure

```python
request = "Create a new measure called 'Total Revenue' in FactOrders table"
result = agent.process_request(request, auto_execute=True)
# Will plan and execute the measure creation
```

### Task 4: Add a KPI Card

```python
request = "Add a KPI card showing Total Revenue to the first page"
result = agent.process_request(request, auto_execute=True)
# Will create the KPI and commit changes
```

## Troubleshooting First Run

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution**: Reinstall dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Issue: "OPENAI_API_KEY not configured"

**Solution**: Check your .env file
```bash
cat .env | grep OPENAI_API_KEY
# Should show: OPENAI_API_KEY=sk-...
```

If not set:
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Issue: "PBIP project not found"

**Solution**: Verify PBIP_ROOT path
```bash
# Check if directory exists
ls Sales_report_PBIP/

# Update PBIP_ROOT in .env if needed
echo "PBIP_ROOT=./Sales_report_PBIP" >> .env
```

### Issue: "Permission denied" on quickstart.py

**Solution**: Make executable
```bash
chmod +x quickstart.py
python quickstart.py
```

### Issue: "Git not configured"

**Solution**: Configure git locally
```bash
cd Sales_report_PBIP
git config user.email "agent@powerbi.local"
git config user.name "Power BI Agent"
```

## What's Next?

After successful setup:

1. **Explore MCP Tools**: Visit http://localhost:8000/docs (when server running)
2. **Read Documentation**: Review README.md for full capability list
3. **Try Advanced Requests**: 
   - "Replace pie charts with bar charts"
   - "Add dark theme to the report"
   - "Create Year-to-Date sales measure"
4. **Create Custom Workflows**: Chain multiple operations
5. **Integrate with Power BI**: Upload modified PBIP back to Power BI Service

## Performance Tips

1. **Use Specific Requests**: Be clear about what you want
   - Good: "Add Total Revenue KPI to Executive Dashboard page"
   - Bad: "Add a KPI"

2. **Plan Before Execute**: Use `auto_execute=False` first
   ```python
   result = agent.process_request(request, auto_execute=False)
   # Review plan, then execute
   ```

3. **Batch Operations**: Group related changes
   - One request: "Replace all pie charts and add KPI"
   - Instead of: Three separate requests

4. **Validate Often**: Check report after major changes
   ```python
   validation = agent.validate_report()
   ```

## Security Best Practices

1. **Protect API Keys**
   - Never share `.env` file
   - Never commit `.env` to git
   - Rotate API keys regularly

2. **Backup Before Changes**
   - Commit current state first
   - Keep backup branches
   - Test in dev environment

3. **Review Changes**
   - Don't use `auto_execute=True` for production changes
   - Review plans before execution
   - Validate results afterward

4. **Git Hygiene**
   - Make meaningful commits
   - Use branch for major changes
   - Tag releases

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Check [MCP Tools Reference](README.md#-mcp-tools-reference)
3. Review [Example Workflows](README.md#-example-workflows)
4. Explore [Advanced Usage](README.md#-advanced-usage)

## Support

If you encounter issues:

1. Check logs: `tail -f agent.log`
2. Test components individually
3. Review environment: `echo $OPENAI_API_KEY`
4. Validate PBIP structure: `ls Sales_report_PBIP/definition/`
5. Check git: `cd Sales_report_PBIP && git status`

## Cheat Sheet

```bash
# Quick start
python quickstart.py

# Start interactive mode
python agent/powerbi_agent.py

# Start MCP server
python server/server.py

# Test specific tool
python -c "from server.metadata_tools import MetadataTools; t=MetadataTools('.'); print(t.hello())"

# Activate environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# View log
tail -f agent.log

# Check git status
cd Sales_report_PBIP && git status
```

---

Happy automating! 🚀
