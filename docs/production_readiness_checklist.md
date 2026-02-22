# Production Readiness Checklist

Last updated: 2026-02-21
Scope: Backend/API + workers for `document_intelligence_ai`

## Current Verdict

Go/No-Go: **NO-GO**

Reason: Operational gaps (observability/runbooks/deployment) and one unstable external-LLM integration test remain.

## Status Legend

- `DONE`: Implemented and verified in code/tests
- `PARTIAL`: Implemented, but incomplete for production reliability
- `MISSING`: Not implemented

## 1) Product and API Completeness

| Area | Status | Evidence | What is missing |
|---|---|---|---|
| Auth APIs (`register/login/logout/refresh`) | DONE | `gateway/api/v1/auth_routes.py` | Add MFA and password policy if required by business |
| Document upload API | DONE | `gateway/api/v1/document_routes.py`, `services/document_service/document_service.py` | Add malware scanning if required |
| Multi-format ingestion parser | DONE | `services/ingestion_service/parser_service.py` | OCR runtime binary (`tesseract`) must be installed in deployment image |
| QA API | DONE | `gateway/api/v1/qa_routes.py`, `services/qa_service/qa_pipeline.py`, `services/qa_service/retriever_service.py`, `services/extraction_service/vector_service.py` | Optional enhancements: long-term conversation memory store, ranking explainability analytics |
| Notification preferences API | DONE | `gateway/api/v1/notification_routes.py`, `services/notification_service/preference_repository.py` | Add stricter payload validation (if business requires) |
| Risk agent | DONE | `services/risk_service/risk_detector.py`, `gateway/api/v1/risk_routes.py`, `services/ingestion_service/ingestion_pipeline.py` | Expand model with LLM-assisted risk reasoning (optional) |
| Obligation agent E2E | PARTIAL | `services/obligation_service/*`, `workers/tasks/reminder_dispatcher.py` | End-to-end production workflow verification and API exposure |
| Real notification delivery providers | DONE | `services/notification_service/providers/*.py`, `services/notification_service/notification_service.py`, `services/notification_service/notification_repository.py` | Configure vendor credentials per environment |

## 2) Security Baseline

| Control | Status | Evidence | Notes |
|---|---|---|---|
| Password hashing (Argon2) | DONE | `services/auth_service/auth_service.py` | Legacy bcrypt compatibility retained |
| JWT + refresh token lifecycle | DONE | `services/auth_service/auth_service.py` | Add key rotation strategy for production |
| QA document ownership authorization | DONE | `gateway/api/v1/qa_routes.py` | Prevents cross-tenant QA access |
| Rate limiting for auth endpoints | DONE | `gateway/api/v1/auth_routes.py`, `gateway/dependencies/rate_limit.py` | Tune limits with traffic data |
| Upload validation (type/ext/size) | DONE | `services/document_service/document_service.py` | Consider AV scanning for higher assurance |
| Secret hardening checks for non-dev | DONE | `shared/config/settings.py` validator | Enforced in `staging/production` |
| Audit logging | PARTIAL | ad-hoc `print(...)` only | Use structured security/audit logs |
| Dependency and container security scanning | MISSING | n/a | Add Trivy/Snyk/GHAS or equivalent in CI |

## 3) Reliability and Operations

| Area | Status | Evidence | What is missing |
|---|---|---|---|
| Background processing with Celery/Redis | DONE | `workers/celery_app.py`, `workers/tasks/*` | Expand queue topology for all workloads |
| Database migrations | DONE | `migrations/`, `alembic.ini` | Add migration rollback playbook |
| Caching layer | DONE | `shared/cache/cache_service.py` | Add cache invalidation on document updates |
| Health/readiness endpoints | MISSING | n/a | Add `/healthz` and `/readyz` |
| Centralized logs/metrics/traces | MISSING | n/a | Add OpenTelemetry + metrics + dashboards |
| Alerting and on-call runbooks | MISSING | n/a | Define SLOs, alerts, escalation runbooks |
| Backup/restore drills | MISSING | n/a | Verify RPO/RTO with tested restores |

## 4) Testing and Quality Gates

| Gate | Status | Evidence | Notes |
|---|---|---|---|
| Unit/integration test suite | PARTIAL | Local run: 48 passed, 1 failed | `tests/test_llm_obligation_validator.py` fails without external LLM connectivity |
| Deterministic CI for tests | PARTIAL | Tests exist | Move external-LLM test behind integration marker and mock in default CI |
| Load/performance testing | MISSING | n/a | Required before production release |
| Chaos/failure testing | MISSING | n/a | Required for worker/retry confidence |

## 5) Deployment and Infrastructure

| Area | Status | Evidence | What is missing |
|---|---|---|---|
| Dockerized local runtime | DONE | `Docker-compose.yml` | Production deployment spec still needed |
| Local exposure hardening | DONE | `Docker-compose.yml` localhost binds | Good for dev; define production network policy separately |
| Production IaC (K8s/Terraform/etc.) | MISSING | n/a | Create repeatable production stack |
| TLS termination and cert lifecycle | MISSING | n/a | Required for internet-facing deployment |
| Secret manager integration | MISSING | n/a | Replace plaintext env-based secret handling |

## 6) Mobile Build Go/No-Go Gate

Use this before starting React Native iOS/Android build:

| Gate | Required | Current |
|---|---|---|
| Stable Auth + token refresh | Yes | PASS |
| Stable Document upload flow | Yes | PASS |
| Stable QA API contract for app UX | Yes | PASS (supports reasoning mode, confidence, persistent citations, multi-document scope, thread context) |
| Notifications preferences API complete | Yes | PASS |
| Risk agent output available to app | Yes | PASS |
| Production observability + error diagnostics | Yes | FAIL |

Mobile phase recommendation: **Start UI prototyping now**, but **do not start production mobile integration** until failed gates are resolved.

## 7) Priority Execution Plan (to reach Go)

1. Add health/readiness endpoints, structured logging, metrics, and alerts.
2. Split external-LLM tests into `integration` marker; keep CI deterministic.
3. Define production deployment stack (TLS, secrets manager, backups, runbooks).

## 8) Supported Document Types (Current)

Implemented parsing support:

- PDF: `.pdf`
- Plain text: `.txt`, `.md`
- Word: `.docx`
- Spreadsheet: `.csv`, `.xlsx`, `.xls`
- Images (OCR): `.jpg`, `.jpeg`, `.png`
- Email: `.eml`, `.msg`
- Web docs: `.html`, `.htm`

Upload allow-list is enforced via:

- `shared/config/settings.py` (`ALLOWED_UPLOAD_CONTENT_TYPES`, `ALLOWED_UPLOAD_EXTENSIONS`)
- `services/document_service/document_service.py` (`_validate_upload`)

## 9) QA API Current Scope (Implemented)

Implemented now:

- Document ownership authorization before QA retrieval
- Reasoning mode response (`include_reasoning`) with:
  - `query_type`, `confidence`, `confidence_band`, `missing_information`, `citations`
- Multi-query retrieval strategy with evidence scoring and aggregation
- Multi-document retrieval in one question (`document_ids`)
- Persistent citation identifiers (`chunk_id`, `chunk_index`, `document_id`)
- Optional thread context (`thread_id`) with Redis-backed short-term memory
- Redis caching for:
  - retrieval chunks
  - final QA response payload

Optional enhancements:

- Persist long conversation history in database (current: Redis short-term memory)
- Add ranking introspection dashboards for citation quality
