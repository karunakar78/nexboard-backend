# NexBoard API

A multi-tenant project & task management REST API built with Django and Django REST Framework.

## Tech Stack

- **Django 6** + **Django REST Framework**
- **PostgreSQL** — primary database
- **Redis** — caching + Celery broker
- **Celery** — async email notifications
- **JWT** — stateless authentication (simplejwt)
- **drf-spectacular** — auto-generated OpenAPI 3.0 docs
- **Docker** + **docker-compose**
- **GitHub Actions** — CI pipeline

## Features

- Multi-tenant workspaces with role-based access (Owner / Admin / Member / Guest)
- Project management with public/private visibility
- Tasks with priority, status, assignee, labels, subtasks, comments
- Auto-generated activity log on every task change
- Async email notifications via Celery + Redis
- Redis caching on analytics endpoints (5 min TTL)
- Rate limiting (500/hr authenticated, 10/min on auth endpoints)
- Pagination, filtering, search, and ordering on all list endpoints
- Swagger UI at `/api/docs/`

## Quick Start (Docker)

```bash
git clone https://github.com/yourusername/nexboard.git
cd nexboard
cp .env.example .env   # fill in your values
docker-compose up --build
```

API available at `http://localhost:8000`
Swagger docs at `http://localhost:8000/api/docs/`

## Local Development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In a separate terminal
celery -A config worker --loglevel=info
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/token/` | Login (get JWT) |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| GET/PATCH | `/api/auth/profile/` | View/update profile |
| GET/POST | `/api/workspaces/` | List/create workspaces |
| POST | `/api/workspaces/<id>/invite/` | Invite member |
| GET/POST | `/api/workspaces/<id>/projects/` | List/create projects |
| GET/POST | `/api/workspaces/<id>/projects/<id>/tasks/` | List/create tasks |
| GET/POST | `/api/workspaces/<id>/projects/<id>/tasks/<id>/comments/` | Comments |
| GET | `/api/workspaces/<id>/analytics/` | Workspace analytics |
| GET | `/api/notifications/` | In-app notifications |

Full documentation: `/api/docs/`

## Environment Variables

See `.env.example` for all required variables.
