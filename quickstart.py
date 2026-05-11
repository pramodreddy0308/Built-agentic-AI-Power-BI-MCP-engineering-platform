#!/usr/bin/env python
"""
Quick start script for Power BI Agentic AI System.

This script sets up and demonstrates the agent capabilities.
Run with: python quickstart.py
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    
    required = [
        "openai",
        "pydantic",
        "fastmcp",
        "mcp",
        "git",
        "dotenv",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  [OK] {package}")
        except ImportError:
            print(f"  [MISSING] {package}")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True


def check_environment():
    """Check environment configuration."""
    print("\nChecking environment...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("  [OK] OPENAI_API_KEY configured")
    else:
        print("  [MISSING] OPENAI_API_KEY not configured")
        print("    Set in .env file: OPENAI_API_KEY=sk-...")
        return False
    
    # Check PBIP_ROOT
    pbip_root = Path(os.getenv("PBIP_ROOT", "."))
    if pbip_root.exists():
        print(f"  [OK] PBIP_ROOT exists: {pbip_root}")
    else:
        print(f"  [MISSING] PBIP_ROOT not found: {pbip_root}")
        return False
    
    return True


def test_agent():
    """Test basic agent functionality."""
    print("\nTesting agent...")
    
    try:
        from agent.powerbi_agent import PowerBIAgent
        from pathlib import Path
        
        pbip_root = Path(os.getenv("PBIP_ROOT", "."))
        agent = PowerBIAgent(pbip_root)
        
        print("  [OK] Agent initialized")
        
        # Get report summary
        summary = agent.get_report_summary()
        print(f"  [OK] Report summary retrieved:")
        print(f"    - Pages: {summary.get('pages_count', 0)}")
        print(f"    - Visuals: {summary.get('visuals_count', 0)}")
        print(f"    - Measures: {summary.get('measures_count', 0)}")
        
        # Validate report
        validation = agent.validate_report()
        print(f"  [OK] Report validation:")
        print(f"    - Valid: {validation.get('is_valid', False)}")
        print(f"    - Errors: {len(validation.get('errors', []))}")
        print(f"    - Warnings: {len(validation.get('warnings', []))}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Test failed: {e}")
        return False


def start_interactive():
    """Start interactive agent mode."""
    print("\n" + "="*70)
    print("Starting Interactive Agent Mode")
    print("="*70)
    
    try:
        from agent.powerbi_agent import PowerBIAgent
        from pathlib import Path
        
        pbip_root = Path(os.getenv("PBIP_ROOT", "."))
        agent = PowerBIAgent(pbip_root)
        agent.interactive_mode()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main quickstart flow."""
    print("\n" + "="*70)
    print("Power BI Agentic AI System - Quick Start")
    print("="*70 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        print("\n[MISSING] Dependency check failed!")
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n[MISSING] Environment check failed!")
        sys.exit(1)
    
    # Test agent
    if not test_agent():
        print("\n[MISSING] Agent test failed!")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("[OK] All checks passed! Agent is ready to use.")
    print("="*70)
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Start interactive agent mode")
    print("2. Start MCP server")
    print("3. Run a test request")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        start_interactive()
    elif choice == "2":
        print("\nStarting MCP server...")
        print("Visit: http://localhost:8000/docs")
        os.system("python server/server.py")
    elif choice == "3":
        test_request()
    else:
        print("Goodbye!")


def test_request():
    """Run a test request."""
    print("\nRunning test request...")
    
    from agent.powerbi_agent import PowerBIAgent
    from pathlib import Path
    
    pbip_root = Path(os.getenv("PBIP_ROOT", "."))
    agent = PowerBIAgent(pbip_root)
    
    # Use a simple test request
    request = "Provide a summary of the current report"
    
    print(f"\nRequest: {request}")
    print("="*70)
    
    try:
        result = agent.process_request(request, auto_execute=False)
        
        if result.get("success"):
            print("\n[OK] Plan generated successfully!")
            plan = result.get("plan")
            if plan:
                print(f"  Plan ID: {plan.plan_id}")
                print(f"  Steps: {len(plan.steps)}")
                print(f"  Goal: {plan.goal}")
        else:
            print(f"\n[ERROR] Failed: {result.get('error')}")
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
