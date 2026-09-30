# FinTrack Frontend

This folder contains all user interface and presentation files for FinTrack.

## Directory Structure

```
frontend/
├── static/                 # Static assets (CSS, JavaScript, Images, Fonts)
│   ├── css/               # Custom stylesheets (Tailwind config & overrides)
│   ├── js/                # Client-side scripts and helpers
│   └── images/            # Brand logos and iconography
│       ├── fintrack-wallet-badge.png     # Ultra-HD 1024x1024 rounded squircle wallet badge
│       ├── fintrack-wallet-1024.jpg      # Master 1024x1024 high-resolution artwork
│       ├── fintrack-icon.png             # Official 512x512 app & navbar emblem
│       ├── fintrack-logo.png             # Horizontal FinTrack banner logo
│       ├── fintrack-logo-transparent.png # Transparent horizontal logo
│       ├── favicon.ico                   # Browser tab favicon (multi-resolution)
│       ├── favicon-32x32.png             # 32x32 tab icon
│       └── favicon-192x192.png           # 192x192 PWA / mobile touch icon
└── templates/              # Server-side rendered HTML templates
    ├── accounts/          # Login, Sign Up, Profile, Team Management
    ├── billing/           # Pricing plans, Checkout, Invoices
    ├── collections/       # Daily collection registers, 1-tap quick pay, receipts
    ├── components/        # Reusable partials (stat cards, modals, tables)
    ├── loans/             # Loan origination, Repayment schedules, Loan plans
    ├── members/           # Customer management, Route ordering, KYC
    ├── reports/           # Financial dashboards, Daily digest, PDF/Excel templates
    │   └── pdf/           # Printable thermal / A4 PDF collection sheets
    ├── website/           # Public marketing landing pages, Terms & Privacy
    ├── base.html          # Base layout (Tailwind CSS CDN, HTMX, Lucide Icons)
    └── app_base.html      # Authenticated application shell & navigation sidebar
```

## Technologies Used
- **HTML5 & Django Template Language (DTL)**
- **Tailwind CSS** (via CDN with customized dark/light mode color tokens)
- **HTMX** (for dynamic SPA-like partial swaps without full page reloads)
- **Lucide Icons** (lightweight modern iconography)
