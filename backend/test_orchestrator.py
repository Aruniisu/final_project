"""
Test Orchestrator routing:
1. Code block → CodeFixerAgent
2. Rule-based routing decisions
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
    print("[TEST] GROQ_API_KEY not set")
    sys.exit(1)

print("[TEST] Environment loaded\n")

from src.agents.orchestrator import Orchestrator

print("=" * 60)
print("TEST 1: Code block + fix request -> CodeFixerAgent")
print("=" * 60)

orch = Orchestrator()

js_code = """
function divide(a, b) {
    return a / b;
}
console.log(divide(10, 0));
"""

result1 = orch.process({
    'action': 'chat',
    'query': f'Please fix this JavaScript code:\n```javascript\n{js_code}\n```',
})

print(f"\nRESULT TYPE: {result1.get('type', 'unknown')}")
print(f"SUCCESS: {result1.get('success')}")
print(f"\nRESPONSE:")
print(result1.get('response', 'no response')[:1500])

print("\n\n" + "=" * 60)
print("TEST 2: Rule-based routing decisions")
print("=" * 60)

test_messages = [
    "Deploy https://github.com/user/myapp to Vercel",
    "Create a CI/CD pipeline for https://github.com/user/myapp",
    "Scan https://github.com/user/myapp for security issues",
    "Fix this code: ```python\nprint(undefined_var)\n```",
    "Monitor https://myapp.com uptime",
    "Hello, what can you do?",
]

for msg in test_messages:
    decision = orch._route_with_rules(msg)
    print(f"\n'{msg[:60]}...'")
    print(f"   -> Routed to: {decision['agent']} (confidence: {decision['confidence']})")
    print(f"   -> Reason: {decision['reasoning']}")