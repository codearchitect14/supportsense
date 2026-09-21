# Deployment Guide

This guide covers deploying SupportSense to free-tier hosting: PostgreSQL and
Redis, the FastAPI backend, and the React frontend, plus continuous
integration, rollback, and monitoring.

## 1. Environment-specific configuration

The backend and frontend each read configuration from environment variables,
with `.env.example` documenting every variable. Keep a separate set of values
per environment rather than sharing one `.env` file across them:

| Environment | Backend `ENVIRONMENT` value | Notes |
|---|---|---|
| Development | `development` | Local Docker Compose Postgres and Redis; `/docs` and `/redoc` enabled. |
| Staging | `staging` | Hosted Postgres and Redis; mirrors production configuration for pre-release testing. |
| Production | `production` | `/docs`, `/redoc`, and `/openapi.json` are disabled; strict security headers and HSTS are enabled. |

Never commit a populated `.env` file. Store staging and production secrets in
the hosting provider's environment variable settings, or in GitHub Actions
repository secrets for values needed at deploy time.

## 2. Database and cache: PostgreSQL and Redis

Use a managed free tier rather than self-hosting for staging and production:

- **PostgreSQL**: Render's free PostgreSQL instance, Railway's free Postgres
  plan, or Supabase's free tier all work; the instance must support the
  `pgvector` extension (`CREATE EXTENSION IF NOT EXISTS vector;`), which Render
  and Supabase both allow.
- **Redis**: Render's free Redis instance, Railway's free Redis plan, or
  Upstash's free tier.

After provisioning, set `DATABASE_URL` and `REDIS_URL` on the backend service
to the provided connection strings, then apply migrations against the hosted
database:

```bash
DATABASE_URL=<hosted connection string> alembic upgrade head
```

Load both datasets against the hosted database following `data/README.md`
before the first deploy.

## 3. Backend: Render or Railway

The backend ships as a multi-stage, non-root Docker image at
`backend/Dockerfile`. Build it locally to verify it first:

```bash
docker build -f backend/Dockerfile -t supportsense-backend backend
docker run --rm -p 8000:8000 --env-file backend/.env supportsense-backend
```

**Render**

1. Create a new Web Service from the repository, with the root directory set
   to `backend` and the Dockerfile path set to `backend/Dockerfile`.
2. Set the environment variables from `backend/.env.example`, using the hosted
   `DATABASE_URL` and `REDIS_URL` from step 2 and `ENVIRONMENT=production`.
3. Set the health check path to `/health`.
4. Create a deploy hook under the service's settings and store its URL as the
   `RENDER_DEPLOY_HOOK_URL` GitHub Actions secret, so the CI workflow can
   trigger a deploy on merge to `main`.

**Railway**

1. Create a new service from the repository, pointing at `backend/Dockerfile`.
2. Set the same environment variables as above.
3. Expose the service on port 8000 and set the health check path to `/health`.
4. Create a deploy webhook and store it as `RENDER_DEPLOY_HOOK_URL` (the CI
   workflow's deploy step name is provider-agnostic; only the secret name is
   fixed) or adjust the workflow's secret name to match.

## 4. Frontend: Vercel or Netlify

The frontend is a static Vite build. Set `VITE_API_BASE_URL` to the deployed
backend's public URL before building.

**Vercel**

1. Import the repository, set the root directory to `frontend`.
2. Build command: `npm run build`. Output directory: `dist`.
3. Set `VITE_API_BASE_URL` as a project environment variable.
4. Create a deploy hook under project settings and store its URL as the
   `VERCEL_DEPLOY_HOOK_URL` GitHub Actions secret.

**Netlify**

1. Import the repository, set the base directory to `frontend`.
2. Build command: `npm run build`. Publish directory: `frontend/dist`.
3. Set `VITE_API_BASE_URL` as a site environment variable.
4. Create a build hook and store its URL as `VERCEL_DEPLOY_HOOK_URL` (or adjust
   the workflow's secret name to match).

Update the backend's `CORS_ALLOWED_ORIGINS` to include the deployed frontend
URL once it is known.

## 5. Continuous integration and deployment

`.github/workflows/ci.yml` runs on every pull request against `main` and on
every push to `main`:

- **backend job**: installs dependencies, runs `ruff` and `black --check`,
  runs `pip-audit` for dependency vulnerabilities, applies database migrations
  against an ephemeral PostgreSQL and Redis service, loads the knowledge base
  dataset, and runs the pytest suite.
- **frontend job**: installs dependencies, runs the linter, runs `npm audit`,
  type-checks and builds the app, and runs the component test suite.
- **deploy job**: runs only on a push to `main`, after both jobs pass. It
  triggers the Render/Railway and Vercel/Netlify deploy hooks configured in
  step 3 and step 4 above, if the corresponding repository secrets are set. If
  no deploy hooks are configured, the job logs that fact and exits
  successfully, so the workflow remains usable before hosting is provisioned.

## 6. Rollback

- **Backend**: both Render and Railway keep a history of previous deploys.
  From the service's deploy history, select the last known-good deploy and
  redeploy it. If a database migration must also be rolled back, identify the
  prior revision with `alembic history` and run
  `alembic downgrade <revision>` against the hosted database before
  redeploying the older backend image, since an older backend is not
  guaranteed to work against a newer schema.
- **Frontend**: both Vercel and Netlify keep every deploy and support
  instantly promoting a previous deploy to production from their dashboard,
  with no rebuild required.
- **General**: prefer rolling back the frontend and backend together when a
  release spans both, since API request and response shapes may have changed
  together.

## 7. Monitoring

- **Uptime**: point a free uptime monitor (for example, UptimeRobot or a
  provider's built-in health check) at the backend's `/health` endpoint on a
  short interval, and at the frontend's root URL.
- **Error logging**: the backend logs structured JSON log lines through the
  standard library logging configuration in `app/core/logging.py`; the hosting
  provider's log viewer (Render logs, Railway logs) is sufficient to search
  and tail these without additional setup. For centralized error tracking
  beyond provider logs, a free tier of an error tracking service (for example
  Sentry) can be wired in by installing its SDK and initializing it in
  `app/main.py`'s `create_app`, guarded by an optional `SENTRY_DSN` setting so
  it stays inactive when unset.
- **Rate limiting and audit events**: authentication events, role changes, and
  analytics access are already written to the `audit_log` table (see
  `app/services/audit_service.py`); query it directly for a security-relevant
  activity trail without additional tooling.

## 8. HTTPS

The backend sets the `Strict-Transport-Security` header when
`ENVIRONMENT=production`, but does not perform HTTP to HTTPS redirection
itself. Render, Railway, Vercel, and Netlify all terminate TLS and redirect
HTTP to HTTPS automatically at their edge for the domains and subdomains they
issue, so no additional redirect logic is required when deploying to any of
them. If the backend is ever deployed behind infrastructure that does not
redirect automatically, add that redirect at the reverse proxy or load
balancer in front of it rather than in the application.
