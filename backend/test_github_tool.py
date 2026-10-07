"""
Test github_get_repo_info tool directly.
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load env
cwd = Path.cwd()
for env_path in [cwd / '.env', cwd / 'src' / '.env']:
    if env_path.exists():
        load_dotenv(env_path, override=True)

token = os.getenv('GITHUB_TOKEN')
print(f"[TEST] Token: {token[:10]}... ({len(token)} chars)")
print()

# ============================================
# Test 1: Direct API call with 30s timeout
# ============================================
print("=" * 60)
print("TEST 1: Direct GitHub API call (30s timeout)")
print("=" * 60)

url = "https://api.github.com/repos/Aruniisu/Tomo-coffee"
print(f"[TEST] URL: {url}")

start = time.time()
try:
    response = requests.get(
        url,
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'Smart-DevOps-AI',
        },
        timeout=30,
    )
    elapsed = time.time() - start
    print(f"[TEST] Status: {response.status_code} ({elapsed:.2f}s)")

    if response.status_code == 200:
        data = response.json()
        print(f"[TEST] ✅ Repo: {data.get('name')}")
        print(f"       Branch: {data.get('default_branch')}")
        print(f"       Private: {data.get('private')}")
    else:
        print(f"[TEST] ❌ Error: {response.text[:500]}")

except requests.Timeout:
    print(f"[TEST] ❌ TIMEOUT after {time.time() - start:.1f}s")
except Exception as e:
    print(f"[TEST] ❌ Exception: {type(e).__name__}: {e}")