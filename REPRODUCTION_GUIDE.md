# ArchitectOS — Reproduction Guide (Deliverable 02)

This guide provides step-by-step instructions for reproducing the ArchitectOS solution, baseline, evaluation suite, and test suites starting from a clean environment.

---

## 1. Prerequisites

- **OS:** macOS, Linux, or Windows (WSL2)
- **Python:** Version 3.10 or higher
- **Node.js & npm:** Version 18+ (for frontend UI)
- **Docker & Docker Compose** (Optional for containerized run)
- **API Key:** Gemini API Key (Default) or OpenAI/Anthropic/DeepSeek key

---

## 2. Quick Setup from Clean Environment

```bash
# 1. Clone the repository
git clone https://github.com/riswanmsm/architectos-ai.git
cd architectos-ai

# 2. Configure environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (or selected LLM provider key)
```

---

## 3. Running the Test Suites

Run the full offline test suite (no API key or network required):

```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run backend unit & verifier tests
PYTHONPATH=backend:. python -m unittest discover -s backend/tests

# Run evaluation & provider schema tests
python -m unittest discover -s evaluation/tests
```

**Expected Output:**
```text
Ran 3 tests in 0.9s — OK
Ran 18 tests in 0.02s — OK
```

---

## 4. Running the Benchmark Evaluations

### A. Run One-Prompt Baseline on 10 Benchmark Cases
```bash
python -m evaluation.baseline --cases evaluation/cases.json --overwrite
```
*Output stored in:* `evaluation/results/baseline/`

### B. Run ArchitectOS Multi-Agent Evaluation on 10 Benchmark Cases
```bash
python -m evaluation.run_agent_eval --cases evaluation/cases.json --overwrite
```
*Output stored in:* `evaluation/results/agent/`

### C. Compare Baseline vs ArchitectOS
```bash
python -m evaluation.compare
```
*Expected Output:* Side-by-side terminal and markdown comparison showing Verified Blueprint Coverage (VBC), Critical Findings delta, Latency, and Cost.

---

## 5. Running the Interactive Application

### Option A: Via Docker (Recommended)
```bash
docker-compose up --build
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

### Option B: Local Dev Servers

**Terminal 1 — Backend:**
```bash
source .venv/bin/activate
uvicorn --app-dir backend app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)**.

---

## 6. Approximate Runtime and Cost

| Task | Approximate Runtime | Approximate Cost (Gemini 3.7 Flash) |
| :--- | :---: | :---: |
| Full 10-Case Baseline Eval | ~45 seconds | < $0.02 USD |
| Full 10-Case Agent Eval | ~180 seconds | < $0.08 USD |
| Interactive Session Generation | ~25 seconds | < $0.01 USD |
| Unit Test Suite (Offline) | < 2 seconds | $0.00 |

---

## 7. Troubleshooting

- **Missing `pydantic` or dependencies:** Ensure the virtual environment is activated (`source .venv/bin/activate`) and `pip install -r backend/requirements.txt` was executed.
- **Provider API Rate Limits:** ArchitectOS automatically handles fallbacks if provider quotas are exceeded.
- **Port Conflicts:** Ensure ports `8000` (FastAPI) and `5173` (Vite) are available.
