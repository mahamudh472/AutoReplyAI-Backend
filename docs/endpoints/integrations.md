# Integrations Endpoints

Back to index: [ENDPOINT_LIST.md](../ENDPOINT_LIST.md)

## Endpoint Inventory

- GET `/api/v1/integrations/`
- POST `/api/v1/integrations/`
- GET `/api/v1/integrations/<uuid:id>/`
- PATCH `/api/v1/integrations/<uuid:id>/`
- DELETE `/api/v1/integrations/<uuid:id>/`
- POST `/api/v1/integrations/<uuid:id>/send-message/`
- GET `/api/v1/integrations/logs/`

---

## GET /api/v1/integrations/

Description: Get all connected integrations for the current authenticated user.

Auth: Required (Bearer access token)

Success response (200):

```json
[
  {
    "id": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
    "platform": "FACEBOOK_PAGE",
    "name": "My Business Page",
    "platform_identifier": "104928374829103",
    "additional_data": {},
    "is_active": true,
    "created_at": "2026-07-14T09:45:00Z",
    "updated_at": "2026-07-14T09:45:00Z"
  }
]
```

---

## POST /api/v1/integrations/

Description: Connect a new integration channel (Facebook Page, Instagram, or WhatsApp Business).

Auth: Required (Bearer access token)

Request JSON:

```json
{
  "platform": "FACEBOOK_PAGE",
  "name": "My Facebook Page",
  "access_token": "EAAG...",
  "platform_identifier": "104928374829103",
  "additional_data": {
    "category": "Retail"
  }
}
```

*Note: Supported platform choices are `FACEBOOK_PAGE`, `INSTAGRAM`, and `WHATSAPP_BUSINESS`.*

Success response (201):

```json
{
  "id": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
  "platform": "FACEBOOK_PAGE",
  "name": "My Facebook Page",
  "platform_identifier": "104928374829103",
  "additional_data": {
    "category": "Retail"
  },
  "is_active": true,
  "created_at": "2026-07-14T10:00:00Z",
  "updated_at": "2026-07-14T10:00:00Z"
}
```

---

## GET /api/v1/integrations/<uuid:id>/

Description: Fetch details of a specific connected integration channel.

Auth: Required (Bearer access token)

Success response (200):

```json
{
  "id": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
  "platform": "FACEBOOK_PAGE",
  "name": "My Facebook Page",
  "platform_identifier": "104928374829103",
  "additional_data": {
    "category": "Retail"
  },
  "is_active": true,
  "created_at": "2026-07-14T10:00:00Z",
  "updated_at": "2026-07-14T10:00:00Z"
}
```

---

## PATCH /api/v1/integrations/<uuid:id>/

Description: Update an integration channel connection.

Auth: Required (Bearer access token)

Request JSON (example):

```json
{
  "name": "Updated Page Name",
  "is_active": false
}
```

Success response (200):

```json
{
  "id": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
  "platform": "FACEBOOK_PAGE",
  "name": "Updated Page Name",
  "platform_identifier": "104928374829103",
  "additional_data": {
    "category": "Retail"
  },
  "is_active": false,
  "created_at": "2026-07-14T10:00:00Z",
  "updated_at": "2026-07-14T10:05:00Z"
}
```

---

## DELETE /api/v1/integrations/<uuid:id>/

Description: Remove an integration channel connection.

Auth: Required (Bearer access token)

Success response (244 No Content) or standard REST Framework delete response (204).

---

## POST /api/v1/integrations/<uuid:id>/send-message/

Description: Send an outgoing message to a recipient on behalf of the integration channel.

Auth: Required (Bearer access token)

Request JSON:

```json
{
  "recipient_id": "user_psid_or_phone_number",
  "message_content": "Hello, thank you for contacting us!"
}
```

Success response (200):

```json
{
  "message": "Message sent successfully.",
  "platform_message_id": "mid.14567890",
  "response": {
    "recipient_id": "user_psid_or_phone_number",
    "message_id": "mid.14567890"
  }
}
```

Error response (400):

```json
{
  "error": "Failed to send message.",
  "detail": "Invalid OAuth access token."
}
```

---

## GET /api/v1/integrations/logs/

Description: List history of all sent messages and their status logs.

Auth: Required (Bearer access token)

Success response (200):

```json
[
  {
    "id": "678e9f01-2345-6789-0123-456789abcdef",
    "integration": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
    "platform": "FACEBOOK_PAGE",
    "integration_name": "My Facebook Page",
    "recipient_id": "user_psid_or_phone_number",
    "message_content": "Hello, thank you for contacting us!",
    "platform_message_id": "mid.14567890",
    "status": "sent",
    "error_message": null,
    "created_at": "2026-07-14T10:10:00Z"
  }
]
```

---

## GET /api/v1/integrations/meta/webhook/

Description: Meta Webhook verification handshake endpoint. Meta sends `hub.mode`, `hub.verify_token`, and `hub.challenge` query parameters when subscribing.

Auth: None (Public / Meta Verified)

Query Parameters:
- `hub.mode`: `subscribe`
- `hub.verify_token`: Verification token matching `META_WEBHOOK_VERIFY_TOKEN` setting
- `hub.challenge`: Random challenge string sent by Meta

Success response (200): Plain text containing the `hub.challenge` string.

Error response (403): Plain text error if `hub.verify_token` or `hub.mode` does not match.

---

## POST /api/v1/integrations/meta/webhook/

Description: Receives webhook event notifications from Meta (Facebook Messenger, Instagram Messaging, WhatsApp Business), processes incoming user messages, and sends a static automated reply.

Auth: None (Public / Meta Signature validation via `X-Hub-Signature-256`)

Payload (Example Facebook Page Event):

```json
{
  "object": "page",
  "entry": [
    {
      "id": "104928374829103",
      "time": 1458692752478,
      "messaging": [
        {
          "sender": {
            "id": "1254459154682919"
          },
          "recipient": {
            "id": "104928374829103"
          },
          "timestamp": 1458692752478,
          "message": {
            "mid": "mid.1458696618141:b4ef9d19ec21086067",
            "text": "Hello, is anyone available?"
          }
        }
      ]
    }
  ]
}
```

Success response (200):

```json
{
  "status": "EVENT_RECEIVED",
  "processed": [
    {
      "status": "replied",
      "integration_id": "a3b4c5d6-e7f8-9012-3456-7890abcdef12",
      "platform": "FACEBOOK_PAGE",
      "sender_id": "1254459154682919",
      "incoming_message_id": "mid.1458696618141:b4ef9d19ec21086067",
      "incoming_text": "Hello, is anyone available?",
      "outgoing_message_id": "mid.1458696618141:xyz987654",
      "error": null
    }
  ]
}
```

