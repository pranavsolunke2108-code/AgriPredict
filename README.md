# AgriPredict - Smart Agriculture Management System (DBMS Project)

AgriPredict is a smart farm management, crop cycle tracking, and data-driven agronomic recommendation system built for a MySQL DBMS academic capstone project. It features farmer authentication, multi-tenant farm isolation, soil test logging, automated weather caching via the **Open-Meteo API**, a **MySQL stored procedure recommendation engine (`recommend_crops`)**, **crop cycle lifecycle management with triggers and stored procedures (`start_crop_cycle`, `close_crop_cycle`)**, financial tracking with **views (`current_status_view`, `farmer_history_view`, `farmer_summary_view`)**, **agronomic fertilizer dosage planning (`recommend_fertilizer`)**, **crop rotation recommendations (`rotation_advice`)**, **crop calendar growth stages (`crop_calendar_view`)**, **trigger-based automated weather alerts (`trg_weather_ai`, `trg_weather_au`)**, **task alerts scheduling (`generate_task_alerts`)**, **market mandi prices with economics forecasting**, **least-privilege MySQL accounts**, and a **clean, mobile-friendly frontend** with interactive **Chart.js** data visualizations and multilingual support (English, Marathi, Hindi).

Built with **FastAPI**, **MySQL 8.x (InnoDB)**, raw parameterized SQL queries using **mysql-connector-python**, **bcrypt** password hashing, and **JWT** session tokens.

---

## 📋 Table of Contents

