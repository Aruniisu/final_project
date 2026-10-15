# 🚀 Agentic AI-Powered Smart DevOps Assistant

> Autonomous Software Delivery & Infrastructure Management through Multi-Agent AI

**Built with:** Python · Flask · React · MongoDB · Groq API · scikit-learn

---

## 📌 Overview

An autonomous DevOps platform powered by **10 AI agents** that deploy applications from natural language commands.

**Key Achievement:** 100% deployment success rate across tested full-stack applications with self-learning ML pipeline achieving **90.3% accuracy**.

---

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **10 autonomous AI agents** coordinated through 2 orchestration patterns
- LLM-based Orchestrator routes tasks to 9 specialist agents
- Standalone InfraAgent with its own perception-reasoning-action loop

### 🧠 Self-Learning ML Pipeline
- Every agent action logged as 8-dimensional feature vector
- Auto-retrain every 60 seconds using scikit-learn
- 8 model generations | 90.3% average accuracy
- Stable CRC32 hashing for deterministic features

### ⚙️ Autonomous Infrastructure Management
- **InfraAgent** with 3 operational modes: Off, Assistive, Autonomous
- 6 registered tools: launch, stop, restart, scale, cleanup, notify
- 5 reasoning rules: High CPU, Crashed Services, High Memory, High Disk, CPU Trend
- Safety limits: max scale 10, cooldown 60s, 30 actions/hour

### 🚀 8-Stage Deployment Pipeline
- Clone → Detect → Build → Deploy → URL
- 1,488 lines of production-grade deployment code
- Parallel builds using ThreadPoolExecutor
- Multi-tenant port isolation
- Cloudflare Tunnel integration for public URLs

### 📊 Real-Time Synchronization
- 6 React dashboards synced via Socket.IO
- Event bus with replay buffer for missed events
- Live logs panel for agent actions

---

## 🏗️ System Architecture

FRONTEND (React)
  6 Dashboards · Socket.IO Real-time · Tailwind CSS
        │
        │ WebSocket / REST
        ▼
BACKEND (Flask + Python)
  Orchestrator (LLM-Based Routing — Groq API)
  ├─ DeployAgent      ├─ SecurityAgent
  ├─ PipelineAgent    ├─ CodeFixerAgent
  ├─ HealerAgent      ├─ ErrorRecoveryAgent
  ├─ MonitorAgent     ├─ AnalyzerAgent
  └─ PlannerAgent     └─ InfraAgent (Standalone)
  Event Bus · ML Feedback · MongoDB · Auto-Retrain
        │
        │ Read / Write
        ▼
DEPLOYMENT (SelfHostService)
  Clone → Detect → Build → Deploy → Generate URL

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **AI/ML** | Python, Groq API (gpt-oss-120b), scikit-learn, Multi-Agent Systems |
| **Backend** | Flask, Flask-SocketIO, Socket.IO, REST APIs |
| **Frontend** | React, Tailwind CSS, DaisyUI, Framer Motion, Chart.js |
| **Database** | MongoDB (Flask-PyMongo) |
| **DevOps** | GitHub Actions, CI/CD, Cloudflare Tunnel, Docker |
| **Tools** | Git, VS Code, Postman, reportlab |

---

## 📊 Results

| Metric | Value |
|--------|-------|
| **Total Deployments** | 2 |
| **Success Rate** | 100% |
| **Average Deployment Time** | 518 seconds |
| **ML Model Generations** | 8 |
| **ML Average Accuracy** | 90.3% |
| **Backend Files** | 127 Python files |
| **Frontend Files** | 44 JavaScript/JSX files |
| **SelfHostService Lines** | 1,488 lines |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB
- Groq API Key

### Backend Setup

git clone https://github.com/Aruniisu/final_project.git
cd final_project

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python app.py

### Frontend Setup

cd frontend
npm install
npm start

### Access

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5000

---

## 🎯 Use Cases

### Natural Language Commands

Deploy https://github.com/user/repo
Create CI/CD pipeline for my-project
Scan repo for vulnerabilities
Monitor my app
Scale service to 3 replicas

### For Businesses

- Automated deployments — no manual pipeline setup
- Self-healing systems — auto-fix common errors
- Cost optimization — identify idle services
- Real-time monitoring — 6 dashboards

---

## 📚 Documentation

- **Portfolio:** jade-kleicha-aa1c89.netlify.app
  
---

## 📄 License

This project is licensed under the **MIT License** — see the LICENSE file for details.

---

⭐ **Star this repo if you found it useful!**
