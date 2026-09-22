import json
import pytest
from services.location_service import calculate_distance
from services.recommendation_service import find_alternatives, get_expiry_alerts, get_low_stock_alerts
from services.voice_service import classify_intent

# 1. Health & Landing Tests
def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'RuralCare AI'

def test_landing_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"RuralCare" in response.data
    assert b"Find Medicines" in response.data

# 2. Customer Search API & Page Tests
def test_search_api_with_query(client):
    response = client.get('/api/medicines/search?q=Dolo')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) >= 1
    assert data['results'][0]['medicine_name'] == 'Dolo 650'
    assert data['results'][0]['lowest_price'] == 30.00

def test_search_api_empty_query(client):
    response = client.get('/api/medicines/search?q=')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 0

def test_search_api_not_found(client):
    response = client.get('/api/medicines/search?q=NonExistentMedicine999')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 0
    assert "not found" in data['message'].lower()

def test_search_page(client):
    response = client.get('/search?q=Cetirizine')
    assert response.status_code == 200
    assert b"Cetirizine" in response.data

def test_medicine_detail_page(client):
    response = client.get('/medicine/1')
    assert response.status_code == 200
    assert b"Dolo 650" in response.data
    assert b"Rural Health Pharmacy" in response.data

def test_medicine_detail_with_geolocation(client):
    # Pass user lat/lng (Salem downtown)
    response = client.get('/medicine/1?lat=11.6600&lng=78.1400&sort=distance')
    assert response.status_code == 200
    assert b"Dolo 650" in response.data

def test_medicine_detail_404(client):
    response = client.get('/medicine/9999')
    assert response.status_code == 404
    assert b"404" in response.data

# 3. Voice Assistant API Tests
def test_voice_query_greeting(client):
    response = client.post('/api/voice/query', json={'query': 'Hello', 'lang': 'en'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['intent'] == 'greeting'
    assert "RuralCare AI" in data['spoken_response']

def test_voice_query_symptom(client):
    response = client.post('/api/voice/query', json={'query': 'I have a severe headache and fever', 'lang': 'en'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['intent'] in ('symptom_search', 'medicine_search')
    assert len(data['results']) > 0

def test_voice_query_empty(client):
    response = client.post('/api/voice/query', json={'query': ''})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'

def test_voice_symptom_map(client):
    response = client.get('/api/voice/symptom-map')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'Pain & Fever' in data['categories']
    assert 'fever' in data['full_map']

def test_recommendations_endpoint(client):
    response = client.get('/api/recommendations?symptom=headache')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['recommendations']) > 0

# 4. Smart Alerts API Tests
def test_alerts_summary(client):
    response = client.get('/api/alerts/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['total_alerts'] >= 1
    assert data['low_stock_count'] >= 1

def test_alerts_expiry(client):
    response = client.get('/api/alerts/expiry?days=30')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['count'] >= 1

def test_alerts_low_stock(client):
    response = client.get('/api/alerts/low-stock?threshold=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['count'] >= 1

# 5. Authentication & Authorization Tests
def test_admin_login_success(client):
    response = client.post('/admin/login', data={
        'username': 'test_admin',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b"Dashboard" in response.data

def test_admin_login_invalid(client):
    response = client.post('/admin/login', data={
        'username': 'test_admin',
        'password': 'wrong_password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_admin_register_flow(client):
    response = client.post('/admin/register', data={
        'shop_name': 'New Rural Meds',
        'owner_name': 'Alice Smith',
        'username': 'alice_pharm',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
        'address': 'Main Bazaar Road, Village',
        'phone': '9123456780'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful" in response.data

def test_admin_register_validation_error(client):
    response = client.post('/admin/register', data={
        'shop_name': '',
        'owner_name': 'Alice Smith',
        'username': 'al',
        'password': '123',
        'confirm_password': '456',
        'address': '',
        'phone': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Shop Name is required" in response.data

def test_admin_protected_route_without_login(client):
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in" in response.data

# 6. Admin Inventory Operations
def test_admin_dashboard_authenticated(auth_client):
    response = auth_client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b"Rural Health Pharmacy" in response.data

def test_admin_medicines_authenticated(auth_client):
    response = auth_client.get('/admin/medicines')
    assert response.status_code == 200
    assert b"Dolo 650" in response.data

def test_admin_add_medicine(auth_client):
    response = auth_client.post('/admin/medicines/add', data={
        'medicine_name': 'Amoxicillin 500 mg',
        'generic_name': 'Amoxicillin',
        'category': 'Antibiotic',
        'medicine_type': 'Capsule',
        'uses': 'Bacterial infections',
        'purpose': 'Antibacterial',
        'how_to_use': 'Take 1 capsule every 8 hours.',
        'price': '45.00',
        'stock_quantity': '100',
        'expiry_date': '2027-12-31'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Amoxicillin 500 mg" in response.data

def test_admin_quick_update(auth_client):
    response = auth_client.post('/admin/medicines/1/quick-update', data={
        'price': '32.50',
        'stock_quantity': '75'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated price" in response.data

def test_admin_toggle_status(auth_client):
    response = auth_client.post('/admin/medicines/1/toggle-status', follow_redirects=True)
    assert response.status_code == 200
    assert b"deactivated" in response.data

# 7. Master Admin Operations
def test_master_dashboard(auth_client):
    response = auth_client.get('/admin/master')
    assert response.status_code == 200
    assert b"Master Administration Portal" in response.data
    assert b"All Pharmacies" in response.data

def test_master_edit_pharmacy(auth_client):
    response = auth_client.post('/admin/master/pharmacy/1/edit', data={
        'shop_name': 'Rural Health Pharmacy Updated',
        'owner_name': 'Dr. Tester Senior',
        'phone': '9876543210',
        'address': 'New Address, Salem',
        'distance_km': '3.2',
        'latitude': '11.6650',
        'longitude': '78.1470'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"updated successfully" in response.data

def test_master_quick_update_inventory(auth_client):
    response = auth_client.post('/admin/master/inventory/1/quick-update', data={
        'price': '28.00',
        'stock_quantity': '60'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated" in response.data

# 8. Location & Recommendation Services Unit Tests
def test_calculate_distance():
    # Distance between Salem and Coimbatore ~ 145-165 km
    dist = calculate_distance(11.6643, 78.1460, 11.0168, 76.9558)
    assert dist is not None
    assert 130 < dist < 170

    # Missing / invalid coordinates handling
    assert calculate_distance(None, None, 11.0, 76.0) is None
    assert calculate_distance("invalid", "coords", 11.0, 76.0) is None

def test_find_alternatives():
    alts = find_alternatives("Dolo 650", "Paracetamol", "Pain & Fever")
    assert len(alts) > 0
    assert "Dolo 650" not in alts
