import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from config import TestingConfig
from models.database import db
from models.models import Admin, Pharmacy, Medicine, PharmacyInventory
from werkzeug.security import generate_password_hash
from datetime import date, timedelta

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        
        # Seed test admin & pharmacy
        admin = Admin(
            username="test_admin",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(admin)
        db.session.flush()

        pharmacy = Pharmacy(
            admin_id=admin.admin_id,
            shop_name="Rural Health Pharmacy",
            owner_name="Dr. Tester",
            address="123 Village Road, Salem, Tamil Nadu",
            phone="9876543210",
            latitude=11.6643,
            longitude=78.1460,
            distance_km=2.5
        )
        db.session.add(pharmacy)
        db.session.flush()

        # Seed test medicines
        med1 = Medicine(
            medicine_name="Dolo 650",
            generic_name="Paracetamol 650 mg",
            medicine_type="Tablet",
            category="Pain & Fever",
            uses="Fever, headache, and body aches",
            purpose="Analgesic and antipyretic",
            how_to_use="Take 1 tablet after meals with water as advised."
        )
        med2 = Medicine(
            medicine_name="Cetirizine 10 mg",
            generic_name="Cetirizine",
            medicine_type="Tablet",
            category="Cold & Allergy",
            uses="Allergic rhinitis, sneezing, and itching",
            purpose="Antihistamine",
            how_to_use="Take 1 tablet at night."
        )
        db.session.add_all([med1, med2])
        db.session.flush()

        # Seed test inventories
        inv1 = PharmacyInventory(
            pharmacy_id=pharmacy.pharmacy_id,
            medicine_id=med1.medicine_id,
            price=30.00,
            stock_quantity=50,
            expiry_date=date.today() + timedelta(days=180),
            is_active=True
        )
        inv2 = PharmacyInventory(
            pharmacy_id=pharmacy.pharmacy_id,
            medicine_id=med2.medicine_id,
            price=18.50,
            stock_quantity=5, # low stock for alert testing
            expiry_date=date.today() + timedelta(days=15), # expiring soon
            is_active=True
        )
        db.session.add_all([inv1, inv2])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess['admin_id'] = 1
        sess['username'] = 'test_admin'
        sess['pharmacy_id'] = 1
        sess['shop_name'] = 'Rural Health Pharmacy'
        sess['owner_name'] = 'Dr. Tester'
    return client
