import subprocess
import os
import socket
import json
import time
import requests
import yaml
from pathlib import Path

# ============================================
# Configuration
# ============================================
CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
CF_ZONE = os.getenv("CLOUDFLARE_ZONE_ID")
TUNNEL_ID = "768b9df6-6a35-422b-9898-b3f250ef3a1b"
BASE_DOMAIN = "smartdevops.site"
CONFIG_PATH = Path.home() / ".cloudflared" / "config.yml"
APPS_DIR = Path("./deployed_apps")
APPS_DIR.mkdir(exist_ok=True)


# ============================================
# Helper Functions
# ============================================
def find_free_port(start=8000):
    """Find a free port starting from 8000."""
    for port in range(start, start + 100):
        with socket.socket() as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    raise Exception("No free ports available.")


def clone_and_run(git_url, project_name, port):
    """Clone GitHub repo and run the app on the given port."""
    project_path = APPS_DIR / project_name

    if project_path.exists():
        subprocess.run(f'rmdir /s /q "{project_path}"', shell=True)

    subprocess.run(f'git clone {git_url} "{project_path}"', shell=True, check=True)

    env = {**os.environ, "PORT": str(port)}

    if (project_path / "requirements.txt").exists():
        subprocess.run("pip install -r requirements.txt", cwd=project_path, shell=True)
        subprocess.Popen("python app.py", cwd=project_path, shell=True, env=env)
    elif (project_path / "package.json").exists():
        subprocess.run("npm install", cwd=project_path, shell=True)
        subprocess.Popen("npm start", cwd=project_path, shell=True, env=env)

    time.sleep(5)


def add_cloudflare_dns(subdomain):
    """Create a Cloudflare DNS record pointing to the tunnel."""
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "CNAME",
        "name": subdomain,
        "content": f"{TUNNEL_ID}.cfargotunnel.com",
        "proxied": True
    }
    r = requests.post(url, headers=headers, json=data).json()
    if not r.get("success"):
        errors = str(r.get("errors", []))
        if "already exists" in errors.lower():
            return True
        raise Exception(f"DNS error: {errors}")
    return True


def update_tunnel_config(subdomain, port):
    """Add a new ingress rule to the tunnel config and restart cloudflared."""
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f) or {}

    if "ingress" not in config:
        config["ingress"] = []

    existing = [r for r in config["ingress"] if r.get("hostname") == subdomain]
    if existing:
        existing[0]["service"] = f"http://localhost:{port}"
    else:
        config["ingress"].insert(-1, {
            "hostname": subdomain,
            "service": f"http://localhost:{port}"
        })

    if not any(r.get("service") == "http_status:404" for r in config["ingress"]):
        config["ingress"].append({"service": "http_status:404"})

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    subprocess.run("taskkill /F /IM cloudflared.exe", shell=True, capture_output=True)
    time.sleep(1)
    subprocess.Popen(
        ["cloudflared", "tunnel", "run", "smartdevops-tunnel"],
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0x00000008
    )
    time.sleep(3)


# ============================================
# MAIN DEPLOY FUNCTION
# ============================================
def deploy(git_url):
    """Deploy a GitHub repo and return a live URL."""
    project_name = git_url.rstrip("/").split("/")[-1].replace(".git", "").lower()
    project_name = project_name.replace("_", "-").replace(" ", "-")

    print(f"Deploying {project_name}...")

    port = find_free_port()
    print(f"Port: {port}")

    clone_and_run(git_url, project_name, port)
    print(f"App running on port {port}")

    subdomain = f"{project_name}.deploy.{BASE_DOMAIN}"
    add_cloudflare_dns(subdomain)
    print(f"DNS created: {subdomain}")

    update_tunnel_config(subdomain, port)
    print(f"Tunnel updated")

    live_url = f"https://{subdomain}"
    print(f"\nLIVE URL: {live_url}\n")

    return {
        "success": True,
        "url": live_url,
        "port": port,
        "project": project_name
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent_deployer.py <github_url>")
        sys.exit(1)

    result = deploy(sys.argv[1])
    print(json.dumps(result, indent=2))