- [Architecture & Tech Stack](#architecture--tech-stack)
- [Least-Privilege Database Accounts](#least-privilege-database-accounts)
- [Project Structure](#project-structure)
- [Database Setup & Sequential Execution](#database-setup--sequential-execution)
- [Configuration (.env)](#configuration-env)
- [Running the Program](#running-the-program)
- [Creating an Administrator](#creating-an-administrator)
- [One-Minute Demo Seeder (`seed_demo.py`)](#one-minute-demo-seeder-seed_demopy)
- [UI and Design System](#-ui-and-design-system)
- [Web Frontend UI Pages](#web-frontend-ui-pages)
- [Database Objects Catalog](#database-objects-catalog)
  - [Tables (16)](#tables-16)
  - [Views (7)](#views-7)
  - [Stored Procedures (9) & Functions (1)](#stored-procedures-9--functions-1)
  - [Triggers (11)](#triggers-11)
  - [Scheduled Events (1)](#scheduled-events-1)
- [API Endpoints Reference](#api-endpoints-reference)
- [Backup and Restore Guide](#backup-and-restore-guide)
- [Running Automated Tests](#running-automated-tests)
- [Known Limitations](#known-limitations)

---

## 🛠️ Architecture & Tech Stack

- **Python**: 3.11+ (tested on Python 3.14)
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/) with asynchronous ASGI server [Uvicorn](https://www.uvicorn.org/)
- **Database Engine**: MySQL 8.x (InnoDB with ACID transaction isolation and crash recovery)
- **Database Driver**: `mysql-connector-python` with connection pooling (`MySQLConnectionPool`)
- **Query Strategy**: Strict raw parameterized SQL queries (`%s` placeholders), MySQL views, and stored procedure calls (`CALL start_crop_cycle(...)`, `CALL close_crop_cycle(...)`, `CALL recommend_crops(...)`) — full SQL injection immunity for DBMS viva scrutiny
- **Password Security**: `bcrypt` (salted, adaptive hashing stored in `farmers.password_hash`)
- **Session Tokens**: JSON Web Tokens (JWT) signed via `python-jose` (HS256)
- **External Weather API**: [Open-Meteo](https://open-meteo.com/) (free, no API key required; fetches past 30 days of mean temperature, rainfall, and relative humidity)
- **Frontend**: Clean, lightweight, responsive vanilla HTML5, CSS3, and JavaScript with [Chart.js](https://www.chartjs.org/) for data visualization
- **Internationalization (i18n)**: English, Marathi, Hindi with database dictionary fallback to English and `crop_localized_view`
- **Validation**: Pydantic v2 schemas with custom validators
- **Testing**: `pytest` and `httpx` with 61 comprehensive automated tests

---

## 🔐 Least-Privilege Database Accounts

To adhere to enterprise security and principle of least privilege, AgriPredict isolates database operations across three distinct MySQL user accounts:

| MySQL User | Scope & Privileges | Used By |
|---|---|---|
| **`agripredict_app`** | `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `CREATE TEMPORARY TABLES` on `agripredict.*`. **Cannot execute DDL (`CREATE TABLE`, `DROP`, `ALTER`)**. | FastAPI Web Backend runtime (`.env` setting `DB_USER`). |
| **`agripredict_migrate`** | `ALL PRIVILEGES` on `agripredict.*`. | Setup scripts, schema migrations, and test harness (`.env` setting `DB_MIGRATE_USER`). |
| **`agripredict_report`** | Read-only access to views and reference tables: `current_status_view`, `farmer_history_view`, `farmer_summary_view`, `crop_calendar_view`, `latest_prices_view`, `cycle_expense_summary_view`, `crops`, `fertilizers`, `market_prices`. **Cannot read `farmers` table** (protects password hashes and phone numbers). | BI dashboards, external reporting tools, and database auditors. |

---

## 📁 Project Structure

```text
AgriPredict/
├── agripredict_schema.sql                  # Phase 1: Core tables, foreign keys, CHECK constraints & starter seed
├── agripredict_phase2_recommend.sql        # Phase 2: recommend_crops stored procedure & get_season function
├── agripredict_phase3_dashboard.sql        # Phase 3: Crop cycles, triggers, dashboard views & procedures
├── agripredict_phase4_advisory.sql         # Phase 4: Fertilizer advice, rotation rules, alerts triggers & event
├── agripredict_phase5_market_admin.sql     # Phase 5: APMC market prices, profit procedures, admin audit log
├── agripredict_phase6_indexes.sql          # Phase 6a: Production index optimization & redundant index removal
├── agripredict_phase6_translations.sql     # Phase 6b: 97 multilingual keys (EN/MR/HI) & crop_localized_view
├── agripredict_phase6_security.sql         # Phase 6c: Role-based least-privilege MySQL accounts
├── seed_demo.py                            # Rapid 1-minute full application demo seeder
├── create_admin.py                         # Interactive CLI script to securely create admin accounts
├── backup_agripredict.ps1                  # PowerShell automated database backup & compression script
├── backup_agripredict.sh                   # Linux/macOS automated database backup script
├── .env.example                            # Configuration template
├── .env                                    # Active database credentials and secrets (ignored by git)
├── requirements.txt                        # Python dependencies
├── app/
│   ├── config.py                           # Environment configuration loader using python-dotenv
│   ├── db.py                               # Connection pooling, parameterized queries & procedure helpers
│   ├── security.py                         # Bcrypt hashing and JWT encoding/decoding utilities
│   ├── schemas.py                          # Pydantic request/response validation schemas
│   ├── dependencies.py                     # FastAPI dependencies (get_current_farmer, require_admin)
│   ├── main.py                             # FastAPI application root, CORS middleware, error handlers & UI routes
│   ├── services/
│   │   └── weather_service.py              # Open-Meteo weather fetcher, upsert logic & 6-hr caching
│   └── routers/
│       ├── auth.py                         # POST /auth/register, POST /auth/login, GET /me, PATCH /me/language
│       ├── farms.py                        # Farm CRUD: POST, GET, PUT, DELETE /farms
│       ├── soil_tests.py                   # Soil Test CRUD: POST, GET, DELETE /soil-tests
│       ├── weather.py                      # POST /weather/refresh, GET /weather, POST /weather/manual
│       ├── recommendations.py              # POST /recommend, GET /predictions
│       ├── dashboard.py                    # GET /dashboard/summary, /dashboard/current, /dashboard/history
│       ├── cycles.py                       # POST /farms/{farm_id}/cycles, POST /cycles/{cycle_id}/close, logs
│       ├── expenses.py                     # POST, GET /cycles/{id}/expenses, DELETE /expenses/{id}
│       ├── advisory.py                     # Fertilizer plan, rotation advice, crop calendar timeline
│       ├── alerts.py                       # Field alerts, unread counts, mark as read
│       ├── prices.py                       # APMC market rates, trends, profit estimates
│       └── admin.py                        # Master data CRUD, user management, audit log, CSV bulk price upload
├── static/                                 # Clean, mobile-friendly frontend
│   ├── css/style.css                       # Agricultural design system tokens, responsive grid, glass cards
│   ├── js/api.js                           # Centralized API client, JWT storage, i18n translation helpers
│   ├── login.html                          # Farmer & admin login page
│   ├── register.html                       # Farmer registration page
│   ├── dashboard.html                      # Overview KPIs, Chart.js profit & expense charts, active cycle cards
│   ├── farms.html                          # Farm management, soil tests, Open-Meteo telemetry & recommendations
│   ├── cycle_detail.html                   # Cycle tracking, stage tasks, input expenses & close cycle dialog
│   ├── alerts.html                         # Real-time weather, task, and price alerts center
│   ├── prices.html                         # APMC mandi commodity prices, 90-day trends & profit projections
│   └── admin.html                          # Admin master data control center, user toggles & CSV price upload
└── tests/                                  # Automated pytest test suite (57 tests)
```

---

## 🗄️ Database Setup & Sequential Execution

Run the SQL migration scripts **in exact sequential order** as MySQL root:

```bash
# 1. Create database and core schema (14 tables + starter seed)
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS agripredict CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p agripredict < agripredict_schema.sql

# 2. Deploy Phase 2 recommendation engine procedure & get_season function
mysql -u root -p agripredict < agripredict_phase2_recommend.sql

# 3. Deploy Phase 3 crop cycles, audit log, triggers & dashboard views
mysql -u root -p agripredict < agripredict_phase3_dashboard.sql

# 4. Deploy Phase 4 agronomic advisory, crop calendar view, weather triggers & alerts
mysql -u root -p agripredict < agripredict_phase4_advisory.sql

# 5. Deploy Phase 5 market prices, economics procedures, admin audit log & price triggers
mysql -u root -p agripredict < agripredict_phase5_market_admin.sql

# 6. Deploy Phase 6a index performance optimizations
mysql -u root -p agripredict < agripredict_phase6_indexes.sql

# 7. Deploy Phase 6b translations dictionary (97 keys x 3 languages) & crop_localized_view
mysql -u root -p agripredict < agripredict_phase6_translations.sql

# 8. Deploy Phase 6c least-privilege MySQL accounts
mysql -u root -p < agripredict_phase6_security.sql
```

*(Note: Verify that the passwords inside `agripredict_phase6_security.sql` match your `.env` configuration).*

---

## ⚙️ Configuration (.env)

Copy `.env.example` to `.env` and configure your credentials:

```ini
# AgriPredict Database Runtime Configuration (Least-Privilege App User)
DB_HOST=localhost
DB_PORT=3306
DB_USER=agripredict_app
DB_PASSWORD=App_AgriPredict#2026
DB_NAME=agripredict
DB_POOL_NAME=agripredict_pool
DB_POOL_SIZE=5

# MySQL Migration / DDL User (for schema migrations & test setup)
DB_MIGRATE_USER=agripredict_migrate
DB_MIGRATE_PASSWORD=Migrate_AgriPredict#2026

# Security & Session Tokens
JWT_SECRET=agripredict_local_development_secret_key_2026
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 🚀 Running the Program

### 1. Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Seed Demo Data (Fast 1-Minute Showcase)
Seed the complete showcase dataset (demo farmer, 2 farms, soil tests, 30 days of weather, active growing cycle, completed harvested cycle with profit, and alerts):

```bash
python seed_demo.py
```

### 3. Import Multilingual Translations (Optional / Complete Fix)
To import all 242 clean Devanagari UI keys (English, Marathi, Hindi) and overwrite any previously corrupted translation rows:

```cmd
mysql -u root -p --default-character-set=utf8mb4 agripredict -e "source d:\Projects\Personal\AgriPredict\agripredict_i18n_extra.sql"
```

### 4. Start the Web Server
Launch the FastAPI ASGI application with live reloading:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Access the Application
- **Public Home Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) *(Interactive landing page with dynamic time-of-day sky, URL testing override `?sky=dawn|day|dusk|night`, animated SVG field scene, Try-it-now quick crop sandbox, sowing season recommendations, and stats)*
- **Farmer & Demo Dashboard**: [http://127.0.0.1:8000/ui/dashboard](http://127.0.0.1:8000/ui/dashboard)
- **Login Screen**: [http://127.0.0.1:8000/ui/login](http://127.0.0.1:8000/ui/login)
  - **Demo Farmer Credentials**: Phone `9876543210` / Password `Demo@1234`
- **Interactive Swagger API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 👨‍💼 Creating an Administrator

To access the Admin Control Center (`/ui/admin`) or manage master crop catalogs, create an administrator account using the secure CLI helper:

```bash
python create_admin.py --name "System Administrator" --phone "9325020551" --email "admin@agripredict.in"
```
*(You will be prompted to enter and confirm a password).*

---

## 🌱 One-Minute Demo Seeder (`seed_demo.py`)

The `seed_demo.py` script enables immediate presentation and evaluation of all AgriPredict features in one minute without manual data entry.

**Features Created:**
1. **Demo Farmer**: Ramesh Patil (Phone: `9876543210`, Password: `Demo@1234`, Language: Marathi).
2. **Two Farms**:
   - `Ganga Plot (Main Field)`: 3.5 acres, Loamy soil, Drip irrigation.
   - `Yamuna Plot (Canal Field)`: 2.0 acres, Black soil, Canal irrigation.
3. **Soil Tests**: Nitrogen, Phosphorus, Potassium, pH (6.8 and 7.2), Moisture, and Organic Carbon recorded for both farms.
4. **Historical Weather**: 30 days of daily temperature, humidity, and precipitation telemetry.
5. **Active Growing Cycle**: Cotton on Farm 1 (sown 45 days ago) with stage tracking and 3 input expenses (Seeds, Fertilizer, Labour).
6. **Harvested Crop Cycle**: Soybean on Farm 2 (harvested 10 days ago) with 1,800 kg yield @ ₹4,850/q, 5 recorded expenses, generating ₹73,200 net profit.
7. **Field Alerts**: 4 real-time warnings (Heavy Rain advisory, Extreme Heat warning, Stage Task notification, Mandi Price alert).

**Safety Constraint:**
`seed_demo.py` strictly refuses to execute if the database contains more than 5 farmers, preventing accidental overwriting or data bloat in shared environments.

---

## 🎨 UI and Design System

AgriPredict features an **"Earthy Modern, Farmer-First"** frontend design system engineered specifically for rural usability, outdoor sunlight legibility, and smooth performance on low-end mobile hardware.

### Design Principles & Philosophy
- **Palette**: Warm cream (`#FBF8F1`) and forest green (`#2F7D4F`) with harvest terracotta and gold accents—warm, trustworthy, and distinctly agricultural.
- **Sunlight Readability**: High contrast ratio ($\ge 4.5:1$) across all typography and data controls; crisp solid surfaces without blurry glassmorphism that degrades contrast or slows down budget phones.
- **Farmer Touch Usability**: All primary buttons and interactive elements meet or exceed touch target requirements ($\ge 48\text{px}$ height and width).
- **Multilingual Native Typography**: Native Devanagari typography using Google Font **Noto Sans Devanagari** paired with **Inter**, ensuring clean rendering for Marathi (MR) and Hindi (HI).
- **Responsive App Shell**:
  - **Desktop ($\ge 1024\text{px}$)**: Fixed 250px left sidebar with branding, quick links, active season badge, and farmer profile footer.
  - **Tablet ($768\text{px}$ - $1023\text{px}$)**: Fluid grid with collapsible sidebar.
  - **Mobile ($\le 767\text{px}$, optimized for $360\text{px}$ Android)**: Fixed bottom tab bar (`Dashboard`, `Farms`, `Cycles`, `Alerts`, `Prices`) with sticky top utility header for theme toggle and language switching.

### Design Tokens (`static/css/theme.css`)
Centralized CSS custom properties define the complete visual token set:
- **Light Theme**: `--bg: #FBF8F1`, `--surface: #FFFFFF`, `--ink: #1C2826`, `--muted: #5B6B64`, `--primary: #2F7D4F`, `--primary-hover: #256640`.
- **Dark Theme**: `--bg: #0F1A14`, `--surface: #18261E`, `--ink: #EAF0EC`, `--muted: #95A89E`, `--primary: #4EA371`, `--primary-hover: #60B784`.
- **Seasonal Accents**:
  - `Kharif`: `--season-kharif: #2F7D4F` (Monsoon green)
  - `Rabi`: `--season-rabi: #C97A3E` (Winter harvest gold)
  - `Zaid`: `--season-zaid: #D9534F` (Summer warm terracotta)
  - `Annual`: `--season-annual: #3B7A8C` (Perennial blue)
- **Status & Alerts**: Success (`#2E7D32`), Warning (`#D97706`), Danger (`#C62828`), Info (`#0284C7`).

### Restyled Pages & Components
1. **Farms Grid (`/ui/farms`)**:
   - Responsive card grid displaying plot size, soil type, and irrigation chips.
   - SVG contour map thumbnail with GPS coordinate tag (or styled placeholder when coordinates are pending).
   - Five rapid-action buttons: *Recommend*, *Soil Test*, *Fertilizer Plan*, *Weather*, and *What to Grow Next*.
2. **Crop Recommendations Modal**:
   - Ranked result cards featuring a circular SVG suitability percentage gauge.
   - Localized crop name with emoji badges.
   - Horizontal multi-factor breakdown bars for pH, temperature, humidity, rainfall, N, P, and K.
   - Economic projections (expected yield, gross revenue, cultivation costs, net profit) with *Fertilizer Plan* and *Start This Crop* actions.
3. **Crop Cycle Details (`/ui/cycle-detail`)**:
   - Real-time **Growth Stages Stepper Timeline** with *Done*, *Current*, and *Upcoming* state badges and task lists.
   - Harvest Countdown KPI card with overdue warnings.
   - Tailored **Fertilizer Plan** card with calculated nutrient dosages (Urea, DAP, MOP).
   - **Spend by Category** Chart.js donut chart alongside itemized expenses table.
   - Prominent **Close Crop Cycle** action card for recording final yield and market revenue.
4. **Alerts Center (`/ui/alerts`)**:
   - Interactive filter chips (*All Types*, *Unread Only*, *Rain*, *Heat*, *Frost*, *Drought*, *Task*, *Price*).
   - Distinct colored icon avatars per alert category with terracotta left-border highlight for unread items.
   - Batch *Mark All as Read* and individual resolution buttons.
5. **Forms & Modals**:
   - Single-column flow on mobile viewports ($\le 480\text{px}$).
   - High-contrast labels positioned cleanly above inputs with contextual helper hints (acceptable ranges, units).
   - Inline feedback and error summaries.
   - Full-width large primary buttons with animated spinner loading states on submit.
6. **Authentication (`/ui/login`, `/ui/register`)**:
   - Desktop split layout: left agricultural hero illustration panel + right clean card form.
   - Mobile single-column fluid card layout.
7. **Admin Control Center (`/ui/admin`) & Mandi Prices (`/ui/prices`)**:
   - Mobile horizontal scroll wrapper (`.table-wrapper`) preventing layout breakage.
   - Sticky table headers and alternating zebra row striping.
8. **Public Home Page (`/`)**:
   - Pure tokenized styling seamlessly matching the application design tokens.
   - Retains dynamic time-of-day sky with testing URL override (`?sky=dawn|day|dusk|night`), dark text scrim for high contrast, animated SVG field scene, and synchronized "Try it now" sandbox.
9. **Skeletons & Friendly Empty States**:
   - Shimmering loading skeletons for all async data cards and tables.
   - Descriptive empty states with illustrative icons and immediate call-to-action buttons.

---

## 🌐 Web Frontend UI Pages & Security Guard

AgriPredict features an enterprise-grade client-and-server authentication guard that prevents unauthenticated flashing of empty content or placeholder figures (`₹0.00`). All protected pages employ CSS anti-flash shielding (`body.auth-protected { visibility: hidden; }`) until asynchronous session validation (`GET /me`) passes. Any expired or missing token immediately triggers an automatic redirection to `/ui/login?next=<path>` with strict same-origin sanitization (blocking external protocol and open-redirect vectors).

| URL Route | Page Title | Key Capabilities |
|---|---|---|
| `/` | Public Home Page | Public landing page with time-of-day sky gradient (supports `?sky=dawn|day|dusk|night` testing override), dark text scrim for high contrast, animated SVG field scene, "Try it now" sandbox with synchronized sliders, top-3 crop recommendations, "Sowing now" cards, aggregate statistics counters, features grid, how-it-works strip, sample mandi rates, and dynamic auth-aware header with desktop and mobile drawer navigation. |
| `/ui/login` | Login | Phone/email authentication, JWT session token storage, cookie persistence, and safe `?next=` redirection. |
| `/ui/register` | Register | Farmer registration with district, village, default language preference, and preservation of `?next=` redirect path. |
| `/ui/dashboard` | Dashboard | Protected overview with KPI cards, Chart.js profit & expense breakdown charts, dynamic Current Status cards (showing crop, farm, stage progress, tasks, days since sowing, expected harvest date, and days to harvest), and a unified in-page **Start New Cycle** modal (no navigation). |
| `/ui/farms` | My Farms | Add/edit farms, record soil tests, sync Open-Meteo weather, generate crop recommendations with 1-decimal scores, interactive **Fertilizer Plan** modals with gap analysis, and rotation advice. |
| `/ui/cycle-detail?id={id}` | Cycle Details | Real-time cycle tracking with an interactive **Crop Calendar Timeline** (Done, Current, Upcoming badges), dedicated **Fertilizer Plan** section, input expense tracking, and close cycle modal. |
| `/ui/alerts` | Alerts Center | Heavy rain, extreme heat, stage task, and price alerts with unread badge counter and mark-as-read toggles. |
| `/ui/prices` | Mandi Prices | APMC commodity market rates across Maharashtra districts, 90-day historical trend line charts, and crop profitability estimations. |
| `/ui/admin` | Admin Panel | Master data CRUD (Crops, Growth Stages, Fertilizers, Rotation Rules), user activation toggle, audit log viewer, and bulk CSV price upload. |

---

## 📊 Database Objects Catalog

AgriPredict leverages advanced MySQL DBMS capabilities across **16 tables, 7 views, 10 stored routines, 11 triggers, and 1 scheduled event**.

### Tables (16)
1. `farmers`: Multi-tenant user accounts with bcrypt hashes, district, village, language (`en`, `mr`, `hi`), and role.
2. `farms`: Agricultural holdings with GPS coordinates, acreage, soil type, and irrigation system.
3. `soil_tests`: Nutrient chemistry logs (N, P, K, pH 0-14, moisture 0-100%, organic carbon).
4. `weather_records`: Daily agro-meteorological records with unique constraint on `(farm_id, record_date)`.
5. `crops`: Master catalog of crop agronomic bounds, duration days, yield expectations, and estimated cultivation costs.
6. `crop_stages`: Phenological growth stages (start day, end day) and required agronomic field tasks.
7. `crop_rotation_rules`: Agronomic succession logic defining beneficial follow-up crops and nitrogen-fixing rationale.
8. `fertilizers`: Chemical and organic fertilizer specifications with N-P-K percentages and retail prices.
9. `market_prices`: Historical APMC commodity prices with unique key on `(crop_id, district, price_date)`.
10. `translations`: Internationalization dictionary (97 text keys x English, Marathi, Hindi).
11. `predictions`: Logged recommendation scores and suitability factors.
12. `crop_cycles`: Complete crop lifecycle tracking (Planned, Growing, Harvested, Failed).
13. `expenses`: Input cost items categorized by `Seeds`, `Fertilizer`, `Pesticide`, `Labour`, `Irrigation`, `Machinery`, `Other`.
14. `crop_cycle_log`: Automated status audit trail for lifecycle transitions.
15. `alerts`: Field alerts with `dedupe_key` preventing redundant notifications.
16. `admin_audit_log`: System audit log capturing JSON before/after diffs and administrator IDs.

### Views (7)
1. `current_status_view`: Computes real-time progress percentage, days since sowing, days to harvest, current stage, pending tasks, and accumulated expenses for ongoing crops.
2. `farmer_history_view`: Aggregates financial returns (revenue, total expenses, net profit) for completed cycles.
3. `farmer_summary_view`: High-level aggregate metrics per farmer across all farms and historical harvests.
4. `crop_calendar_view`: Projects calendar milestone dates for active cycles with `Done`, `Current`, `Upcoming` status flags.
5. `latest_prices_view`: Resolves the most recent APMC market price per crop and district.
6. `cycle_expense_summary_view`: Aggregates category spending and relative percentage per cycle.
7. `crop_localized_view`: Joins crops with translations to display crop names in the user's preferred language (`crop_id`, `crop_name`, `lang`, `localized_name`).

### Stored Procedures (9) & Functions (1)
- `recommend_crops(farm_id, test_id, season)`: Multi-factor scoring engine evaluating soil and weather conditions, returning ranked suitability scores.
- `start_crop_cycle(farm_id, crop_id, prediction_id, sowing_date)`: Validates and initializes a new crop cycle with automatic harvest date calculation.
- `close_crop_cycle(cycle_id, status, yield_kg, price_per_quintal)`: Concludes a crop cycle, enforcing financial calculations and status rules.
- `recommend_fertilizer(farm_id, test_id, crop_id)`: Diagnoses soil nutrient deficits and computes commercial fertilizer dosages (Urea, DAP, MOP) and estimated cost.
- `rotation_advice(farm_id)`: Evaluates previous harvest history and identifies optimal seasonal rotation crops.
- `check_weather_alerts(farm_id, temp, rain)`: Evaluates incoming weather observations against safety thresholds.
- `generate_task_alerts(days_ahead)`: Scans all active crops and creates notifications for upcoming stage tasks.
- `estimate_crop_profit(farm_id, crop_id)`: Combines agronomic yield, university cost budgets, and APMC prices to project gross revenue, profit per acre, and monthly returns.
- `profit_for_recommendations(farm_id)`: Generates economic return projections for all recommended crops on a farm.
- `get_season(check_date)` *(Function)*: Returns agricultural season (`Kharif`, `Rabi`, `Zaid`) based on date.

### Triggers (11)
- `trg_cycle_bi` (BEFORE INSERT on `crop_cycles`): Enforces **one active cycle per farm** and auto-computes `expected_harvest`.
- `trg_cycle_ai` (AFTER INSERT on `crop_cycles`): Automatically logs cycle creation in `crop_cycle_log`.
- `trg_cycle_bu` (BEFORE UPDATE on `crop_cycles`): Prevents reopening closed cycles and sets `actual_harvest = CURDATE()`.
- `trg_cycle_au` (AFTER UPDATE on `crop_cycles`): Logs status changes in `crop_cycle_log`.
- `trg_weather_ai` (AFTER INSERT on `weather_records`): Automatically generates weather alerts on extreme rainfall (> 50mm) or heat (> 40°C).
- `trg_weather_au` (AFTER UPDATE on `weather_records`): Checks updated weather observations and raises alerts.
- `trg_market_prices_ai` (AFTER INSERT on `market_prices`): Generates price alerts and logs `INSERT` in `admin_audit_log`.
- `trg_market_prices_au` (AFTER UPDATE on `market_prices`): Detects > 10% price spikes to notify farmers and logs `UPDATE` in `admin_audit_log`.
- `trg_market_prices_ad` (AFTER DELETE on `market_prices`): Records price deletions in `admin_audit_log`.
- `trg_crops_au` (AFTER UPDATE on `crops`): Records crop catalog parameter adjustments in `admin_audit_log`.
- `trg_crops_ad` (AFTER DELETE on `crops`): Records crop catalog deletions in `admin_audit_log`.

### Scheduled Events (1)
- `ev_daily_task_alerts`: Executes `CALL generate_task_alerts(2)` every morning at 06:00:00 to alert farmers of upcoming field tasks.

---

## 📡 API Endpoints Reference

### Public Endpoints (No Authentication Required)
- `GET /`: Serves public home page (`static/index.html`) or API JSON metadata if requested via `Accept: application/json`.
- `POST /public/quick-recommend`: Instant top-3 crop recommendations without saving data:
  - Executes parameterized `CALL quick_recommend(...)` stored procedure.
  - Server-side range validation (pH 0-14, N/P/K >= 0, Temp -10 to 60°C, Humidity 0-100%, Rain >= 0).
  - Enforces IP-based rate limiting of 20 requests per minute.
  - Rounds all suitability and nutrient scores to 1 decimal place.
  - Localizes crop names to requested language (`en`, `mr`, `hi`).
  - Automatically maps procedure errors (SQLSTATE 45000) to HTTP 400 Bad Request.
- `GET /public/season`: Returns current agricultural season (via `get_season(CURDATE())`) and crops suitable for sowing now (season crops + Annual crops) with localized names.
- `GET /public/stats`: Returns aggregated platform counters (`crops_supported`, `languages_supported`, `recommendations_made`) with complete privacy protection (no personal farmer data).

### Health & Internationalization (i18n)
- `GET /health`: Comprehensive health check including database connection pool status, Devanagari translation encoding integrity status (`valid` vs `corrupted`), and count of corrupted translation entries.
- `GET /i18n/{lang}`: Multilingual dictionary (`en`, `mr`, `hi`) falling back to English for any missing keys.
- `GET /crops/localized?lang=`: List crops with localized names via `crop_localized_view`.

### Authentication & Profile
- `POST /auth/register`: Register new farmer account.
- `POST /auth/login`: Authenticate and receive JWT access token.
- `GET /me` (or `/auth/me`): Fetch profile of logged-in farmer.
- `PATCH /me/language`: Save farmer language preference in `farmers.language`.

### Geolocation & Nominatim Proxies
- `GET /geo/search?q=`: OpenStreetMap Nominatim search suggestions proxied for India (`countrycodes=in`, limit 5, in-memory caching, 1 req/sec rate limiting, proper User-Agent).
- `GET /geo/reverse?lat=&lon=`: Reverse geocoding of latitude and longitude into human-readable location labels with soft warning for coordinates outside India (expected lat 6-38, lon 68-98).
- `PATCH /me/address`: Update farmer profile's `district` and `village` directly from geocoded location.

### Farm Management
- `POST /farms`: Create a farm plot with location label, coordinates, soil type, and irrigation.
- `GET /farms`: List all farms owned by the logged-in farmer (includes `location_label`).
- `GET /farms/{farm_id}`: Fetch single farm details.
- `PUT /farms/{farm_id}`: Update farm parameters (including `location_label`).
- `DELETE /farms/{farm_id}`: Delete farm (cascades to tests, weather, cycles, expenses).

---

## 🗺️ Easy Location Selection & Geocoding

AgriPredict replaces manual latitude and longitude entry with an intuitive location selection workflow in Add/Edit Farm:
1. **Interactive Leaflet Map**: Uses OpenStreetMap tiles with attribution and a draggable pin. Clicking the map or dragging the pin updates coordinates and triggers automatic reverse-geocoding into a human-readable `location_label` (e.g. *"Pune, Maharashtra"*).
2. **"Use My Current Location"**: One-click browser geolocation (`navigator.geolocation`) with friendly error handling for permission denials, unavailable GPS, or timeouts.
3. **Village/Town/City Autocomplete Search**: Search box debounced against backend proxy `GET /geo/search?q=` with instant dropdown suggestions.
4. **Nominatim Usage Policy Compliance**: Backend proxies in `app/routers/geo.py` enforce strict compliance with OpenStreetMap's Nominatim usage policy:
   - Custom User-Agent header with contact info (`AgriPredict/1.0 (contact: admin@agripredict.in)`).
   - Thread-safe rate limiting ensuring a maximum of 1 request per second.
   - In-memory result caching for both search queries and reverse-geocoded coordinates.
   - Geographically restricted to India (`countrycodes=in`, limit 5).
5. **Read-Only Auto-Filled Coordinates with Manual Toggle**: Latitude and longitude fields are auto-filled and read-only by default, with an *"Enter coordinates manually"* toggle allowing direct numerical adjustments.
6. **India Bounds Validation & Soft Warning**: Validates coordinates and presents a soft warning banner if selected coordinates fall outside India's standard boundary (lat 6–38, lon 68–98).
7. **Farm Card Display**: Shows `location_label` prominently on each farm card, keeping raw GPS coordinates as small secondary text. Existing legacy farms without a label gracefully fallback to displaying GPS.
8. **Profile Address Autofill Prompt**: If the farmer's registered profile lacks a district or village, the modal detects candidate values from the geocoded address and offers a 1-click prompt to save them to their profile (`PATCH /me/address`).

---

## 🧪 Running Automated Tests

Run the complete test suite (71 automated tests covering all phases, security models, bug fixes, location selection, and i18n features):

```bash
.venv\Scripts\pytest -v
```

### Test Coverage Highlights:
- **`test_geo_and_location.py`** (10 tests): OpenStreetMap Nominatim search and reverse geocode proxies with mocked HTTP, in-memory result caching, rate limiting, India bounds validation and soft warnings, global coordinate rejection, farm `location_label` persistence across CRUD operations, and `PATCH /me/address` profile updates.
- **`test_auth_and_farms.py`** (13 tests): Farmer registration, login via phone or email, JWT validation, admin role checks, and farm ownership isolation.
- **`test_bugfixes.py`** (4 tests): Wheat crop calendar (5 growth stages, 1 Current stage), harvest date calculation on status cards, fertilizer advice for low-NPK soil, protected page redirects when unauthenticated, safe `next` redirection with external URL rejection, and recommendation score 1-decimal rounding.
- **`test_create_admin.py`** (2 tests): Interactive prompts and non-interactive CLI flags for admin creation.
- **`test_phase2_soil_weather_recommend.py`** (8 tests): Soil test CRUD, Open-Meteo weather caching and upserts, and crop recommendation stored procedure execution.
- **`test_phase3_dashboard_cycles.py`** (8 tests): Crop cycle lifecycle, one active cycle trigger enforcement, expenses CRUD, close cycle flow, and audit trail logging.
- **`test_phase4_advisory_alerts.py`** (11 tests): Fertilizer dosage calculation, succession rotation rules, crop calendar timelines, and automated trigger weather alerts with `dedupe_key`.
- **`test_phase5_market_admin.py`** (9 tests): Admin RBAC, master catalog CRUD, HTTP 409 conflict protection, trigger-based audit logging with `@app_user`, and CSV bulk price upload.
- **`test_phase6_security_i18n.py`** (6 tests): Health endpoint check, `GET /i18n/{lang}` dictionary with English fallback, `PATCH /me/language` persistence, invalid language rejection, and `GET /crops/localized` using `crop_localized_view`.

### Soil & Weather Telemetry
- `POST /farms/{farm_id}/soil-tests`: Record soil test (N, P, K, pH 0-14, moisture 0-100%, organic carbon).
- `GET /farms/{farm_id}/soil-tests`: List soil tests (newest first).
- `DELETE /soil-tests/{test_id}`: Delete soil test.
- `POST /farms/{farm_id}/weather/refresh`: Sync last 30 days from Open-Meteo API.
- `GET /farms/{farm_id}/weather`: Retrieve cached weather records.

### Crop Recommendations & Advisory
- `POST /farms/{farm_id}/recommend`: Generate top-3 crop recommendations (`CALL recommend_crops`).
- `GET /farms/{farm_id}/predictions`: Retrieve past recommendation history.
- `POST /farms/{farm_id}/fertilizer-advice`: Nutrient deficit diagnosis & dosage plan (`CALL recommend_fertilizer`).
- `GET /farms/{farm_id}/rotation-advice`: Succession crop guidance (`CALL rotation_advice`).
- `GET /cycles/{cycle_id}/calendar`: Milestone growth timeline from `crop_calendar_view`.

### Dashboard & Financial Tracking
- `GET /dashboard/summary`: Single row from `farmer_summary_view`.
- `GET /dashboard/current`: All ongoing crops from `current_status_view`.
- `GET /dashboard/history`: Completed crops from `farmer_history_view` with pagination.
- `GET /dashboard/expenses-by-category`: Aggregated spending across all cycles.

### Crop Cycles & Input Expenses
- `POST /farms/{farm_id}/cycles`: Start crop cycle (`CALL start_crop_cycle`).
- `GET /cycles/{cycle_id}`: Get detailed cycle metrics.
- `POST /cycles/{cycle_id}/close`: Conclude cycle (`CALL close_crop_cycle`).
- `GET /cycles/{cycle_id}/log`: Audit trail from `crop_cycle_log`.
- `POST /cycles/{cycle_id}/expenses`: Log expenditure (`Seeds`, `Fertilizer`, `Labour`, etc.).
- `GET /cycles/{cycle_id}/expenses`: List cycle expenses.
- `DELETE /expenses/{expense_id}`: Delete an expense entry.
- `GET /cycles/{cycle_id}/expense-summary`: Summary breakdown from `cycle_expense_summary_view`.

### Alerts & Notifications
- `GET /alerts`: View farmer alerts (`?unread=true` filter supported).
- `GET /alerts/unread-count`: Number of unread alerts for navbar badge.
- `PATCH /alerts/{alert_id}/read`: Mark alert as read.
- `POST /alerts/read-all`: Mark all alerts as read.

### Market Prices & Economics
- `GET /prices`: Current APMC rates from `latest_prices_view` (filter by `crop_id`, `district`).
- `GET /prices/history`: 90-day price trend history for charting.
- `GET /farms/{farm_id}/profit-estimates`: Economic forecast for recommended crops (`CALL profit_for_recommendations`).
- `GET /farms/{farm_id}/crops/{crop_id}/profit`: Single crop economics (`CALL estimate_crop_profit`).

### Administrator Endpoints (`require_admin`)
- `GET, POST, PUT, DELETE /admin/crops`: Master crop catalog CRUD.
- `GET, POST, PUT, DELETE /admin/crop-stages`: Phenological growth stage CRUD.
- `GET, POST, PUT, DELETE /admin/fertilizers`: Fertilizer specifications CRUD.
- `GET, POST, PUT, DELETE /admin/rotation-rules`: Succession rules CRUD.
- `POST /admin/market-prices`: Single APMC price upsert.
- `POST /admin/market-prices/upload-csv`: Bulk CSV price upload with error report.
- `GET /admin/audit-log`: System audit trail with JSON diffs.
- `GET /admin/users`: Registered user listing.
- `PATCH /admin/users/{farmer_id}/active`: Enable/disable account access.
- `POST /admin/run-task-alerts`: Manually trigger task alerts procedure.

---

## 💾 Backup and Restore Guide

AgriPredict provides automated scripts to create complete database dumps (including tables, views, stored procedures, functions, triggers, and scheduled events) with UTF-8 character encoding to preserve Marathi and Hindi text.

### Creating a Backup
**On Windows (PowerShell):**
```powershell
# Set root password in session
$env:DB_PASSWORD = "your_mysql_password"

# Run automated backup (dumps, compresses to .zip, verifies integrity)
.\backup_agripredict.ps1
```

**On Linux / macOS (Bash):**
```bash
export DB_PASSWORD="your_mysql_password"
chmod +x backup_agripredict.sh
./backup_agripredict.sh
```

### Restoring from Backup
```bash
# Decompress the zip file if needed, then restore via MySQL CLI:
mysql -u root -p agripredict < backups/agripredict_YYYYMMDD_HHMMSS.sql
```

---



## ⚠️ Known Limitations

1. **Seed Data Is Approximate**: Crop ideal ranges, duration days, average yields, cultivation costs, and APMC prices are starter reference values, not agronomically verified regional budgets.
2. **Recommender Is Rule-Based**: The recommendation procedure calculates closeness to target ranges using weighted score formulas. It is not an ML model trained on historical yield outcomes.
3. **Fertilizer Dosages Are Indicative**: The procedure treats nutrient gaps as simple kg/ha targets. In real-world farming, local Agricultural Department and Krishi Vigyan Kendra (KVK) soil health card guidelines should always take precedence.
4. **Weather Telemetry Uses Historical Averages**: Recommender input utilizes the 30-day historical mean from Open-Meteo rather than long-range seasonal forecasts.
5. **One Active Crop Per Farm**: The `trg_cycle_bi` trigger restricts each farm to one active cycle at a time. Intercropping or multi-plot farming must be modeled as separate farm records.
6. **Scheduled Event Requirements**: The daily background reminder event requires the MySQL event scheduler to be enabled (`SET GLOBAL event_scheduler = ON;`).
7. **Production Scope**: Production features such as phone SMS OTP verification, payment gateway integration, and database replication are beyond the scope of this DBMS capstone project.
