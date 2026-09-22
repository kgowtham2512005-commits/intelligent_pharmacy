# RuralCare AI – Intelligent Pharmacy Assistance System

RuralCare AI is an intelligent pharmacy assistance web application bridging healthcare access for rural communities by connecting patients and customers with local medical shops and pharmacies.

## 🚀 Key Highlights & Features

- 🏥 **Customer Medicine Search & Price Comparison**: Instant medicine search by brand or generic salt, transparent price comparison, and stock verification across rural medical shops.
- 📍 **Real-time Geolocation & Distance Calculation**: Haversine formula calculation computing distance between user location and pharmacies, with sorting by lowest price, nearest pharmacy, or stock level.
- 🎙️ **Conversational Voice Assistant & Multi-Language Support**: Voice search and interactive health assistant supporting English, Tamil (தமிழ்), and Hindi (हिंदी) via Web Speech API (STT & TTS) with offline NLP intent & symptom matching.
- 💊 **Intelligent Recommendations & Generic Alternatives**: Automated discovery of equivalent generic substitutes and symptom-based medicine suggestions.
- 🔔 **Smart Alerts & Expiry Tracking**: Real-time admin inventory alerts for low-stock, out-of-stock, and medicines expiring within 30 days.
- 📊 **Visual Analytics Dashboard**: Interactive Chart.js graphs displaying pharmacy stock distribution and medicine category breakdown.
- 🛡️ **Multi-Pharmacy Isolation & Security**: Werkzeug secure password hashing (PBKDF2/Scrypt), session isolation, HTTP-only cookies, SQL injection prevention via ORM, and full role-based access control.
- 🌐 **Master Administration Portal**: System-wide oversight and direct management of all registered pharmacies, global medicine catalog, and cross-store inventory.
- ☁️ **Production & Cloud Ready**: WSGI standard `wsgi.py`, `Procfile`, connection pooling with `pool_pre_ping`, health check endpoint `/health`, and auto-fallback between MySQL and SQLite.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ / 3.13, Flask 3.1, Flask-SQLAlchemy 3.1, Werkzeug
- **WSGI Server**: Gunicorn
- **Database**: MySQL 8.0 / PostgreSQL (via `DATABASE_URL`) / SQLite fallback
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons
- **Audio & Speech**: Web Speech API (SpeechRecognition & SpeechSynthesis)
- **Charts & Data Viz**: Chart.js 4.4
- **Testing**: Pytest 8.0+

---

## 📁 Project Structure

```
ruralcare-ai/
│
├── app.py                      # Flask application factory & route registration
├── config.py                   # Environment & database configuration (MySQL/Postgres/SQLite)
├── wsgi.py                     # Production WSGI entry point for Gunicorn
├── Procfile                    # Deployment process configuration (Render/Heroku/Railway)
├── runtime.txt                 # Python runtime version
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── init_db.py                  # Database & tables initialization script
├── import_dataset.py           # Dataset importer & sample seeder
├── dataset.txt                 # Initial rural pharmacy catalog dataset
├── ruralcare_ai.db             # Pre-configured local SQLite database
├── .env                        # Local environment variables
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── models/
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy db instance
│   └── models.py               # Admin, Pharmacy, Medicine, PharmacyInventory models
│
├── routes/
│   ├── __init__.py
│   ├── user_routes.py          # Customer search, detail & comparison routes
│   ├── admin_routes.py         # Admin auth, dashboard, inventory & master portal
│   ├── voice_routes.py         # Conversational voice assistant & recommendation APIs
│   └── alerts_routes.py        # Expiry & low stock smart alerts APIs
│
├── services/
│   ├── location_service.py     # Haversine distance calculator
│   ├── recommendation_service.py # Generic alternatives & alert calculation logic
│   └── voice_service.py        # Voice NLP, intent classifier & multi-language engine
│
├── templates/
│   ├── base.html               # Master layout, navbar, voice widget & footer
│   ├── index.html              # Customer homepage with voice search & results
│   ├── user/
│   │   └── medicine_detail.html # Result page with Price Comparison & Speech Readout
│   ├── admin/
│   │   ├── register.html       # Pharmacy admin registration
│   │   ├── login.html          # Secure admin login
│   │   ├── dashboard.html      # Dynamic stats, charts & alerts
│   │   ├── medicines.html      # Inventory table with search, filter & modal
│   │   ├── add_medicine.html   # Add medicine form
│   │   ├── edit_medicine.html  # Edit medicine & inventory properties
│   │   ├── master_dashboard.html # Super admin system-wide manager
│   │   ├── master_edit_pharmacy.html # Master pharmacy editor
│   │   └── master_edit_medicine.html # Master medicine editor
│   └── errors/
│       ├── 404.html            # Custom 404 page
│       └── 500.html            # Custom 500 page
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern design system & responsive styling
│   └── js/
│       ├── main.js             # Form validation & notifications
│       ├── user_search.js      # Geolocation, autocomplete & voice search
│       └── voice_assistant.js  # Conversational voice assistant UI & STT/TTS
│
└── tests/
    ├── conftest.py             # Pytest fixtures & in-memory test DB
    └── test_all.py             # Full automated test suite (32 tests)
```

---

## 🚀 Getting Started Locally

### 1. Clone & Setup Virtual Environment

```bash
# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and configure your settings:
```env
SECRET_KEY=your_strong_secret_key_here
DB_TYPE=auto
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=ruralcare_ai
```
*(Note: If MySQL is not running, the system will automatically fall back to the built-in SQLite database seamlessly.)*

### 4. Initialize Database & Seed Sample Data

```bash
python init_db.py
```

### 5. Run the Application

```bash
python app.py
```
Open `http://127.0.0.1:5000` in your web browser.

---

## 🧪 Running Automated Tests

Run the full automated test suite with pytest:

```bash
pytest -v
```

All 32 test cases cover:
- Health check & landing pages
- Medicine search API, autocomplete & pagination
- Geolocation distance calculation & sorting
- Voice Assistant intent classification, STT/TTS & multi-language responses
- Smart alerts (expiry tracking & low-stock warnings)
- Admin registration, secure login, password hashing & session management
- Inventory CRUD operations & status toggling
- Master Administration system-wide management
- Error handlers (404 / 500)

---

## ☁️ Deployment Guide

### Deployment on Render / Railway / Heroku

1. **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start Command**:
   ```bash
   gunicorn wsgi:app
   ```
3. **Environment Variables**:
   - `SECRET_KEY`: Set to a strong random string
   - `DATABASE_URL`: Set to your PostgreSQL or MySQL cloud URI (e.g., from Neon, Supabase, Railway MySQL, or Render Postgres)
   - `PORT`: Automatically assigned by the host

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
```

---

## 🔒 Security & Medical Disclaimer

- **Security**: Passwords hashed using PBKDF2 with SHA-256 / Scrypt, session cookies protected with `HttpOnly` and `SameSite=Lax`, SQL injection prevented via SQLAlchemy parameterized queries.
- **Medical Disclaimer**: RuralCare AI is an informational pharmacy-assistance system. Information provided is for educational reference only and does not constitute medical advice, diagnosis, or auto-prescriptions. Always consult a certified doctor or licensed pharmacist for medical advice.
