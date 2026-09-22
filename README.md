# PetCare — Pet Health & Care Management Platform

PetCare is a production-oriented Flask application for managing a pet owner's digital health passport: pets, medical history, vaccinations, medications, appointments, reminders and operational dashboards.

The supplied product specification calls for a responsive, secure, Supabase-backed pet-health platform with Render deployment and optional integrations. fileciteturn0file0L5-L22

## Current implementation

This repository now contains:

- Python 3.11 Flask application
- Supabase PostgreSQL-ready configuration
- SQLAlchemy data models for users, pets, vaccinations, medications, appointments, reminders, notifications, weight records, preventive care, documents and audit logs
- Cookie-based JWT authentication
- Owner-level pet ownership checks to reduce IDOR/BOLA risk
- Rate limits on authentication endpoints
- Responsive PetCare dashboard, pet profiles and admin console
- Automatic reminder creation when vaccination/appointment due dates are recorded
- In-app notification records
- PDF pet health report endpoint
- Supabase Storage upload endpoint for medical documents
- Demo admin account and demo pets seeded on first startup
- Render deployment configuration
- Vercel Python entrypoint/configuration
- Health check endpoint at `/health`
- Basic smoke tests with Pytest

The project follows the specification's requested Python 3.11 / Flask / Supabase / Gunicorn direction. fileciteturn0file0L26-L48

## Demo admin credentials

**Email:** `admin@petcare.local`  
**Password:** `PetCare@12345`

These are development/demo credentials only. Change them through environment variables before exposing a production deployment.

## Local setup

### 1. Clone

```bash
git clone https://github.com/SanFlash/petcare.git
cd petcare
```

### 2. Create a Python 3.11 virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment

```bash
copy .env.example .env
```

For macOS/Linux:

```bash
cp .env.example .env
```

Minimum local configuration can run against the included SQLite development fallback, but production should use Supabase PostgreSQL.

Example production variables:

```env
SECRET_KEY=long-random-secret
JWT_SECRET_KEY=another-long-random-secret
DATABASE_URL=postgresql://...
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_KEY=YOUR_SERVER_SIDE_KEY
SUPABASE_STORAGE_BUCKET=petcare
DEMO_ADMIN_EMAIL=admin@petcare.local
DEMO_ADMIN_PASSWORD=PetCare@12345
APP_BASE_URL=https://your-domain
```

The application expects secrets and database credentials through environment variables rather than source code. fileciteturn0file0L52-L82

### 5. Run

```bash
python run.py
```

Open:

```
http://127.0.0.1:5000
```

### 6. Run tests

```bash
pytest -q
```

## Main routes

```
/
 /login
 /register
 /dashboard
 /pets/<pet_id>
 /admin

 /health

 /api/auth/register
 /api/auth/login
 /api/auth/logout
 /api/dashboard
 /api/pets
 /api/pets/<pet_id>/vaccinations
 /api/pets/<pet_id>/medications
 /api/pets/<pet_id>/appointments
 /api/pets/<pet_id>/medical-records
 /api/pets/<pet_id>/reminders
 /api/reminders/<reminder_id>/complete
 /api/admin/stats
```

## Render deployment

The repository includes `render.yaml`.

### Automatic deploy

1. Push this repository to GitHub.
2. In Render, choose **New + → Blueprint**.
3. Select `SanFlash/petcare`.
4. Render reads `render.yaml`.
5. Add the Supabase values for `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_KEY` and `APP_BASE_URL`.
6. Deploy.

Render build command:

```bash
pip install -r requirements.txt
```

Render start command:

```bash
gunicorn run:app
```

Health check:

```
/health
```

The deployment target is Python 3.11.9.

## Supabase setup

Create a Supabase project and obtain:

- Project URL
- Server-side key
- PostgreSQL connection string

Set the PostgreSQL connection string in `DATABASE_URL`.

Set a storage bucket named `petcare` (or change `SUPABASE_STORAGE_BUCKET`). Keep medical-document storage private and use server-side credentials only.

The application creates its SQLAlchemy tables on startup for this initial build. For a larger production system, move to formal Alembic migrations before making incompatible schema changes.

## Vercel deployment

The repository includes:

- `api/index.py`
- `vercel.json`

Deploy from the Vercel dashboard by importing the GitHub repository, then configure the same environment variables used by Render.

The Vercel entrypoint is:

```python
from run import app
```

This avoids the common “no Flask entrypoint found” problem by explicitly pointing Vercel at the Flask app.

## Notifications

The current implementation persists in-app notification records and creates reminder records for due-date driven tasks.

External email, push, WhatsApp and calendar integrations are intentionally configuration-driven. The product specification identifies these as notification/integration channels, but this repository's core build does not pretend an external provider is active when credentials are absent. fileciteturn0file0L492-L620

For production reminders at scale, use a separate worker/cron architecture rather than relying only on an in-process scheduler. fileciteturn0file0L1247-L1289

## Security notes

The application includes:

- Password hashing
- JWT authentication in HttpOnly cookies
- Role-based admin page protection
- Owner checks on pet records
- Input validation for core write endpoints
- Authentication rate limiting
- File-extension restrictions for document uploads
- Environment-based secrets

Before production launch, also configure:

- HTTPS
- Strong random secrets
- Supabase RLS/storage policies appropriate to your architecture
- A production rate-limit store
- CSRF protection if you add state-changing browser forms
- Formal migrations
- Email verification/password reset provider
- Centralized logging/monitoring
- Backups and recovery testing

These areas are consistent with the supplied security and production-readiness requirements. fileciteturn0file0L1293-L1359

## Product scope

The target product covers a digital pet health passport: profile data, medical history, vaccinations, medications, preventive care, appointments, reminders, documents, weight tracking, reports, QR/lost-pet capabilities and an admin console. fileciteturn0file0L288-L355 fileciteturn0file0L361-L488 fileciteturn0file0L626-L646 fileciteturn0file0L863-L910

### Important product disclaimer

PetCare is a tracking and reminder platform. It is not a veterinary diagnostic system and does not replace professional veterinary care.
