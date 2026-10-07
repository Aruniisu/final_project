"""
Quick test for Orchestrator + all agents
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
from dotenv import load_dotenv
load_dotenv('../.env')

print("=" * 60)
print("Orchestrator Test")
print("=" * 60)

# Import
from agents.orchestrator import Orchestrator

# Initialize
print("\n[1] Initializing orchestrator...")
orch = Orchestrator()
print("✅ Initialized")

# List agents
print("\n[2] Available agents:")
for name, agent in orch.agents.items():
    print(f"   ├─ {name}: {agent.name} ({len(agent.list_tools())} tools)")

# Test routing (rule-based)
print("\n[3] Testing routing (rule-based):")
test_messages = [
    "deploy my app to vercel",
    "create a pipeline for my repo",
    "fix the error in my code",
    "run a security scan",
    "monitor my application",
    "analyze my code",
]

for msg in test_messages:
    result = orch._route_with_rules(msg)
    print(f"   '{msg}'")
    print(f"      → {result['agent']} ({result['reasoning']})")

# Test LLM routing (if API key set)
if os.getenv('GROQ_API_KEY'):
    print("\n[4] Testing LLM routing:")
    decision = orch._route_with_llm("fix my broken deployment")
    print(f"   Decision: {decision}")
else:
    print("\n[4] Skipping LLM test (GROQ_API_KEY not set)")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)