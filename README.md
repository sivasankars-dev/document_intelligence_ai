# Life Admin AI

An AI-powered multi-agent system that helps users manage important life documents such as insurance policies, contracts, agreements, and subscriptions.

---

## 🚀 Problem Statement

Managing life documents manually is difficult. Users often miss:

- Expiry dates
- Important obligations
- Risky clauses
- Renewal reminders
- Contract understanding

Life Admin AI solves this using AI agents.

---

## 🧠 Core Features

- Document ingestion & parsing
- Knowledge extraction
- Risk analysis
- Obligation & reminder generation
- AI-powered document Q&A

---

## 🏗️ Architecture Overview

Mobile App(React Native) -> API Gateway(FastAPI) -> Agent Orchestrator -> Multi-Agent System


---

## 🤖 AI Agents

| Agent | Responsibility |
|--------|-------------|
| Ingestion Agent | File storage and text extraction |
| Extraction Agent | Extract structured knowledge |
| Risk Agent | Detect risky clauses |
| Obligation Agent | Create reminders and obligations |
| QA Agent | Document-based question answering |

---

## 🧰 Tech Stack

### Backend
- FastAPI
- PostgreSQL
- Redis
- Celery
- LangGraph

### AI
- OpenAI
- Chroma Vector DB

### Storage
- AWS S3 / MinIO(Not yet decided)

### Frontend
- React Native

---

## 📊 Development Roadmap

See [ROADMAP.md](ROADMAP.md)

---

## 📚 Documentation

All system documentation is inside `/docs`

---

## ⚡ Getting Started

Coming soon...

---

## 📜 License

MIT License

```
document_intelligence_ai
├─ Docker-compose.yml
├─ README.md
├─ ROADMAP.md
├─ alembic.ini
├─ docs
│  ├─ agents_design.md
│  ├─ data_model.md
│  ├─ scalability_plan.md
│  ├─ sdlc_plan.md
│  ├─ system_design.md
│  └─ vision.md
├─ document_intelligence_ai.code-workspace
├─ gateway
│  ├─ __init__.py
│  ├─ api
│  │  ├─ __init__.py
│  │  └─ v1
│  │     ├─ __init__.py
│  │     ├─ auth_routes.py
│  │     ├─ document_routes.py
│  │     └─ qa_routes.py
│  ├─ dependencies
│  │  └─ auth.py
│  └─ main.py
├─ infrastructure
│  └─ Dockerfile
├─ migrations
│  ├─ README
│  ├─ env.py
│  ├─ script.py.mako
├─ pytest.ini
├─ requirements.txt
├─ services
│  ├─ __init__.py
│  ├─ auth_service
│  │  ├─ __init__.py
│  │  └─ auth_service.py
│  ├─ document_service
│  │  ├─ __init__.py
│  │  └─ document_service.py
│  ├─ extraction_service
│  │  ├─ chunking_service.py
│  │  └─ vector_service.py
│  ├─ ingestion_service
│  │  ├─ __init__.py
│  │  ├─ ingestion_service.py
│  │  └─ parser_service.py
│  ├─ obligation_service
│  ├─ qa_service
│  │  ├─ prompt_service.py
│  │  ├─ qa_pipeline.py
│  │  └─ retriever_service.py
│  ├─ risk_service
│  └─ storage_service
│     ├─ __init__.py
│     └─ storage_service.py
├─ shared
│  ├─ __init__.py
│  ├─ config
│  │  ├─ __init__.py
│  │  └─ settings.py
│  ├─ database
│  │  ├─ __init__.py
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ models
│  │  ├─ __init__.py
│  │  ├─ document.py
│  │  ├─ document_version.py
│  │  └─ user.py
│  └─ schemas
│     ├─ __init__.py
│     ├─ document_schema.py
│     └─ user_schema.py
├─ storage
│  └─ vector_db
├─ tests
│  ├─ __init__.py
│  ├─ debug_vector_check.py
│  ├─ test_auth_routes.py
│  ├─ test_document_upload.py
│  ├─ test_qa_routes.py
│  └─ test_user_registration.py
└─ workers
   ├─ celery_app.py
   └─ tasks
      ├─ __init__.py
      └─ ingestion_tasks.py

```