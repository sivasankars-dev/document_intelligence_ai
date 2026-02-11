# Data Model

## Users
- id
- email
- password_hash
- created_at

---

## Documents
- id
- user_id
- file_name
- file_url
- document_type
- uploaded_at

---

## Document Versions
- id
- document_id
- version
- created_at

---

## Extracted Facts
- id
- document_id
- key
- value
- confidence_score

---

## Risks
- id
- document_id
- description
- severity
- detected_at

---

## Obligations
- id
- document_id
- title
- due_date
- reminder_status
