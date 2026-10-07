"""
Test PipelineAgent with REAL GitHub repo.

⚠️ REPLACE the URL below with YOUR test repo!
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
cwd = Path.cwd()
for env_path in [cwd / '.env', cwd / 'src' / '.env']:
    if env_path.exists():
        load_dotenv(env_path, override=True)

if not os.getenv('GROQ_API_KEY'):
    print("❌ GROQ_API_KEY not set")
    sys.exit(1)

if not os.getenv('GITHUB_TOKEN'):
    print("❌ GITHUB_TOKEN not set")
    sys.exit(1)

print("[TEST] Environment loaded")
print(f"[TEST] GitHub token: {os.getenv('GITHUB_TOKEN')[:8]}...")
print()

# ============================================
# ⚠️ REPLACE THIS WITH YOUR TEST REPO URL
# ============================================
TEST_REPO = "https://github.com/your-actual-username/test-agentic-pipeline"

if 'YOUR_USERNAME' in TEST_REPO:
    print("⚠️  Please edit this file and set TEST_REPO to your own repo URL")
    print("   Example: https://github.com/john/test-agentic-pipeline")
    sys.exit(1)

from src.agents.orchestrator import Orchestrator

print("=" * 60)
print(f"TEST: Autonomous Pipeline + Auto-Fix Loop")
print(f"Repo: {TEST_REPO}")
print("=" * 60)
print()

orch = Orchestrator()

result = orch.process({
    'action': 'pipeline',
    'repo_url': TEST_REPO,
})

print("\n\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)
print(f"SUCCESS: {result.get('success')}")
print(f"STATUS: {result.get('status')}")
print(f"AUTO-FIXES APPLIED: {result.get('auto_fixes_applied', 0)}")
print(f"FIX ATTEMPTS: {result.get('fix_attempts', 0)}")
print(f"DURATION: {result.get('duration', 'N/A')}")
print(f"\nWORKFLOW: {result.get('workflow_file', 'N/A')}")
print(f"COMMIT: {result.get('commit_sha', 'N/A')}")
print(f"ACTIONS URL: {result.get('actions_url', 'N/A')}")
print(f"\nRESPONSE:")
print(result.get('response', 'no response'))