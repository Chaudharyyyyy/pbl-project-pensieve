# Pensieve

> A privacy-first reflective journaling system with ML-powered pattern recognition and psychological grounding.

![Privacy-First](https://img.shields.io/badge/Privacy-First-green)
![ML-Powered](https://img.shields.io/badge/ML-Powered-blue)
![License](https://img.shields.io/badge/License-Internal-red)

## Overview

Pensieve analyzes your journal entries longitudinally to detect emotional, thematic, and linguistic patterns. It generates grounded, explainable reflections citing psychological theories and philosophical frameworks—all while prioritizing your privacy.

### Key Features

- 🔐 **End-to-End Encryption** — AES-256-GCM encryption with per-user keys
- 🧠 **ML Pattern Detection** — Emotions, themes, linguistic trends, temporal patterns  
- 📚 **Grounded Insights** — Every reflection cites psychological/philosophical concepts
- 🤫 **Zero-Knowledge Architecture** — Server cannot decrypt your journals
- ⚖️ **Ethical Constraints** — Never diagnoses, never prescribes, never overclaims

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pensieve
   ```

2. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your settings (especially SECRET_KEY)
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec backend python scripts/populate_concepts.py
   ```

5. **Access the app**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/api
   - API Docs: http://localhost:8000/api/docs

## Architecture

```
┌─────────────────────────────────────┐
│         Frontend (Next.js)          │
│   • Journal UI with autosave        │
│   • Reflection display              │
│   • Pattern timeline                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Backend (FastAPI)           │
│   • Authentication (Argon2/JWT)     │
│   • Encrypted entry storage         │
│   • Reflection generation           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          ML Pipeline                │
│   • Emotion Detection (GoEmotions)  │
│   • Theme Clustering (HDBSCAN)      │
│   • Linguistic Analysis (spaCy)     │
│   • Temporal Tracking               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   PostgreSQL + pgvector + Redis     │
│   • Encrypted journals              │
│   • Pattern metadata                │
│   • Concept embeddings for RAG      │
└─────────────────────────────────────┘
```

## Ethical Constraints (Enforced in Code)

| Constraint | Implementation |
|------------|----------------|
| **Confidence Capping** | Maximum 80% confidence on all insights |
| **Hedging Language** | Reflections must use "may suggest", "resembles", etc. |
| **Rate Limiting** | Maximum 2 reflections per week |
| **Minimum Data** | Requires 3+ entries over 7+ days for reflection |
| **No Diagnostics** | Blocked patterns prevent clinical language |
| **Always Disclaimed** | Every reflection includes disclaimer |

## Project Structure

```
pensieve/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, auth, encryption
│   │   ├── ml/             # ML models
│   │   ├── models/         # SQLAlchemy models
│   │   └── services/       # Business logic
│   └── pyproject.toml
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # Pages
│       └── components/     # React components
├── schemas/                # PostgreSQL schemas
├── data/                   # Concept database
├── scripts/                # Utility scripts
└── docker-compose.yml
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login and get token |
| `/api/entries` | GET/POST | List/create entries |
| `/api/entries/autosave` | POST | Autosave draft |
| `/api/reflections/suggest` | GET | Generate reflections |
| `/api/concepts` | GET | Browse concept database |

## ML Models

| Component | Model | Dataset |
|-----------|-------|---------|
| Emotion Detection | RoBERTa | GoEmotions (58K) |
| Theme Clustering | Sentence-BERT + HDBSCAN | - |
| Linguistic Analysis | spaCy en_core_web_sm | - |
| Concept Retrieval | Sentence-BERT | Custom (54 concepts) |

## Security

- **Encryption**: AES-256-GCM with per-user keys derived via PBKDF2
- **Password Hashing**: Argon2id (winner of Password Hashing Competition)
- **Session Tokens**: Short-lived JWTs (24h default)
- **Zero-Knowledge**: Server cannot decrypt without user authentication

## Development

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Database

Pensieve includes 54 curated psychological and philosophical concepts:

- **Psychology**: CBT, positive psychology, attachment theory, emotion regulation
- **Philosophy**: Stoicism, existentialism, Buddhist psychology
- **Research**: Peer-reviewed findings with citations

*"Pensieve learns with you, not from you. Your patterns stay yours—they never improve our system for others."*
