from datetime import date
from flask import Blueprint, render_template, request, jsonify
from models.database import db
from models.models import Medicine, PharmacyInventory, Pharmacy
from services.location_service import calculate_distance

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/')
def landing():
    """Customer Homepage for RuralCare AI with search & entry points."""
    return render_template('index.html')

@user_bp.route('/api/medicines/search')
def search_api():
    """REST API endpoint for medicine search supporting partial/case-insensitive matching."""
    query = request.args.get('q', '').strip()
    user_lat = request.args.get('lat')
    user_lng = request.args.get('lng')

    if not query:
        return jsonify({'status': 'success', 'results': [], 'message': 'Please enter a medicine name.'})

    pattern = f"%{query}%"
    meds = Medicine.query.filter(
        db.or_(
            Medicine.medicine_name.ilike(pattern),
            Medicine.generic_name.ilike(pattern),
            Medicine.category.ilike(pattern)
        )
    ).all()

    if not meds:
        return jsonify({'status': 'success', 'results': [], 'message': 'Medicine not found.'})

    today = date.today()
    results = []
    for m in meds:
        items = PharmacyInventory.query.filter_by(medicine_id=m.medicine_id, is_active=True).all()
        items = [i for i in items if not i.expiry_date or i.expiry_date >= today]
        
        available_items = [i for i in items if i.stock_quantity > 0]
        lowest_price = min([float(i.price) for i in available_items]) if available_items else None
        
        results.append({
            'medicine_id': m.medicine_id,
            'medicine_name': m.medicine_name,
            'generic_name': m.generic_name,
            'category': m.category,
            'uses': m.uses,
            'available_pharmacies_count': len(available_items),
            'total_pharmacies_count': len(items),
            'lowest_price': lowest_price
        })

    return jsonify({'status': 'success', 'results': results, 'message': f'Found {len(results)} medicine(s).'})

@user_bp.route('/search')
def search_page():
    """HTML search results view."""
    query = request.args.get('q', '').strip()
    user_lat = request.args.get('lat')
    user_lng = request.args.get('lng')

    meds = []
    message = None

    if query:
        pattern = f"%{query}%"
        meds = Medicine.query.filter(
            db.or_(
                Medicine.medicine_name.ilike(pattern),
                Medicine.generic_name.ilike(pattern),
                Medicine.category.ilike(pattern)
            )
        ).all()
        
        if not meds:
            message = "Medicine not found."
    else:
        message = "Please enter a medicine name to search."

    today = date.today()
    search_results = []
    for m in meds:
        items = PharmacyInventory.query.filter_by(medicine_id=m.medicine_id, is_active=True).all()
        items = [i for i in items if not i.expiry_date or i.expiry_date >= today]
        available_items = [i for i in items if i.stock_quantity > 0]
        lowest_price = min([float(i.price) for i in available_items]) if available_items else None

        search_results.append({
            'medicine': m,
            'available_count': len(available_items),
            'total_count': len(items),
            'lowest_price': lowest_price
        })

    return render_template(
        'index.html',
        query=query,
        search_results=search_results,
        message=message,
        user_lat=user_lat,
        user_lng=user_lng
    )

@user_bp.route('/medicine/<int:medicine_id>')
def medicine_detail(medicine_id):
    """Customer Medicine Result & Pharmacy Price Comparison Page."""
    medicine = Medicine.query.get_or_404(medicine_id)
    user_lat = request.args.get('lat')
    user_lng = request.args.get('lng')
    sort_by = request.args.get('sort', 'price').lower()

    today = date.today()
    inventory_items = PharmacyInventory.query.filter_by(medicine_id=medicine_id, is_active=True).all()
    inventory_items = [i for i in inventory_items if not i.expiry_date or i.expiry_date >= today]

    pharmacies_data = []
    available_prices = []

    for item in inventory_items:
        pharmacy = item.pharmacy
        dist = pharmacy.distance_km
        is_available = item.stock_quantity > 0
        
        if is_available:
            available_prices.append(float(item.price))

        pharmacies_data.append({
            'inventory_id': item.inventory_id,
            'pharmacy_id': pharmacy.pharmacy_id,
            'shop_name': pharmacy.shop_name,
            'owner_name': pharmacy.owner_name,
            'address': pharmacy.address,
            'phone': pharmacy.phone,
            'price': float(item.price),
            'stock_quantity': item.stock_quantity,
            'status': item.status,
            'is_available': is_available,
            'last_updated': item.last_updated,
            'distance': dist
        })

    lowest_available_price = min(available_prices) if available_prices else None

    # Sorting
    if sort_by == 'distance':
        pharmacies_data.sort(key=lambda p: (p['distance'] if p['distance'] is not None else 99999, p['price']))
    elif sort_by == 'stock':
        pharmacies_data.sort(key=lambda p: (not p['is_available'], -p['stock_quantity'], p['price']))
    # Find generic/alternative medicines (Phase 15)
    from services.recommendation_service import find_alternatives
    alt_names = find_alternatives(medicine.medicine_name, medicine.generic_name, medicine.category)
    alternatives_data = []
    if alt_names:
        for aname in alt_names:
            alt_meds = Medicine.query.filter(Medicine.medicine_name.ilike(f"%{aname}%")).all()
            for am in alt_meds:
                if am.medicine_id != medicine.medicine_id and not any(x['medicine_id'] == am.medicine_id for x in alternatives_data):
                    a_items = PharmacyInventory.query.filter_by(medicine_id=am.medicine_id, is_active=True).all()
                    a_items = [i for i in a_items if not i.expiry_date or i.expiry_date >= today]
                    a_avail = [i for i in a_items if i.stock_quantity > 0]
                    a_price = min([float(i.price) for i in a_avail]) if a_avail else None
                    alternatives_data.append({
                        'medicine_id': am.medicine_id,
                        'name': am.medicine_name,
                        'generic_name': am.generic_name,
                        'category': am.category,
                        'lowest_price': a_price,
                        'available_count': len(a_avail),
                        'total_pharmacies': len(a_items)
                    })

    return render_template(
        'user/medicine_detail.html',
        medicine=medicine,
        pharmacies=pharmacies_data,
        lowest_available_price=lowest_available_price,
        alternatives=alternatives_data,
        user_lat=user_lat,
        user_lng=user_lng,
        sort_by=sort_by
    )

