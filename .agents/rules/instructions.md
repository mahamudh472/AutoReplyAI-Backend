# AutoReplyAI Backend Project Instructions & Rules

These guidelines are the official workspace rules for Antigravity. Always read and adhere to these rules when working in the `autoreplyai_backend` codebase.

---

## 1. Project Overview & Tech Stack

AutoReplyAI Backend is a Django-based REST API designed for automated messaging integrations and account management.

- **Backend Framework:** Django 6.0.4+
- **API Framework:** Django REST Framework (DRF) 3.17.1+
- **Authentication:** JSON Web Tokens (JWT) via `django-rest-framework-simplejwt`
- **Type Checking:** Pyright (`pyrightconfig.json` is set to `basic` mode) and Mypy
- **Admin Panel:** Django Unfold (available config in `configs/unfold_conf.py`)
- **Database:** SQLite for development (`db.sqlite3` / `SQLITE_DB_NAME`), PostgreSQL support available for production via environment settings

---

## 2. Best Coding Principles (Mandatory)

Always design, write, and refactor code according to the following foundational engineering principles:

### A. SOLID Principles
- **Single Responsibility (SRP):** Each class, module, or function must have one, and only one, reason to change. Separate Django views (routing/request handling) from business logic (service functions).
- **Open/Closed (OCP):** Software entities should be open for extension, but closed for modification. Use subclassing, polymorphism, or configuration settings to extend behavior without mutating existing core functionality.
- **Liskov Substitution (LSP):** Subtypes must be substitutable for their base types without altering correctness.
- **Interface Segregation (ISP):** Prefer small, specific interfaces/classes over fat, multi-purpose ones.
- **Dependency Inversion (DIP):** Depend on abstractions rather than concrete implementations where appropriate.

### B. Clean & Maintainable Code
- **DRY (Don't Repeat Yourself):** Extract duplicated logic into reusable functions, helper utilities (in `common/` or app-specific `utils.py`), or base classes.
- **KISS (Keep It Simple, Stupid):** Write code that is simple to understand. Avoid premature optimization or over-engineering. Readable code is always preferred over clever code.
- **Self-Documenting Code:** Use descriptive variable names, clear function signatures, and write comments explaining *why* something is done rather than *what* is done.

### C. Security & Data Protection
- **Secrets Management:** NEVER hardcode credentials, tokens, or private keys. Load all secrets strictly from environment variables using `django-environ` or `os.getenv`.
- **SQL Injection Prevention:** Leverage the Django ORM query builder. Avoid raw SQL queries. If raw queries are unavoidable, always use parameterized query execution.
- **Input Validation & Sanitization:** Validate all incoming payloads within DRF serializers before passing them to the business logic layer.

### D. Query Performance & Efficiency
- **N+1 Query Prevention:** Always analyze database queries. Use `select_related()` for foreign key/one-to-one relationships and `prefetch_related()` for many-to-many/many-to-one relationships.

---

## 3. Directory Structure & Architecture

The codebase follows a structured, modular design:

```
autoreplyai_backend/
├── manage.py                   # Django management script
├── pyrightconfig.json          # Pyright type checker configuration
├── requirements.txt            # Python package dependencies
├── .env.example                # Example environment variables template
├── common/                     # Common utilities and global helpers
│   ├── enums.py                # Global Enum definitions
│   └── __init__.py
├── autoreplyai/                # Project configuration folder
│   ├── settings.py             # Main Django settings (auth configs, SMTP, apps list)
│   ├── urls.py                 # Core routing definitions (API v1 root, Admin URLs)
│   ├── configs/                # Configuration modules
│   │   └── unfold_conf.py      # Django Unfold Admin settings
│   └── __init__.py
├── apps/                       # Modular business domain applications
│   ├── accounts/               # Custom user management, registration, OTP validation, profiles
│   │   ├── models.py           # Custom User class (UUID primary key) & OTP database models
│   │   ├── views.py            # API controller endpoints (Register, Verify, Profile, etc.)
│   │   ├── serializers.py      # Request/Response validation schemas
│   │   ├── services/           # Business logic layer (e.g., handle_logout)
│   │   ├── utils.py            # Email notifications and random code generators
│   │   └── urls.py             # Endpoint routing paths
│   └── integrations/           # Third-party platform integrations (WhatsApp, Telegram, etc.)
└── docs/                       # Project documentation
    ├── ENDPOINT_LIST.md        # API Endpoint directory
    └── endpoints/              # Specific endpoint specifications
```

---

## 4. Coding Guidelines & Architecture Patterns

All contributions must follow these architectural practices:

### A. Separation of Concerns
1. **Views/Controllers:** Keeps controllers lightweight. Focus on request validation, calling service functions, and return formatting.
2. **Service Layer (`services/`):** All core business logic (e.g. database updates, third-party calls, state transitions) must reside in service functions inside `<app>/services/` instead of views or model files.
3. **Serializers:** Handled via DRF Serializers for validation and schema definitions. Keep them strictly focused on deserializing, serializing, and simple field-level validation.

### B. Type Annotations & Safety
- **Mandatory Types:** All new methods, functions, and helper functions must be fully type-annotated.
- **Null Safety:** Explicitly use `Optional[T]` from the `typing` module for nullable fields or return values.
- **Verification:** Run Pyright/Mypy checking after modifying or creating files to ensure there are no static analysis warnings.

### C. Custom Models & Database Migrations
- **Primary Keys:** New database models must use UUIDs or Auto-increment BigAutoFields as primary keys where appropriate (e.g., `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`).
- **Naming Conventions:** Class names must be `PascalCase` (e.g., `UserOTP`). Database tables should be explicitly defined in the model's `Meta` subclass using `db_table = '<name_plural>'` (e.g., `db_table = 'otps'`).
- **Migrations:** Always run `python manage.py makemigrations` and `python manage.py migrate` for model updates. Include generated migrations files in commits.

### D. Consistent API Design & Error Handling
- **Status Codes:** Use appropriate HTTP status codes from `rest_framework.status` (e.g. `200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`).
- **Response Format:** Return consistent JSON envelopes.
  - **Success:** `{"message": "Action completed successfully"}` or the resource data direct payload.
  - **Errors:** `{"error": "A detailed explanation of what went wrong"}`.
- **Documentation:** When introducing new API endpoints, update [docs/ENDPOINT_LIST.md](file:///home/mahmud/Projects/autoreplyai_backend/docs/ENDPOINT_LIST.md) and add a matching file under `docs/endpoints/`.

---

## 5. Local Commands & Verification Workflow

Always verify code correctness locally before concluding a task:

1. **Environment Setup:** Make sure environment variables are declared in `.env` (copying `.env.example`).
2. **Dependency Installation:** Run `pip install -r requirements.txt`.
3. **Database Setup:** Run migrations with `python manage.py migrate`.
4. **Running the Server:** Start local server using `python manage.py runserver`.
5. **Testing:** Run existing test suite using `python manage.py test`. Always add tests for new code in the `<app>/tests/` directory.
