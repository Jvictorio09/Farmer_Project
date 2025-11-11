# AgriTrack System Overview

## 1. Product Summary
- **Purpose**: AgriTrack centralizes day-to-day farm operations (activity logging, expense tracking, yield forecasting, reminders) for smallholder farmers and their support staff.
- **Primary Actors**: `farmer`, `technician`, and `admin` roles share a common auth surface; all dashboards currently target farmers.
- **Key Capabilities**:
  - Capture field activities and automatically derive crop yield forecasts.
  - Track farm expenses with analytics, filtering, and export utilities.
  - Surface near-term harvest windows, reminders, and expense trends on the farmer dashboard.
  - Provide HTMX-powered inline reminder management and Chart.js visual summaries.

## 2. Technology Stack
- **Backend**: Django 5.1 with a custom user model (`myApp.User`).
- **Database**: SQLite by default; `psycopg2-binary` and `dj-database-url` included for easy PostgreSQL upgrades.
- **Frontend**: Django templates, Tailwind CSS via CDN, Chart.js 4, HTMX 1.9, Lucide icons.
- **Document Generation**: `reportlab` for PDF exports.
- **Server Runtime**: Configured for Gunicorn + WhiteNoise (production), Railway deploy URL pre-listed in `ALLOWED_HOSTS`.

## 3. Authentication & Authorization
- **Custom User Model** (`myApp.models.User`):
  - Extends `AbstractUser` with `role` (`admin`, `farmer`, `technician`) and optional `region`.
  - Convenience helpers: `is_farmer()`, `is_technician()`, `is_admin()`.
- **Entry Points**:
  - `register_view` (`/register/`) issues login post-registration using `CustomUserCreationForm`.
  - `LoginView` / `LogoutView` use templates under `templates/auth`.
- **Role Routing**:
  - `role_redirect_view` (`/`) inspects `request.user.role`. Farmers land on `farmer_dashboard`; technicians currently reuse the same dashboard placeholder; admins are pushed to Django admin.
- **Session Defaults** in `settings.py`:
  - `LOGIN_URL='login'`, `LOGIN_REDIRECT_URL='farmer_dashboard'`, `LOGOUT_REDIRECT_URL='login'`.

## 4. Domain Model & Relationships
| Model | Key Fields | Relationships / Notes |
| --- | --- | --- |
| `User` | `role`, `region` | Base actor; `farmer` drives most features. |
| `Crop` | `name`, `ideal_seasons`, growth baselines (`days_to_harvest_*`, `seed_rate_*`, `fert_sacks_*`, `yield_t_*`) | Referenced by `Activity`, `Forecast`, `Recommendation`. Baselines power forecasts and UI tooltips. |
| `Activity` | `farmer`, `crop`, `activity_type` (`planting/watering/harvesting`), `date`, `notes`, planting metrics (`area_ha`, `seed_qty_kg`, `fert_sacks`, `spacing`) | Logs field work. Planting entries trigger forecast generation via post-save signal. |
| `Expense` | `farmer`, `expense_type`, `amount`, `date`, `description` | Feeds dashboard KPIs, expense log, and charts. |
| `Forecast` | `farmer`, `crop`, `expected_yield_kg`, `yield_min_kg`, `yield_max_kg`, `season_factor`, `input_factor`, `population_factor`, `harvest_start/end`, `notes` | Auto-created/updated from planting activities; surfaced throughout dashboard and analytics. |
| `Recommendation` | `crop`, `region`, `month`, `reason` | Unused in current UI but prepared for location-based crop advice. |
| `Reminder` | `farmer`, `message`, `due_date` | Managed inline on dashboard with HTMX partial reloads. |
| `FAQ`, `SupportContact` | FAQ knowledge base & support submissions | Not yet surfaced in templates. |

### Forecast Engine
- `compute_forecast_from_activity(activity)` normalizes planting inputs against crop baselines:
  - Seasonality via `_season_factor` comparing planting month to `Crop.ideal_seasons`.
  - Input sufficiency factors for seed and fertilizer.
  - Tree crops (mango, guava, banana) adjust by spacing-derived population density.
  - Harvest window derived from crop maturity days.
- `auto_forecast_on_planting` post-save signal keeps the latest forecast in sync per `farmer/crop`.

## 5. User-Facing Flows

### 5.1 Registration & Login
- Register form (`CustomUserCreationForm`) collects username, email, role, region.
- Post-registration auto-login redirects to dashboard for farmers.
- Shared `auth/base.html` layout uses Tailwind CDN and Lucide icons.

### 5.2 Farmer Dashboard (`farmer_dashboard`)
- **Data Sources**:
  - Distinct crops planted this month (`Activity`).
  - Expense totals, most common expense type, last entry (`Expense`).
  - Recent activities, upcoming reminders, forecast shortlist.
  - Upcoming harvest pipeline from `Forecast` (prefers future `harvest_end`).
- **Visualization Layer** (`templates/myApp/farmer_dashboard.html`):
  - Tailwind-based cards for KPIs.
  - Mini analytics rail:
    - Monthly expense sparkline (`chart_expenses_monthly` JSON endpoint).
    - Expense distribution donut (`chart_expenses_by_category`).
    - Harvest timeline chip rail combining `chart_harvest_timeline` + `chart_yield_by_crop`.
  - Per-crop forecast cards with factor breakdown and `notes` from the forecast engine.
