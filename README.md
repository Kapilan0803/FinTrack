# FinTrack - Modern Loan Collection & Recovery Platform

A cloud-based, mobile-first Loan Collection & Lending Management SaaS platform designed for Indian NBFCs, chit funds, microfinance firms, and private lenders.

---

## 🌟 Key Features

1. **Multi-Tenancy & Data Isolation**:
   - Every lending business is an isolated `Company` tenant.
   - Strict tenant separation: users, borrowers, loans, and collections are protected from cross-tenant access.

2. **Supported Loan Models**:
   - **Daily Collection Loans**: 50 or 100 days; automatically skips Sundays if enabled.
   - **Weekly Collection Loans**: 10, 15, or 20 weeks.
   - **Monthly EMI Loans**: Equal monthly amortized installments.
   - **Monthly Interest Loans**: Bullet principal on final maturity, interest paid monthly.
   - **Weekly Interest Loans**: Bullet principal on final maturity, interest paid weekly.
   - **Mathematical Exactness**: All calculations use Python's `Decimal` with final installment absorbing penny rounding discrepancies (`sum(installments) == total_amount` down to the exact paisa).

3. **Field Agent "Today's Collection" Sheet (Mobile-First UX)**:
   - Optimized for field agents under direct sunlight on any smartphone.
   - **1-Tap Quick Pay**: HTMX-powered instant mark as PAID without page reloads.
   - **Modal for Custom / UPI / Advance**: Allows partial repayments, advance installments, UPI UTR numbers, and collection notes.
   - **Thermal Receipt (58mm/80mm)**: Bluetooth printer format receipt for on-the-spot printing.
   - **WhatsApp Receipt Sharing**: 1-click sharing pre-filled receipt to borrower's WhatsApp.

4. **Automated Risk & Reporting**:
   - **Executive Dashboard**: Today's collected, expected, pending, 7-day trend bar chart, and active portfolio stats.
   - **Daily Collection Register**: Auditable log with filters by agent, date, and payment mode.
   - **Excel Export**: Formatted `.xlsx` report using `openpyxl` with styled headers and totals.
   - **PDF Export**: Clean printable PDF via `xhtml2pdf`.
   - **Overdue Defaulters Aging**: Visual breakdown by 1-7 days, 8-30 days, and 30+ days overdue.
   - **Celery Automation**: Daily 00:05 AM task marks missed payments `OVERDUE` and computes late penalty fees.

5. **Subscription & Billing**:
   - 30-day full-feature free trial upon company registration (no credit card required).
   - Automated `SubscriptionLockMiddleware` that locks account access once trial expires while keeping billing screens accessible.
   - Razorpay subscription integration (₹1,000 / year + 18% GST = ₹1,180).
   - Automatic GST invoice generation.

6. **Marketing Website**:
   - Modern Emerald & Deep Slate design.
   - Live interactive EMI & daily collection calculator.
   - 4-step workflow, testimonials, FAQ accordion, and demo request form.
   - DPDP Act (Digital Personal Data Protection Act 2023) compliant privacy policy.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Virtual environment (`.venv`)

### 2. Run the Development Server
```bash
# Clone the repository and enter the directory
git clone <your-repo-url> fintrack
cd fintrack

# Activate virtual environment and run server
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```
Open your browser at: **`http://127.0.0.1:8000/`**

### 3. Demo Credentials
The database has already been seeded with realistic test data:

- **Owner / Admin Login**:
  - URL: `http://127.0.0.1:8000/accounts/login/`
  - Username: **`owner`**
  - Password: **`password123`**

- **Field Collection Agent Login**:
  - Username: **`agent_kannan`**
  - Password: **`password123`**

### 4. Running Automated Tests
```powershell
.venv\Scripts\python.exe manage.py test
```

### 5. Running Scheduled Celery Tasks (Production)
```powershell
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```
*(In local development, `CELERY_TASK_ALWAYS_EAGER = True` is enabled in `.env` so tasks execute synchronously without needing a running Redis server).*

---

## 📁 Directory Structure
```
fintrack/
├── manage.py                # Root management CLI (auto-discovers backend)
├── requirements.txt         # Python dependencies
├── .env / .env.example      # Environment secrets & configuration
├── db.sqlite3               # SQLite database
│
├── frontend/                # Presentation Layer & UI Assets
│   ├── templates/           # Clean Tailwind CSS + HTMX templates
│   │   ├── accounts/        # Auth, team, profile templates
│   │   ├── billing/         # Pricing, checkout, invoices
│   │   ├── collections/     # Field collection sheets, receipts
│   │   ├── components/      # Reusable UI widgets & stat cards
│   │   ├── loans/           # Loan origination & schedules
│   │   ├── members/         # Borrower directories & KYC
│   │   ├── reports/         # Dashboard, Excel & PDF templates
│   │   ├── website/         # Landing pages, terms, privacy
│   │   ├── base.html        # App shell (Tailwind, HTMX, Lucide)
│   │   └── app_base.html    # Navigation sidebar layout
│   ├── static/              # CSS, JS, and image assets
│   └── README.md            # Frontend documentation
│
└── backend/                 # Application Core & Business Logic
    ├── config/              # Split settings, Celery, and master URLs
    ├── accounts/            # Company multi-tenancy, custom User, roles, trial guard
    ├── members/             # Customer directory, Aadhaar/KYC, route assignment
    ├── loans/               # Loan plans, amortized schedule engine (0-paisa rounding)
    ├── loan_collections/    # 1-Tap collection sheet, thermal receipts, WhatsApp links
    ├── reports/             # Analytics dashboard, Excel (openpyxl) and PDF export
    ├── billing/             # 30-day trial lock, Razorpay checkout, GST invoices
    ├── website/             # Public landing page, interactive calculator, FAQ, demo
    ├── manage.py            # Local backend management utility
    └── README.md            # Backend documentation
```
