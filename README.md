# PAWCARE 360

> **Every Paw. Every Record. Every Reminder.**


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
- Animated 3D-style landing experience with particle field, glassmorphism, tilt cards and responsive motion
- Notification center with live in-app care feed
- Twilio SMS integration for owner alerts
- Scheduled reminder-processing worker for Render

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
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
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

## Notifications and SMS

PetCare now has a notification pipeline designed around the owner's phone:

1. A care event creates an in-app notification.
2. If the owner has a phone number and Twilio is configured, an SMS is attempted.
3. Upcoming reminders are processed by `scripts/process_notifications.py`.
4. The Render configuration includes a scheduled notification worker.
5. SMS attempts are recorded as `sms/sent` or `sms/failed` notification records.

Configure:

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
```

Use an E.164 phone number for the owner, for example `+919876543210`.

The browser never receives Twilio credentials. They remain server-side environment variables.

The notification architecture follows the product specification's requirement for reminders and multi-channel notifications while keeping external providers optional until credentials are configured. fileciteturn0file0L492-L620

### Manual worker test

After configuring your environment:

```bash
python scripts/process_notifications.py
```

For production, the Render cron service runs the same worker automatically.


## UI / UX redesign

The new interface is intentionally different from the earlier utility-dashboard approach.

It now uses:

- Dark premium visual system
- Glassmorphism surfaces
- 3D-style depth and perspective
- Interactive pointer tilt
- Animated floating pet card
- Particle/network background
- Ambient gradient orbs
- Motion-based reveal transitions
- Animated progress/routine indicators
- Responsive touch-friendly layouts
- Quick-action modal forms instead of browser `prompt()` flows
- Notification drawer
- Toast feedback after actions
- Clear care-status chips
- Mobile-specific layout breakpoints
- Existing repository pet imagery reused for relevant visual context

Animations are implemented with CSS and lightweight browser JavaScript rather than a heavy front-end framework, keeping deployment simple.

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


## Owner appointment SMS schedule

When a pet is created, the owner mobile number can be saved with the pet profile. PetCare creates reminders for appointments, vaccination due dates, medical follow-ups, and custom/checkup reminders.

For each upcoming event, the notification worker sends:

- **2 days before** — first SMS follow-up
- **1 day before** — second SMS follow-up
- **Event day** — final SMS reminder

Each stage is deduplicated so the 15-minute worker does not send the same stage repeatedly.

The scheduler uses `APP_TIMEZONE` (default `Asia/Kolkata`) rather than the server's UTC date.

### Twilio configuration

Set these server-side environment variables:

```env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...
TWILIO_MESSAGING_SERVICE_SID=...
APP_TIMEZONE=Asia/Kolkata
```

Use either `TWILIO_FROM_NUMBER` or `TWILIO_MESSAGING_SERVICE_SID`.

The dashboard now has a **Test SMS** button after an owner number is saved. Use it before creating a real appointment so you know the Twilio connection is working.

For India, Twilio documents country-specific SMS/DLT requirements; review the sender registration requirements before production use. urlTwilio India SMS guidelineshttps://www.twilio.com/en-us/guidelines/in/sms

Render cron jobs run the configured command on schedule and receive their configured environment variables. urlRender cron job documentationhttps://render.com/docs/cronjobs


## PAWCARE 360 UI/UX redesign

The application now uses a veterinary SaaS command-center experience built around:

- Responsive sidebar + top navigation shell
- Light/dark theme with persisted preference
- Global pet/appointment search
- Action-first dashboard hierarchy
- Needs Attention, Today's Schedule and Upcoming Events
- Responsive appointment calendar with month/week/day controls
- Pet overview cards and premium pet profile
- Health timeline, vaccination and medication views
- Notification center and SMS test flow
- Admin operations workspace
- Branded empty, loading, success and error states
- Keyboard focus states and `prefers-reduced-motion` support
- Mobile navigation drawer and compact, scrollable modals

The redesign preserves the existing Flask, SQLAlchemy, JWT-cookie authentication, notification worker, Twilio SMS and database APIs rather than replacing the application with hardcoded UI data.

### Design system

Primary `#2F6F73`, secondary `#74B49B`, accent `#F4B942`, background `#F7FAFC`, surface `#FFFFFF`, text `#243238`, muted `#718096`, success `#43A978`, warning `#E9A23B`, danger `#E76F51`, info `#4F8CC9`.

Dark mode uses `#0F1720`, `#16232D`, `#1C303A`, `#F4F7F8`, `#9AAEB8` and `#5CC8C2`.

### Functional boundaries

The current backend does not expose full CRUD endpoints for every requested enterprise screen (for example document uploads, appointment editing/rescheduling, medication editing, or owner management). The redesign therefore does not invent fake production data or pretend those operations exist. Existing working actions remain connected to their real APIs, while unsupported areas are presented through the available records and navigation anchors.
