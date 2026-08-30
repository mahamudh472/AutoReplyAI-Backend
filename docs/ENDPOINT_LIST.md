# API Endpoints Index

This index lists available API endpoints and links to the per-app reference pages under `docs/endpoints/`.

### Accounts

- [POST /api/v1/accounts/register/](endpoints/accounts.md) — Register a new user (sends OTP email)
- [POST /api/v1/accounts/verify-email/](endpoints/accounts.md) — Verify email with OTP
- [POST /api/v1/accounts/login/](endpoints/accounts.md) — Obtain JWT access and refresh tokens
- [POST /api/v1/accounts/token/refresh/](endpoints/accounts.md) — Refresh JWT access token
- [POST /api/v1/accounts/logout/](endpoints/accounts.md) — Logout / revoke session (authenticated)
- [POST /api/v1/accounts/password-reset/](endpoints/accounts.md) — Send OTP to reset password
- [POST /api/v1/accounts/check-otp/](endpoints/accounts.md) — Validate an OTP
- [POST /api/v1/accounts/password-reset-confirm/](endpoints/accounts.md) — Confirm password reset with OTP
- [POST /api/v1/accounts/change-password/](endpoints/accounts.md) — Change password (authenticated)
- [GET  /api/v1/accounts/profile/](endpoints/accounts.md) — Get current user's profile (authenticated)
- [PATCH /api/v1/accounts/profile/update/](endpoints/accounts.md) — Partial update profile (authenticated)

### Integrations

- [GET /api/v1/integrations/](endpoints/integrations.md) — List all user integration connections (authenticated)
- [POST /api/v1/integrations/](endpoints/integrations.md) — Connect a Facebook Page, Instagram, or WhatsApp Business account (authenticated)
- [GET /api/v1/integrations/<uuid:id>/](endpoints/integrations.md) — Get details of a specific integration connection (authenticated)
- [PATCH /api/v1/integrations/<uuid:id>/](endpoints/integrations.md) — Update an integration connection (authenticated)
- [DELETE /api/v1/integrations/<uuid:id>/](endpoints/integrations.md) — Delete an integration connection (authenticated)
- [POST /api/v1/integrations/<uuid:id>/send-message/](endpoints/integrations.md) — Send a message on behalf of the integration (authenticated)
- [GET /api/v1/integrations/logs/](endpoints/integrations.md) — View message dispatch history logs (authenticated)
- [GET /api/v1/integrations/meta/connect/](endpoints/integrations.md) — Generate Meta OAuth URL (authenticated)
- [GET /api/v1/integrations/meta/callback/](endpoints/integrations.md) — Meta OAuth callback handler (public)
- [GET /api/v1/integrations/meta/pages/](endpoints/integrations.md) — Fetch user managed Facebook Pages (authenticated)
- [POST /api/v1/integrations/meta/select-page/](endpoints/integrations.md) — Select and connect a Facebook Page integration (authenticated)
- [GET /api/v1/integrations/meta/webhook/](endpoints/integrations.md) — Meta Webhook challenge verification (public)
- [POST /api/v1/integrations/meta/webhook/](endpoints/integrations.md) — Meta Webhook event receiver & auto-responder (public)

### Organizations

- [GET /api/v1/organizations/](endpoints/organizations.md) — List organizations the user belongs to (authenticated)
- [POST /api/v1/organizations/](endpoints/organizations.md) — Create a new organization (authenticated)
- [GET /api/v1/organizations/current/](endpoints/organizations.md) — Get user's primary active organization (authenticated)
- [GET /api/v1/organizations/<uuid:id>/](endpoints/organizations.md) — Get organization details (authenticated)
- [PATCH /api/v1/organizations/<uuid:id>/](endpoints/organizations.md) — Update organization (authenticated)
- [POST /api/v1/organizations/<uuid:id>/logo/](endpoints/organizations.md) — Upload / update organization logo (authenticated)
- [DELETE /api/v1/organizations/<uuid:id>/logo/](endpoints/organizations.md) — Remove organization logo (authenticated)
- [GET /api/v1/organizations/<uuid:id>/subscription/](endpoints/organizations.md) — Get organization subscription plan & usage quotas (authenticated)
- [DELETE /api/v1/organizations/<uuid:id>/](endpoints/organizations.md) — Permanently delete organization (authenticated)
- [GET /api/v1/organizations/<uuid:org_id>/members/](endpoints/organizations.md) — List organization members (authenticated)
- [POST /api/v1/organizations/<uuid:org_id>/members/](endpoints/organizations.md) — Add organization member (authenticated)

### AI & Knowledge Base

- [GET /api/v1/ai/settings/](endpoints/ai.md) — Get AI configuration for the user's primary organization (authenticated)
- [PATCH /api/v1/ai/settings/](endpoints/ai.md) — Update AI configuration for the user's primary organization (authenticated)
- [PUT /api/v1/ai/settings/](endpoints/ai.md) — Replace AI configuration for the user's primary organization (authenticated)
- [GET /api/v1/ai/knowledge-base/](endpoints/ai.md) — List Knowledge Base documents with filter options (authenticated)
- [POST /api/v1/ai/knowledge-base/upload/](endpoints/ai.md) — Upload text-related files or raw text for future indexing (authenticated)
- [GET /api/v1/ai/knowledge-base/<uuid:id>/](endpoints/ai.md) — Get Knowledge Base document details (authenticated)
- [PATCH /api/v1/ai/knowledge-base/<uuid:id>/](endpoints/ai.md) — Update Knowledge Base document (authenticated)
- [DELETE /api/v1/ai/knowledge-base/<uuid:id>/](endpoints/ai.md) — Delete Knowledge Base document (authenticated)

---

Add other apps here as their endpoint pages are created under `docs/endpoints/`.
