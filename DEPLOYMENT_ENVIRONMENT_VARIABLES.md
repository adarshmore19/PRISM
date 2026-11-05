# PRISM Production Deployment Environment Variables

This document provides a comprehensive audit and configuration reference for all environment variables used by the PRISM full-stack application across **Vercel** (Frontend), **Render** (Backend), and **Supabase** (Database, Auth, Storage).

---

## Architecture Overview

```
                      +-----------------------------+
                      |       User Browser          |
                      +--------------+--------------+
                                     |
              +----------------------+----------------------+
              |                                             |
              v (HTTPS)                                     v (REST API + Bearer JWT)
+-----------------------------+               +-----------------------------+
|       Vercel (Frontend)     |               |       Render (Backend)      |
|    React 19 / Vite SPA      |               |      FastAPI ASGI App       |
+--------------+--------------+               +--------------+--------------+
               |                                             |
               |                                +------------+------------+
               |                                |            |            |
               v (Auth JWTs)                    v            v            v
+-----------------------------+          +-----------+ +-----------+ +-----------+
|      Supabase Auth          |          |  Supabase | |  Supabase | |  Upstash  |
| (OIDC / ES256 / JWKS)       |          | Postgres  | |  Storage  | |   Redis   |
+-----------------------------+          |  (v15)    | | (S3 API)  | |  (TLS)    |
                                         +-----------+ +-----------+ +-----------+
```

---

## 1. Frontend Environment Variables (Vercel)

These variables must be configured in the **Vercel Dashboard** under **Project Settings -> Environment Variables**.
Only public identifiers and non-secret URLs should ever have the `VITE_` prefix.

| Variable Name | Required? | Default / Example | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | **Yes** | `https://prism-backend.onrender.com` | Base URL of deployed Render backend. All API requests route here. | Render Dashboard -> Web Service -> Service URL | No |
| `VITE_SUPABASE_URL` | **Yes** | `https://tuaeujvuuanadqvykugw.supabase.co` | Project endpoint URL for Supabase Auth and client SDK. | Supabase Dashboard -> Project Settings -> API -> Project URL | No |
| `VITE_SUPABASE_ANON_KEY` | **Yes** | `sb_publishable_...` | Supabase public publishable/anon key. Safe for browser usage. | Supabase Dashboard -> Project Settings -> API -> Project API keys -> `anon` / `publishable` | No |
| `VITE_APP_NAME` | Optional | `Proof-of-Action` | Human-readable title of the application. | Static configuration | No |
| `VITE_ENVIRONMENT` | Optional | `production` | Active frontend client environment. | Set to `production` in Vercel | No |
| `VITE_ENABLE_ANALYTICS` | Optional | `false` | Enables client-side telemetry. | Internal feature flag | No |
| `VITE_ENABLE_DEBUG_MODE` | Optional | `false` | Disables debug logging in production. | Set to `false` in production | No |

> [!CAUTION]
> **Never** expose `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`, `S3_SECRET_KEY`, or `JWT_SECRET` in Vercel environment variables or with a `VITE_` prefix.

---

## 2. Backend Environment Variables (Render)

These variables must be configured in the **Render Dashboard** under **Environment** for the `prism-backend` Web Service (or via blueprint `render.yaml`).

### Database & Migrations

| Variable Name | Required? | Example Value | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** | `postgresql+psycopg2://postgres.tuaeujvuuanadqvykugw:[ENCODED_PW]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require` | Supabase PostgreSQL connection string using psycopg2 driver. Must use **pooler port 6543** for IPv4 compatibility with Render. | Supabase Dashboard -> Project Settings -> Database -> Connection String -> URI (select *Pooler*, Transaction mode). | **YES** |
| `RUN_MIGRATIONS` | Optional | `true` | When `true`, the container startup script automatically runs `alembic upgrade head` before launching Uvicorn. | Set to `true` on Render. | No |
| `MIGRATION_DATABASE_URL` | Optional | *(Same as DATABASE_URL or dedicated migrator user)* | Dedicated migration connection if separated from runtime user. | Supabase Dashboard -> Database. | **YES** |

> [!IMPORTANT]
> **Supabase Password Special Characters**:
> If your database password contains characters like `@`, `:`, `#`, `%`, `&`, they must be URL-encoded (for example, `@` becomes `%40`).
> PRISM includes automatic URL normalization and decoding, but encoding the password in Render avoids shell and parser ambiguity.

---

### Application Runtime & Security

| Variable Name | Required? | Example Value | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `staging` or `production` | Deployment mode. When `production`, activates fail-closed security validators. | Set to `staging` or `production` | No |
| `PORT` | Auto | `10000` | Render dynamically assigns this port; Uvicorn binds to `0.0.0.0:${PORT}`. | Managed automatically by Render | No |
| `JWT_SECRET` | **Yes** | `min-32-chars-cryptographic-random-secret...` | Cryptographic secret for signing tokens. Minimum 32 chars in production. | Generated with `openssl rand -hex 32` | **YES** |
| `CORS_ALLOW_ORIGINS` | **Yes** | `https://your-app.vercel.app,https://prism.yourdomain.com` | Explicit list of trusted frontend origins. Wildcard `*` is permitted only in `development`/`staging`. | Vercel Deployment URL | No |

---

### Supabase Authentication & OIDC

