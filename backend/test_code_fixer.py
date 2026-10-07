"""
Test CodeFixerAgent — Robust env loading.
"""
import os
import sys
from pathlib import Path

# ============================================
# Find and load .env from multiple possible locations
# ============================================
from dotenv import load_dotenv

# Current working directory
cwd = Path.cwd()
print(f"[TEST] CWD: {cwd}")

# Try multiple locations
env_candidates = [
    cwd / '.env',                          # backend/.env
    cwd / 'src' / '.env',                  # backend/src/.env
    Path(__file__).parent / '.env',        # script dir
    Path(__file__).parent / 'src' / '.env',
]

loaded = False
for env_path in env_candidates:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"[TEST] ✅ Loaded env from: {env_path}")
        loaded = True

if not loaded:
    print("[TEST] ⚠️ No .env file found. Using existing environment variables.")

# Verify
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("[TEST] ❌ GROQ_API_KEY not set!")
    print("[TEST] Please add it to backend/.env or backend/src/.env")
    sys.exit(1)

print(f"[TEST] ✅ GROQ_API_KEY: {groq_key[:10]}... ({len(groq_key)} chars)")
print(f"[TEST] ✅ GROQ_MODEL: {os.getenv('GROQ_MODEL', 'not set')}")
print()

# ============================================
# Now import and test
# ============================================
from src.agents.specialists.code_fixer_agent import CodeFixerAgent

agent = CodeFixerAgent()

test_code = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)

result = calculate_average([])
print(result)
"""

result = agent.process({
    'query': f'Fix this code. Error: ZeroDivisionError\n```python\n{test_code}\n```',
    'code': test_code,
    'error': 'ZeroDivisionError: division by zero',
})

print("\n" + "=" * 60)
print("SUCCESS:", result.get('success'))
print("=" * 60)

if result.get('success'):
    print("\n✅ FIXED CODE:")
    print(result.get('fixed_code', ''))
    print("\n" + "=" * 60)
    print("\n📝 EXPLANATION:")
    print(result.get('explanation', ''))
    print("\n" + "=" * 60)
    print("\n🐞 ISSUES:")
    for issue in result.get('issues', []):
        print(f"  - [{issue.get('type')}] {issue.get('description')}")
else:
    print("\n❌ ERROR:", result.get('error'))