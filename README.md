# RuralCare AI – Intelligent Pharmacy Assistance System

RuralCare AI is an intelligent pharmacy assistance web application connecting rural communities with local medical shops and pharmacies.

## Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons
- **Backend**: Python Flask 3.1
- **Database**: MySQL 8.0 (with Flask-SQLAlchemy & PyMySQL ORM) / SQLite fallback
- **Security**: Werkzeug password hashing (PBKDF2/Scrypt), Parameterized SQL queries, Session isolation, Input validation.

---

## Project Structure
```
ruralcare-ai/
│
├── app.py                  # Main Flask application entry point & factory
├── config.py               # Environment configuration settings
├── init_db.py              # MySQL database & tables initializer
├── requirements.txt        # Python package dependencies
├── .env                    # Environment variables (DB credentials, secret key)
├── .env.example            # Environment variables template
├── .gitignore              # Git ignored files
│
├── models/
│   ├── __init__.py
│   ├── database.py         # SQLAlchemy instance definition
│   └── models.py           # Admin, Pharmacy, Medicine, PharmacyInventory ORM models
│
├── routes/
│   ├── __init__.py
│   ├── user_routes.py      # Customer homepage, search API, & medicine detail routes
│   └── admin_routes.py     # Admin registration, login, dashboard, & inventory routes
│
├── services/
│   └── location_service.py # Haversine geolocation distance calculation
│
├── templates/
│   ├── base.html           # Base layout with navbar, alerts, & footer
│   ├── index.html          # Customer homepage with search bar & autocomplete
│   ├── user/
│   │   └── medicine_detail.html # Result page with Price Comparison & Nearby Pharmacies
│   └── admin/
│       ├── register.html   # Admin & Pharmacy registration form
│       ├── login.html      # Secure admin login form
│       ├── dashboard.html  # Protected admin dashboard with dynamic stats
│       ├── medicines.html  # Inventory UI with Search, Filter & Sort
│       ├── add_medicine.html # Add Medicine form
│       └── edit_medicine.html # Edit Medicine form
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom design system & glassmorphic styling
│   └── js/
│       ├── main.js         # General client-side validation & interactivity
│       └── user_search.js  # Geolocation, Web Speech API voice search 🎤, & autocomplete
│
└── README.md               # Project documentation & setup instructions
```

---

## Implemented Features (Phases 1–12)

- **Phase 1 — Setup & Landing Page**: Flask app structure, Bootstrap 5 base layout, dual role entry points (Customer & Pharmacy Admin).
- **Phase 2 — Database Design**: Relational MySQL schema with primary keys, foreign keys, unique constraints, and dynamic status property.
- **Phase 3 — Registration**: Validation, unique username check (`"Username already exists. Please choose another username."`), Werkzeug password hashing, atomic admin + pharmacy creation.
- **Phase 4 — Authentication**: Secure login, session management, `@admin_required` protection decorator, logout, and multi-pharmacy isolation.
- **Phase 5 — Dynamic Dashboard**: Pharmacy-specific statistics cards (Total, Available, Out-of-Stock, Inactive/Expired) and recently updated items table.
- **Phase 6 — Add Medicine & Master Catalog Deduplication**: Form validation, master medicine lookup by name (prevents duplicate catalog entries), and inventory record linkage.
- **Phase 7 — Edit & Safe Deactivation**: Full medicine & inventory editor, quick price & stock update modal, and safe toggle activation/deactivation (`is_active`).
- **Phase 8 — Inventory UI**: Search medicines, filter by status, sort by name/price/stock/update time, quick update modals, and confirmation dialogs.
- **Phase 9 — Customer Homepage**: "Find Medicines Near You" search component, Web Speech API voice search microphone button 🎤, popular search chips, and location status badge.
- **Phase 10 — Medicine Search REST API**: `GET /api/medicines/search?q=<query>`, partial/case-insensitive search matching brand & generic names, return clean `"Medicine not found."` on invalid search without crashing.
- **Phase 11 — Nearby Pharmacy Search**: Displays pharmacy details (Name, Owner, Address, Phone, Price, Stock Status), calculates distance in km via Haversine formula, fallback for denied location permission.
- **Phase 12 — Price Comparison & Result Page**: `/medicine/<medicine_id>` page with Medicine Header, **Lowest Available Price Highlight** (`"Lowest available price: ₹15"` calculated ONLY over available stock), and sorting by Lowest Price, Nearest Pharmacy, or Availability.

---

## REST APIs Created

1. **`GET /api/medicines/search?q=<query>&lat=<lat>&lng=<lng>`**
   - Returns matching medicines with brand name, generic name, category, uses, available pharmacy count, and lowest price.
2. **`GET /search?q=<query>`**
   - HTML search results page.
3. **`GET /medicine/<int:medicine_id>?lat=<lat>&lng=<lng>&sort=<sort_by>`**
   - Result page displaying medicine details, price comparison, and nearby pharmacy stock.

---

## How to Run the Project

1. **Configure Environment Variables** in `.env`:
   ```env
   SECRET_KEY=ruralcare-ai-super-secret-key-2026
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DB=ruralcare_ai
   ```

2. **Initialize Database**:
   ```bash
   py init_db.py
   ```

3. **Run Flask Application**:
   ```bash
   py app.py
   ```
   Open your browser at `http://localhost:5000`.

---

## Automated Test Suites

- **Phases 1–4 Test Suite**: `py scratch/test_app.py` -> **PASSED**
- **Phases 5–8 Test Suite**: `py scratch/test_phase5_8.py` -> **PASSED**
- **Phases 9–12 Test Suite**: `py scratch/test_phase9_12.py` -> **PASSED**