| Variable Name | Required? | Example Value | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AUTH_MODE` | **Yes** | `enforcing` (or `development`) | `enforcing` rejects unauthenticated requests with 401. `development` allows anonymous bypass. | Set to `enforcing` for production. | No |
| `AUTH_DEV_TOKENS_ENABLED` | **Yes** | `false` (production) / `true` (staging) | Disables static development mock tokens (`dev-user-*`). | Set `false` in production. | No |
| `AUTH_OIDC_ENABLED` | **Yes** | `true` | Enables local cryptographic verification of Supabase access tokens. | Set to `true`. | No |
| `AUTH_OIDC_ISSUER` | **Yes** | `https://tuaeujvuuanadqvykugw.supabase.co/auth/v1` | Supabase Auth issuer URL. | Supabase Dashboard -> Settings -> API -> Project URL + `/auth/v1` | No |
| `AUTH_OIDC_JWKS_URI` | **Yes** | `https://tuaeujvuuanadqvykugw.supabase.co/auth/v1/.well-known/jwks.json` | Public JWKS endpoint used to verify JWT signatures locally. | Supabase Dashboard -> Auth JWKS | No |
| `AUTH_OIDC_AUDIENCE` | **Yes** | `authenticated` | Expected audience claim (`aud`) in Supabase tokens. | Default Supabase audience is `authenticated`. | No |
| `AUTH_OIDC_ALGORITHMS` | **Yes** | `ES256,RS256` | Allowed asymmetric signing algorithms. Supabase uses ECC P-256 (`ES256`). | Supabase JWT Keys | No |
| `AUTH_OIDC_IDENTITY_PROVIDER` | **Yes** | `supabase` | Provider identifier stored in the `users` table. | Default: `supabase` | No |

---

### Object Storage (Supabase Storage S3-Compatible API)

| Variable Name | Required? | Example Value | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `S3_ENDPOINT` | **Yes** | `https://tuaeujvuuanadqvykugw.supabase.co/storage/v1/s3` | S3-compatible API endpoint for Supabase Storage. | Supabase Dashboard -> Storage -> S3 Connection | No |
| `S3_REGION` | **Yes** | `ap-south-1` | Supabase project region (e.g. `ap-south-1` for Mumbai). | Supabase Dashboard -> Project Settings -> General | No |
| `S3_USE_SSL` | **Yes** | `true` | Enforces HTTPS on S3 operations. | Always `true` for Supabase Storage. | No |
| `S3_QUARANTINE_BUCKET` | **Yes** | `pofa-quarantine` | Bucket for incoming, unverified evidence files. | Supabase Dashboard -> Storage -> Buckets | No |
| `S3_EVIDENCE_BUCKET` | **Yes** | `pofa-evidence` | Bucket for verified, immutable evidence files. | Supabase Dashboard -> Storage -> Buckets | No |
| `S3_ACCESS_KEY` | **Yes** | `[ACCESS_KEY_ID]` | Supabase S3 Access Key ID. | Supabase Dashboard -> Project Settings -> Storage -> S3 Access Keys | **YES** |
| `S3_SECRET_KEY` | **Yes** | `[SECRET_ACCESS_KEY]` | Supabase S3 Secret Access Key. | Supabase Dashboard -> Project Settings -> Storage -> S3 Access Keys | **YES** |
| `STORAGE_REQUIRED` | Optional | `false` | If `true`, `/readyz` fails if storage cannot be reached. Default `false` allows web server to boot smoothly. | Internal configuration | No |
| `MAX_UPLOAD_SIZE` | Optional | `10485760` (10MB) | Maximum file size in bytes. | Internal configuration | No |

---

### External Redis (Upstash)

| Variable Name | Required? | Example Value | Description | Where to Obtain / Dashboard | Secret? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `REDIS_URL` | Optional / Recommended | `rediss://default:[PASSWORD]@[ENDPOINT].upstash.io:6379` | Managed Redis connection string with TLS (`rediss://`). | Upstash Console -> Databases -> Connect -> Details -> `rediss://...` | **YES** |
| `REDIS_REQUIRED` | Optional | `false` | When `false`, web API does not require Redis to report ready. Set `true` on analysis worker instances. | Internal configuration | No |
| `ANALYSIS_QUEUE_NAME` | Optional | `pofa:analysis:jobs` | Redis list key for background worker jobs. | Internal configuration | No |

---

## Step-by-Step Dashboard Setup Instructions

### 1. Supabase Setup
1. **Database & Pooler**:
   - Go to **Project Settings -> Database**.
   - Under **Connection Pooling**, note the pooler host (e.g. `aws-0-ap-south-1.pooler.supabase.com`), port (`6543`), user (`postgres.tuaeujvuuanadqvykugw`), and database (`postgres`).
2. **Storage Buckets**:
   - Go to **Storage -> Buckets -> New Bucket**.
   - Create bucket `pofa-quarantine` (Private).
   - Create bucket `pofa-evidence` (Private).
3. **Storage S3 Access Keys**:
   - Go to **Project Settings -> Storage**.
   - Click **Generate S3 Access Keys** and save the **Access Key ID** and **Secret Access Key**.
4. **Auth JWKS**:
   - Verify that your Project URL is active (e.g. `https://tuaeujvuuanadqvykugw.supabase.co`).
   - Test that `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json` returns JSON keys.

### 2. Upstash Redis Setup (Optional / Recommended)
1. Go to [https://console.upstash.com](https://console.upstash.com).
2. Click **Create Database**, select the region closest to Supabase (e.g., `ap-south-1` Mumbai or `us-west-2` Oregon).
3. Under **Connect -> Redis URL**, copy the `rediss://...` connection string.

### 3. Render Web Service Setup
1. In Render Dashboard, click **New -> Web Service** and connect `https://github.com/adarshmore19/PRISM.git`.
2. Configure:
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Health Check Path**: `/healthz`
3. In **Environment Variables**, add the values from the Backend table above.

### 4. Vercel Frontend Setup
1. In Vercel Dashboard, click **Add New -> Project** and import `https://github.com/adarshmore19/PRISM.git`.
2. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (or leave default root `.`)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add the Frontend Environment Variables (`VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`).
4. Click **Deploy**.
