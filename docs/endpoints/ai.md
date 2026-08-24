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
