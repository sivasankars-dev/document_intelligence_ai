# System Design

## 🏗️ High-Level Architecture

Client -> API Gateway -> Agent Orchestrator -> Agents -> Storage

---

## 🔄 Document Processing Flow

1. User uploads document
2. Document stored in object storage
3. Ingestion agent extracts raw text
4. Extraction agent identifies structured data
5. Risk agent flags potential issues
6. Obligation agent creates reminders
7. QA agent provides user queries

---

## 🗄️ Storage Layer

### PostgreSQL
- Metadata
- Extracted facts
- Obligations
- Risk flags

### Vector Database
- Document embeddings

### Object Storage
- Raw document storage

---

## 🧠 Orchestration Layer

- Event-driven workflow
- Background job processing
- Retry and idempotency support
