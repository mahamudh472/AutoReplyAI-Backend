# AI Settings Endpoints

Back to index: [ENDPOINT_LIST.md](../ENDPOINT_LIST.md)

## Endpoint Inventory

- GET `/api/v1/ai/settings/`
- PATCH `/api/v1/ai/settings/`
- PUT `/api/v1/ai/settings/`

---

## GET /api/v1/ai/settings/

Description: Get the AI configuration and parameters for the user's primary organization (queries first organization). Automatically creates default settings if none exist yet.

Auth: Required (Bearer access token)

Success response (200):

```json
{
  "id": "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
  "organization_id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
  "organization_name": "Acme Corp's Organization",
  "is_enabled": true,
  "provider": "openai",
  "model_name": "gpt-4o-mini",
  "api_key": null,
  "system_prompt": "You are a helpful, polite, and professional customer support assistant for our business. Reply concisely, clearly, and accurately to customer inquiries.",
  "tone": "professional",
  "temperature": 0.7,
  "max_tokens": 500,
  "fallback_message": "Thank you for contacting us! A member of our team will review your message and get back to you shortly.",
  "auto_reply_delay_seconds": 0,
  "business_name": null,
  "business_description": null,
  "created_at": "2026-08-24T12:00:00Z",
  "updated_at": "2026-08-24T12:00:00Z"
}
```

---

## PATCH /api/v1/ai/settings/

Description: Update AI configuration parameters for the user's primary organization.

Auth: Required (Bearer access token)

Request JSON (example):

```json
{
  "is_enabled": true,
  "provider": "gemini",
  "model_name": "gemini-1.5-flash",
  "tone": "friendly",
  "temperature": 0.5,
  "max_tokens": 800,
  "business_name": "Acme Corp",
  "business_description": "Online store selling premium custom mechanical keyboards.",
  "system_prompt": "You are the friendly support assistant for Acme Corp. Help customers find keyboards and answer shipping questions."
}
```

Success response (200): Returns the updated AI settings object.

---

## GET /api/v1/ai/knowledge-base/

Description: List all Knowledge Base documents for the user's organization with filtering support.

Auth: Required (Bearer access token)

Query Parameters:
- `status`: Filter by document status (`pending`, `processing`, `indexed`, `failed`)
- `source_type`: Filter by source type (`file`, `text`, `faq`, `url`)
- `is_active`: Filter by boolean (`true`/`false`)
- `tag`: Filter by tag match
- `search`: Full text search across title, description, filename, and content

Success response (200):

```json
[
  {
    "id": "7a8b9c0d-1e2f-3456-7890-abcdef123456",
    "organization_id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
    "organization_name": "Acme Corp's Organization",
    "title": "Return Policy FAQ",
    "description": "FAQ regarding refunds and returns",
    "file": "/media/knowledge_base/2026/08/faq_policy.txt",
    "file_url": "http://localhost:8000/media/knowledge_base/2026/08/faq_policy.txt",
    "file_name": "faq_policy.txt",
    "file_type": "txt",
    "file_size": 1024,
    "source_type": "file",
    "raw_content": "Welcome to AutoReplyAI support. Our return policy is 30 days.",
    "status": "pending",
    "error_message": null,
    "character_count": 59,
    "word_count": 10,
    "chunk_count": 0,
    "tags": ["faq", "refunds"],
    "metadata": {
      "category": "policies",
      "version": "1.0"
    },
    "is_active": true,
    "created_by_email": "alice@example.com",
    "created_at": "2026-08-28T12:00:00Z",
    "updated_at": "2026-08-28T12:00:00Z",
    "indexed_at": null
  }
]
```

---

## POST /api/v1/ai/knowledge-base/upload/ (or /api/v1/ai/knowledge-base/)

Description: Upload a text-related file (`.txt`, `.md`, `.csv`, `.json`, etc.) or raw text content to be stored in the Knowledge Base and indexed later.

Auth: Required (Bearer access token)

Content-Type: `multipart/form-data` or `application/json`

Form Fields / JSON Payload:
- `file`: The document file to upload (optional if `raw_content` is provided)
- `title`: Title of the document (optional, defaults to filename)
- `description`: Summary of document content (optional)
- `raw_content`: Direct text input if not uploading a file (optional if `file` is uploaded)
- `source_type`: `file`, `text`, `faq`, or `url` (default: `file`)
- `tags`: List of string tags or JSON string (e.g. `["support", "refunds"]`)
- `metadata`: JSON object containing arbitrary metadata (e.g. `{"category": "shipping"}`)
- `is_active`: Boolean flag (default: `true`)

Success response (201): Returns the created `KnowledgeDocument` object with status `pending`.

---

## GET /api/v1/ai/knowledge-base/<uuid:id>/

Description: Retrieve details of a specific Knowledge Base document.

Auth: Required (Bearer access token)

Success response (200): Returns single `KnowledgeDocument` object.

---

## PATCH /api/v1/ai/knowledge-base/<uuid:id>/

Description: Update document metadata, title, tags, or active status.

Auth: Required (Bearer access token)

Success response (200): Returns updated `KnowledgeDocument` object.

---

## DELETE /api/v1/ai/knowledge-base/<uuid:id>/

Description: Delete a knowledge document and its associated file and chunks.

Auth: Required (Bearer access token)

Success response (204 No Content)

