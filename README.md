# Online Grocery Store v2

A full-stack grocery store with three roles — **shoppers**, **store managers** and an **admin** — built with **Flask** (REST API, JWT auth) and **Vue 3** (Vite, Vue Router, Bootstrap 5).

## Features

- Browse products, filter by category, search by name, price range, manufacture/expiry dates and stock
- Shopping cart and checkout with live inventory updates
- User dashboard with profile and order history
- Users can apply to become a store manager; the admin approves or rejects requests
- Managers and the admin can add, edit and delete products; the admin also manages categories
- Downloadable sales report (CSV)
- Response caching (Redis, or in-memory when Redis isn't configured)
- Optional background jobs with Celery + Redis: daily reminder e-mails and monthly spending reports

## Demo accounts

A fresh database is created and seeded with a demo catalog on first start.

| Role    | Login page        | Username / e-mail     | Password                                 |
|---------|-------------------|-----------------------|------------------------------------------|
| Shopper | `/login`          | `demo@grocery.app`    | `demo1234`                               |
| Manager | `/login`          | `manager@grocery.app` | `manager1234`                            |
| Admin   | `/admin/login`    | `admin`               | value of `ADMIN_PASSWORD` (default `password`) |

## Run locally

Requires Python 3.11+ and Node 20+.

```bash
# API (http://localhost:5000)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py

# Frontend dev server (http://localhost:8080), proxies /api to Flask
cd frontend
npm install
npm run dev
```

To try the production setup locally, run `npm run build` in `frontend/`, then open http://localhost:5000: Flask serves the built app itself.

Or with Docker:

```bash
docker build -t grocery-store .
docker run -p 8000:8000 \
  -e SECRET_KEY="$(openssl rand -hex 32)" \
  -e JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  -e ADMIN_PASSWORD=choose-a-strong-one \
  grocery-store
# open http://localhost:8000
```

The image runs with `APP_ENV=production`, so it refuses to start with missing or default secrets (keys must be at least 32 characters, admin password at least 8 and not `password`).

## Deploy

The app ships as one Docker image: the Vue app is built and served by Flask/Gunicorn, so there is one service and no CORS setup.

**Render (free tier):** push to GitHub, then in Render choose **New + → Blueprint** and select this repo. `render.yaml` generates the secret keys; set `ADMIN_PASSWORD` when prompted.

Any Docker host works the same way (Fly.io, Railway, Google Cloud Run, a VPS). The container listens on `$PORT` (default 8000). Health checks: `/api/health` (process up) and `/api/ready` (database reachable).

Production defaults: auth tokens expire after 12 hours, login and signup are rate-limited per IP, and responses carry a strict Content-Security-Policy and other security headers.

> On free tiers the disk is ephemeral, so the SQLite database resets to the demo data on each redeploy or restart. For a portfolio demo that's useful, because it keeps the demo clean. To keep data, mount a volume and point `DATABASE_PATH` at it.

### Configuration

The main settings are below; `.env.example` documents every variable (rate limits, token lifetime, proxy count, gunicorn tuning, CSP, logging).

| Variable          | Default                  | Purpose                                          |
|-------------------|--------------------------|--------------------------------------------------|
| `APP_ENV`         | `development`            | `production` enables the startup secrets check and HSTS |
| `SECRET_KEY`      | dev value                | Flask secret. **Set in production.**             |
| `JWT_SECRET_KEY`  | `SECRET_KEY`             | Signs auth tokens. **Set in production.**        |
| `ADMIN_USERNAME`  | `admin`                  | Admin login                                      |
| `ADMIN_PASSWORD`  | `password`               | Admin password. **Set in production.**           |
| `DATABASE_PATH`   | `./data/grocery.db`      | SQLite file, created and seeded if missing       |
| `REDIS_URL`       | unset (in-memory cache)  | Enables the Redis cache and the Celery broker    |
| `CORS_ORIGINS`    | unset                    | Comma-separated origins, only if the frontend is hosted separately |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SENDER_EMAIL` | `localhost:1025` (MailHog) | E-mail for background jobs |

### Background e-mail jobs (optional)

With Redis running and `REDIS_URL` set:

```bash
celery -A app:celery_app worker --loglevel INFO
celery -A app:celery_app beat --loglevel INFO
```

[MailHog](https://github.com/mailhog/MailHog) on `localhost:1025` is handy for capturing the e-mails locally.

## Project layout

```
app.py                 Flask app, Celery schedule, serves the built frontend
applications/          API routes, auth helpers, DB access, background tasks
frontend/              Vue 3 + Vite single-page app
Dockerfile, gunicorn.conf.py, render.yaml, .env.example
docs/                  Original project report
```
