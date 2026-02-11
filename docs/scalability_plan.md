# Scalability Plan

## Stage 1 – Monolith
- Single FastAPI service
- Celery workers
- PostgreSQL + Chroma

---

## Stage 2 – Microservices
- Separate services for each agent
- Kafka event streaming
- Independent scaling

---

## Stage 3 – Cloud Native
- Kubernetes deployment
- Horizontal scaling
- Multi-region deployment
