# Organizations Endpoints

Back to index: [ENDPOINT_LIST.md](../ENDPOINT_LIST.md)

## Endpoint Inventory

- GET `/api/v1/organizations/`
- POST `/api/v1/organizations/`
- GET `/api/v1/organizations/current/`
- GET `/api/v1/organizations/<uuid:id>/`
- PATCH `/api/v1/organizations/<uuid:id>/`
- DELETE `/api/v1/organizations/<uuid:id>/`
- GET `/api/v1/organizations/<uuid:org_id>/members/`
- POST `/api/v1/organizations/<uuid:org_id>/members/`

---

## GET /api/v1/organizations/current/

Description: Get primary organization details for current authenticated user.

Auth: Required (Bearer access token)

Success response (200):

```json
{
  "id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
  "name": "Acme Corp's Organization",
  "owner": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "owner_email": "alice@example.com",
  "members_count": 1,
  "created_at": "2026-08-24T10:00:00Z",
  "updated_at": "2026-08-24T10:00:00Z"
}
```

---

## GET /api/v1/organizations/

Description: List organizations the authenticated user belongs to.

Auth: Required (Bearer access token)

Success response (200):

```json
[
  {
    "id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
    "name": "Acme Corp's Organization",
    "owner": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "owner_email": "alice@example.com",
    "members_count": 1,
    "created_at": "2026-08-24T10:00:00Z",
    "updated_at": "2026-08-24T10:00:00Z"
  }
]
```

---

## GET /api/v1/organizations/<uuid:org_id>/members/

Description: List members and their roles for a specific organization.

Auth: Required (Bearer access token)

Success response (200):

```json
[
  {
    "id": "f5c4b3a2-1098-7654-3210-fedcba987654",
    "organization": "e4b3c2a1-0987-6543-21fe-dcba09876543",
    "user": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_email": "alice@example.com",
    "user_full_name": "Alice Smith",
    "role": "OWNER",
    "created_at": "2026-08-24T10:00:00Z",
    "updated_at": "2026-08-24T10:00:00Z"
  }
]
```
