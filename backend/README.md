# FinTrack Backend

This folder contains the core Django backend, domain models, services, tasks, and business logic for FinTrack.

## Directory Structure

```
backend/
├── config/                # Central Django settings, routing, ASGI/WSGI, Celery configuration
│   ├── settings/          # Environment-specific settings (base, development, production)
│   ├── urls.py            # Master URL dispatcher
│   ├── celery.py          # Asynchronous task queue runner
│   ├── wsgi.py            # Production WSGI web server hook
│   └── asgi.py            # Asynchronous gateway interface
├── accounts/              # Multi-tenant organization isolation, authentication & staff roles
├── billing/               # Razorpay payment gateway integration, subscription plans & invoices
├── loans/                 # Flat-rate & amortized loan schedules, plans, exact-paisa calculator
├── loan_collections/      # 1-Tap collection engine, late fee penalties, cash denomination closing
├── members/               # Borrower profiles, KYC document attachments, route sequencing
├── reports/               # Executive dashboard, agent targets, Excel & PDF exporter services
├── website/               # Landing pages and demo inquiry request capture
└── manage.py              # Backend administrative utility
```

## Running Commands

You can run Django management commands either from the project root:
```bash
python manage.py runserver
python manage.py test
python manage.py makemigrations
python manage.py migrate
```

Or from within the `backend/` directory:
```bash
cd backend
python manage.py runserver
```
