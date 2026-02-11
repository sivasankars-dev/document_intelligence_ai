# Data Model

## Users
table_name: users
- id(UUID)
- email
- password_hash
- is_active
- created_at
- updated_at

---

## Documents
table_name: documents
- id(UUID)
- user_id
- file_name
- file_type
- storage_path
- document_status
- uploaded_at

---

## Document Versions
table_name: document_versions
- id
- document_id
- version_number
- created_at

---

## Extracted Facts
table_name: extracted_facts
- id
- document_id
- key
- value
- confidence_score
- created_at

---

## Risks
table_name: risks
- id
- document_id
- description
- severity
- created_at

---

## Obligations
table_name: obligations
- id
- document_id
- title
- due_date
- status
- created_at
