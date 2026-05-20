# NexBoard API

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-6.0-green)
![DRF](https://img.shields.io/badge/DRF-3.x-red)
![Tests](https://img.shields.io/badge/Tests-43%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/Coverage-83%25-yellowgreen)

A production-ready, multi-tenant project & task management REST API built with Django and Django REST Framework — inspired by Linear and Jira.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 6 + Django REST Framework |
| Database | PostgreSQL |
| Cache | Redis (django-redis) |
| Task Queue | Celery + Redis broker |
| Auth | JWT (simplejwt) + OAuth2 (allauth) |
| Docs | drf-spectacular (OpenAPI 3.0 / Swagger) |
| Testing | pytest + pytest-django (43 tests, 83% coverage) |
| DevOps | Docker, docker-compose, GitHub Actions CI |

---

## Features

- **Multi-tenant workspaces** — users can create and belong to multiple workspaces
- **Role-based access control** — four roles per workspace: Owner, Admin, Member, Guest
- **Project management** — public/private visibility, workspace-scoped access
- **Rich task model** — priority, status, assignee, labels, subtasks, due dates
- **Activity log** — every task change is automatically recorded
- **Comments** — threaded comments on tasks
- **Async notifications** — email + in-app via Celery (non-blocking)
- **Analytics** — workspace stats cached in Redis (5 min TTL)
- **Rate limiting** — 500/hr authenticated, 10/min on auth endpoints
- **Pagination, filtering, search, ordering** — on all list endpoints
- **Swagger UI** — interactive API docs at `/api/docs/`

---

## Architecture

```
nexboard/
├── apps/
│   ├── accounts/        # Custom user model, JWT auth, register/login/profile
│   ├── workspaces/      # Multi-tenant workspaces, RBAC, invite system
│   ├── projects/        # Projects with public/private visibility
│   ├── tasks/           # Tasks, subtasks, labels, comments, activity log
│   ├── notifications/   # In-app + async email notifications via Celery
│   └── analytics/       # Workspace analytics with Redis caching
├── common/              # Shared utilities — pagination, permissions, exceptions
├── config/
│   ├── settings/
│   │   ├── base.py      # Shared settings
│   │   ├── local.py     # Development overrides
│   │   └── production.py# Production overrides
│   ├── celery.py        # Celery app config
│   └── urls.py
├── tests/               # 43 tests, 83% coverage
├── docker-compose.yml
└── requirements.txt
```

---

## Quick Start (Docker)

```bash
git clone https://github.com/yourusername/nexboard.git
cd nexboard
cp .env.example .env    # fill in your values
docker-compose up --build
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/api/docs/`
- Admin panel: `http://localhost:8000/admin/`

---

## Local Development

**Requirements:** Python 3.12, PostgreSQL, Redis

```bash
# 1. Clone and set up environment
git clone https://github.com/yourusername/nexboard.git
cd nexboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your DB and Redis credentials

# 3. Run migrations
python manage.py migrate
python manage.py createsuperuser

# 4. Start the server
python manage.py runserver

# 5. Start Celery worker (separate terminal)
celery -A config worker --loglevel=info
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```ini
SECRET_KEY=your-secret-key-min-32-chars
DB_NAME=nexboard
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
DEFAULT_FROM_EMAIL=noreply@nexboard.dev

# Production only
ALLOWED_HOSTS=yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourfrontend.com
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-key
```

---

## API Reference

### Auth

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user, returns tokens | No |
| POST | `/api/auth/token/` | Login, returns JWT pair | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| POST | `/api/auth/logout/` | Blacklist refresh token | Yes |
| GET/PATCH | `/api/auth/profile/` | View or update profile | Yes |
| POST | `/api/auth/change-password/` | Change password | Yes |

### Workspaces

| Method | Endpoint | Description | Min Role |
|--------|----------|-------------|----------|
| GET | `/api/workspaces/` | List my workspaces | Member |
| POST | `/api/workspaces/` | Create workspace | — |
| GET | `/api/workspaces/<id>/` | Workspace detail | Member |
| PATCH | `/api/workspaces/<id>/` | Update workspace | Admin |
| DELETE | `/api/workspaces/<id>/` | Delete workspace | Owner |
| GET | `/api/workspaces/<id>/members/` | List members | Member |
| PUT | `/api/workspaces/<id>/members/<uid>/` | Change member role | Admin |
| DELETE | `/api/workspaces/<id>/members/<uid>/remove/` | Remove member | Admin |
| POST | `/api/workspaces/<id>/invite/` | Invite by email | Admin |
| GET | `/api/workspaces/<id>/analytics/` | Workspace analytics | Member |

### Projects

| Method | Endpoint | Description | Min Role |
|--------|----------|-------------|----------|
| GET | `/api/workspaces/<id>/projects/` | List projects | Member |
| POST | `/api/workspaces/<id>/projects/` | Create project | Admin |
| GET | `/api/workspaces/<id>/projects/<id>/` | Project detail | Member |
| PATCH | `/api/workspaces/<id>/projects/<id>/` | Update project | Admin |
| DELETE | `/api/workspaces/<id>/projects/<id>/` | Delete project | Admin |

### Tasks

| Method | Endpoint | Description | Min Role |
|--------|----------|-------------|----------|
| GET | `/api/workspaces/<wid>/projects/<pid>/tasks/` | List tasks | Member |
| POST | `/api/workspaces/<wid>/projects/<pid>/tasks/` | Create task | Member |
| GET | `/api/workspaces/<wid>/projects/<pid>/tasks/<id>/` | Task detail | Member |
| PATCH | `/api/workspaces/<wid>/projects/<pid>/tasks/<id>/` | Update task | Member |
| DELETE | `/api/workspaces/<wid>/projects/<pid>/tasks/<id>/` | Delete task | Creator/Admin |
| GET/POST | `/api/workspaces/<wid>/projects/<pid>/tasks/<id>/comments/` | Comments | Member |
| GET | `/api/workspaces/<wid>/projects/<pid>/tasks/<id>/activity/` | Activity log | Member |
| GET/POST | `/api/workspaces/<wid>/projects/<pid>/tasks/labels/` | Labels | Member |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | List notifications (paginated) |
| GET | `/api/notifications/unread-count/` | Unread count |
| POST | `/api/notifications/mark-all-read/` | Mark all as read |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=apps --cov-report=term-missing
```

**Results: 43 tests, 83% coverage**

Key scenarios covered:
- RBAC enforcement across all four roles
- Private project visibility (guests cannot see private projects)
- JWT token blacklisting on logout
- Activity log created on every task change
- Duplicate validation returns 400 not 500
- Non-members receive 404 not 403 (no information leakage)
- Subtask creation and nesting
- Comment creation and listing

---

## Design Decisions

**UUID primary keys** — avoids exposing record counts to clients (`/tasks/1/` leaks that you have at least 1 task). UUIDs are also safe to generate client-side without a DB round-trip.

**Custom exception handler** — all errors return a consistent shape regardless of error type:
```json
{
  "status": "error",
  "code": 400,
  "errors": { "field": ["message"] },
  "message": "Human readable summary"
}
```

**JWT over session auth** — stateless, no session table to maintain, horizontally scalable. Access tokens expire in 60 minutes; refresh tokens in 7 days with rotation and blacklisting on logout.

**Celery for email** — SMTP can block for 1-3 seconds. Without Celery the API hangs until the mail server responds. With Celery, the task is queued instantly and the API returns in under 50ms. Workers retry up to 3 times with 60s delays on failure.

**Redis cache with Authorization header vary** — the analytics endpoint is expensive (multiple aggregation queries). It's cached for 5 minutes per user. Varying on `Authorization` ensures user A never receives user B's cached data.

**Constraint enforcement at two layers** — uniqueness is enforced both at the DB level (`unique_together`) and at the serializer level (`validate_*`). The DB constraint is the safety net; the serializer constraint ensures clients get a clean 400 JSON response instead of a 500.

**Non-members get 404 not 403** — returning 403 on a workspace a user doesn't belong to confirms the workspace exists. 404 leaks nothing.

---

## CI/CD

GitHub Actions runs on every push to `main` and `develop`:
- Spins up PostgreSQL and Redis service containers
- Runs `python manage.py check`
- Runs all migrations
- Extend with `pytest tests/` for full test runs on each push
