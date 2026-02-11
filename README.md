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