- **Reminders**:
  - HTMX fragment (`partials/reminder_list.html`) auto-refreshes via `hx-trigger="load, reminder-updated"`.
  - Modal forms post to `/reminders/add|edit|delete/`, returning `204` for HTMX success.

### 5.3 Activity Log (`activity_log_view`)
- **Features**:
  - Unified page with "Log Activity" and "Manage Crops" tabs.
  - Quick log form posts to `add_activity`; planting type reveals additional fields (area, seed, fertilizer, spacing) to enrich forecasts.
  - Crop CRUD (add/edit/delete) handled in situ via `CropForm`.
  - Filters by crop, start date, end date.
- **Analytics**:
  - Chart.js mini dashboards hitting `/charts/activities/monthly|type|crop/`.
- **Exports**:
  - CSV/PDF export endpoints respect optional `start/end` query params.

### 5.4 Expense Tracker (`expense_log_view`)
- **CRUD**:
  - Inline add, modal edit, confirm delete.
  - Filters by month/year keep state for exports and KPIs.
- **Statistics**:
  - Aggregations on filtered queryset compute `total`, `avg_expense`, and top category totals.
  - Secondary monthly summary uses current-month snapshot for context.
- **Visualizations**:
  - `/expenses/chart/data/` for monthly totals.
  - `/charts/expenses-by-category/` reused for donut and bar charts.
- **Exports**:
  - CSV (`export_expenses_csv`) and PDF (`export_expenses_pdf`) honour filter query parameters.

### 5.5 Chart & Analytics Endpoints
- All chart endpoints return JSON for Chart.js, scoped to `request.user`.
- Activity endpoints support optional `start` / `end` querystring filtering via `_date_range`.
- Expense endpoints normalize amounts to floats for serialization.

### 5.6 Reminder Lifecycle
- `add_reminder` / `edit_reminder` / `delete_reminder` respond with `204` for HTMX calls to avoid full-page reload.
- `refresh_reminders` re-renders the reminder list partial; JS dispatches `reminder-updated` after form submissions to trigger refresh.

### 5.7 Data Export Workflows
- CSV export uses Python’s `csv` module to stream responses.
- PDF export builds simple tabular layouts with ReportLab (`canvas.Canvas`), paginating when height is exhausted.

## 6. Frontend Composition
- **Base Layouts**:
  - `templates/base.html` for authenticated pages (header nav + footer includes).
  - `templates/auth/base.html` for standalone auth screens.
- **Reusable Includes**:
  - `includes/header.html` provides top nav with active-route highlighting.
  - `partials/reminder_list.html` is HTMX target.
- **Styling & JS Utilities**:
  - Tailwind loaded via CDN (v2.2.19).
  - Chart.js via CDN (v4.4.1) on pages requiring charts.
  - HTMX wired globally in `base.html` for AJAX partial updates.
  - Lucide icons initialized client-side.

## 7. Supporting Utilities & Scripts
- **`seed_crops.py`**:
  - Standalone script to upsert baseline crop records with agronomic defaults.
  - Validates presence of required `Crop` fields before seeding.
  - Run with `DJANGO_SETTINGS_MODULE=myProject.settings python seed_crops.py`.

## 8. Configuration & Environment
- **Settings Highlights**:
  - `AUTH_USER_MODEL='myApp.User'` enables the custom user.
  - `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` pre-configured for Railway deploy domain.
  - Static files served via Django (`STATIC_URL='static/'`); WhiteNoise is included in requirements for production but not yet wired in middleware.
- **Dependencies** (`requirements.txt`):
  - Django 5.1.2 core stack, `python-dotenv` for environment variables, `gunicorn` for production WSGI, `whitenoise` for static assets.
- **Database**: SQLite located at `myProject/db.sqlite3`; migrations define schema through `migration 0003`.

## 9. External Integrations
- **Client-Side Libraries**: Tailwind, Chart.js, HTMX, Lucide (all CDN-delivered).
- **Server-Side Packages**: ReportLab for PDF, psycopg2-binary for optional PostgreSQL, dj-database-url for DSN parsing.
- **No background workers** currently (forecasting handled synchronously on activity save).

## 10. Known Gaps & Next Steps
- `templates/myApp/index.html` is a placeholder (`"sdafdfdsds"`) and not wired to routing; replace with a meaningful landing page or remove.
- Technician-specific dashboard route (`dashboard`) referenced in `role_redirect_view` does not exist; technician users currently receive a broken redirect.
- `Recommendation`, `FAQ`, and `SupportContact` models have no UI surfaces yet.
- Header nav hardcodes `/activities/` highlight; consider DRYing route matching or using `{% url %}` comparisons consistently.
- WhiteNoise and Gunicorn are declared but not configured in `settings.py` (e.g., `STATIC_ROOT`, middleware insertion) for production readiness.
- No automated tests in `tests.py`; consider covering forecast computations and exports.

---

This document should serve as the canonical reference for developers onboarding to AgriTrack, mapping model relationships, request flows, and integration points across the Django project.

