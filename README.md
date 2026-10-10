# SocialGuard: Explainable Multi-Signal Instagram Fake Account Detection System

Final-Year B.Tech Capstone Project.

SocialGuard is an academic and practical system engineered to detect fake, suspicious, or bot-generated Instagram accounts using multi-signal public observation and Explainable AI (XAI).

---

## 1. Phase 1 Scope & Status

**Phase 1: Project Foundation & Architecture (Current)**
- [x] Monorepo architecture with clean boundaries (`frontend/`, `backend/`, `contracts/`, `docs/`).
- [x] Python FastAPI backend with Pydantic v2 schemas and centralized error handling.
- [x] Authoritative account input validation and canonicalization (`POST /api/v1/accounts/validate`).
- [x] Liveness (`GET /api/v1/health`) and foundation readiness (`GET /api/v1/ready`) endpoints.
- [x] Modern React + TypeScript + Vite frontend with accessible form and state management.
- [x] Typed API service layer with error handling and configurable timeouts.
- [x] Automated backend (pytest) and frontend (Vitest + React Testing Library) test suites passing.
- [x] Formal contracts for collection adapters and future machine learning predictions.

> **Phase 1 Limitation Notice:** Live data acquisition (Instaloader, gallery-dl, Playwright) and machine-learning scoring (XGBoost, SHAP) are not implemented in Phase 1. No real scraping or artificial predictions are generated.

---

## 2. Technology Stack

### Backend
- **Language & Runtime:** Python 3.10+ (tested on Python 3.10.11)
- **Framework:** FastAPI, Uvicorn
- **Validation:** Pydantic v2, Pydantic-Settings
- **Testing:** pytest, pytest-asyncio, HTTPX

### Frontend
- **Framework:** React 19, TypeScript
- **Tooling:** Vite
- **Styling:** Maintainable CSS custom properties (responsive, accessible, clean light aesthetic)
- **Testing:** Vitest, React Testing Library, jsdom

---

## 3. Repository Structure

```
SocialGuard/
  frontend/
    src/
      features/account-analysis/  # Target analysis form & presentation
      services/                   # Typed API service client
      styles/                     # Global CSS styling
      tests/                      # Vitest UI tests
      types/                      # TypeScript API data contracts
      App.tsx                     # Application shell
      main.tsx                    # Entry point
    package.json
    tsconfig.json
    vite.config.ts
    .env.example

  backend/
    app/
      api/routes/                 # Health, readiness & account routes
      core/                       # Config, logging & centralized error handling
      schemas/                    # Pydantic v2 data models
      main.py                     # FastAPI application setup
    tests/                        # Pytest suite
    pyproject.toml

  contracts/
    README.md
    account-contract.md           # Input rules & canonicalization specs
    collection-contract.md        # Collector adapter & future ML schemas

  docs/
    architecture.md               # Architecture diagrams and component boundaries
    development-setup.md          # Comprehensive setup commands

  .env.example                    # Global environment template
  .gitignore
  README.md
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Environment Setup
```bash
cp .env.example .env
```

### 2. Backend Setup & Run
```bash
cd backend
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```
Interactive API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
Application interface: `http://localhost:5173`

---

## 5. Running Automated Tests & Builds

### Backend Tests
```bash
cd backend
.\.venv\Scripts\pytest -v
```

### Frontend Tests & Production Build
```bash
cd frontend
npm run test
npm run build
```

---

## 6. Endpoints Reference (Phase 1)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service liveness health check |
| `GET` | `/api/v1/ready` | Foundation readiness probe (transparently reports planned modules) |
| `POST` | `/api/v1/accounts/validate` | Validates username/URL syntax and computes canonical target representation |

### Validation Example:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/accounts/validate \
  -H "Content-Type: application/json" \
  -d '{"input": "https://www.instagram.com/johndoe/"}'
```
Response:
```json
{
  "success": true,
  "timestamp": "2026-10-11T01:50:00.000000Z",
  "data": {
    "is_valid": true,
    "target": {
      "original_input": "https://www.instagram.com/johndoe/",
      "normalized_username": "johndoe",
      "canonical_profile_url": "https://www.instagram.com/johndoe/",
      "input_type": "profile_url"
    },
    "message": "Target is syntactically valid. Account data collection is planned for Phase 2."
  }
}
```

---

## 7. Upcoming Phases
- **Phase 2:** Multi-source collection adapters (Instaloader, gallery-dl, Playwright) & observation normalization.
- **Phase 3:** Feature extraction pipeline (ratios, graph dynamics, sentiment, media patterns).
- **Phase 4:** ML model training, evaluation (XGBoost) and SHAP explainability.
- **Phase 5:** Full investigation report dashboard & UI visualization.
