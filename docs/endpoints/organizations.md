# Organizations Endpoints

Back to index: [ENDPOINT_LIST.md](../ENDPOINT_LIST.md)

## Endpoint Inventory

- GET `/api/v1/organizations/` — List all user organizations (for dropdown switcher)
- POST `/api/v1/organizations/` — Create a new organization
- GET `/api/v1/organizations/{id}/` — Retrieve organization details
- PATCH `/api/v1/organizations/{id}/` — Update organization settings
- POST `/api/v1/organizations/{id}/logo/` — Upload / change organization logo
- DELETE `/api/v1/organizations/{id}/logo/` — Remove organization logo
- DELETE `/api/v1/organizations/{id}/` — Permanently delete organization
- GET `/api/v1/organizations/{id}/subscription/` — Get subscription plan & usage summary
- GET `/api/v1/organizations/current/` — Get primary organization details
- GET `/api/v1/organizations/{org_id}/members/` — List organization members
- POST `/api/v1/organizations/{org_id}/members/` — Add organization member

---

## 1. GET /api/v1/organizations/

Description: List all organizations belonging to the authenticated user (for the organization switcher dropdown).

Auth: Required (Bearer access token)

Success response (200 OK):

```json
[
  {
    "id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
    "name": "ABC Store",
    "slug": "abc-store",
    "logo_url": "http://localhost:8000/media/organization_logos/2026/08/logo.png",
    "role": "owner"
  },
  {
    "id": "2c5d9e1f-8a4b-7c3d-1234-567890abcdef",
    "name": "XYZ Agency",
    "slug": "xyz-agency",
    "logo_url": null,
    "role": "member"
  }
]
```

---

## 2. POST /api/v1/organizations/

Description: Create a new organization.

Auth: Required (Bearer access token)

Request JSON:

```json
{
  "name": "ABC Store",
  "slug": "abc-store",
  "default_language": "English",
  "timezone": "GMT+06:00",
  "description": "We sell high-quality products."
}
```

Success response (201 Created): Returns the created organization details.

---

## 3. GET /api/v1/organizations/{id}/

Description: Retrieve details of a specific organization.

Auth: Required (Bearer access token)

Success response (200 OK):

```json
{
  "id": "e4b3c2a1-0987-6543-21fe-dcba09876543",
  "name": "ABC Store",
  "slug": "abc-store",
  "logo_url": "http://localhost:8000/media/organization_logos/2026/08/logo.png",
  "default_language": "English",
  "timezone": "GMT+06:00",
  "description": "We sell high-quality products and provide excellent customer support.",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-08-30T14:20:00Z",
  "role": "owner"
}
```

---

## 4. PATCH /api/v1/organizations/{id}/

Description: Update organization settings.

Auth: Required (Bearer access token)

Request JSON:

```json
{
  "name": "ABC Store",
  "slug": "abc-store",
  "default_language": "English",
  "timezone": "GMT+06:00",
  "description": "We sell high-quality products and provide excellent customer support."
}
```

Success response (200 OK): Returns the updated organization object with `updated_at`.

---

## 5. POST /api/v1/organizations/{id}/logo/

Description: Upload or change organization logo image (JPG, PNG, SVG ≤ 2MB).

Auth: Required (Bearer access token)

Content-Type: `multipart/form-data`

Form Fields:
- `logo`: Binary image file (image/png, image/jpeg, image/svg+xml, image/webp)

Success response (200 OK):

```json
{
  "success": true,
  "logo_url": "http://localhost:8000/media/organization_logos/2026/08/logo.png"
}
```

---

## 6. DELETE /api/v1/organizations/{id}/logo/

Description: Remove organization logo.

Auth: Required (Bearer access token)

Success response (200 OK):

```json
{
  "success": true,
  "message": "Logo removed successfully",
  "logo_url": null
}
```

---

## 7. GET /api/v1/organizations/{id}/subscription/

Description: Get current subscription plan & usage summary (for sidebar plan card).

Auth: Required (Bearer access token)

Success response (200 OK):

```json
{
  "plan_name": "Starter Plan",
  "status": "active",
  "billing_cycle": "monthly",
  "features": {
    "max_messages": 10000,
    "used_messages": 450,
    "max_team_members": 1,
    "used_team_members": 1,
    "max_connected_accounts": 1,
    "used_connected_accounts": 1
  },
  "renews_at": "2026-09-15T00:00:00Z"
}
```

---

## 8. DELETE /api/v1/organizations/{id}/

Description: Permanently delete the organization (owner only).

Auth: Required (Bearer access token)

Success response (200 OK):

```json
{
  "success": true,
  "message": "Organization has been permanently deleted."
}
```
