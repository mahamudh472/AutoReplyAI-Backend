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

---

Add other apps here as their endpoint pages are created under `docs/endpoints/`.
