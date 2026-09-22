"""
RuralCare AI — Voice Assistant API Routes (Phase 13)
Provides REST endpoints for the conversational voice assistant.
"""

from datetime import date
from flask import Blueprint, request, jsonify
from models.database import db
from models.models import Medicine, PharmacyInventory
from services.voice_service import (
    classify_intent,
    generate_greeting_response,
    generate_farewell_response,
    generate_symptom_response,
    generate_medicine_response,
    generate_no_result_response,
    SYMPTOM_MEDICINE_MAP
)

voice_bp = Blueprint('voice_bp', __name__)


@voice_bp.route('/api/voice/query', methods=['POST'])
def voice_query():
    """
    Process a natural language voice query and return structured results + spoken response.

    Request JSON:
        { "query": "I have a headache", "lang": "en" }

    Response JSON:
        {
            "status": "success",
            "intent": "symptom_search",
            "spoken_response": "For headache, I found 3 medicines...",
            "results": [...],
            "symptoms": ["headache"],
            "suggestions": ["Show Dolo 650 details", "Find cheapest option"]
        }
    """
    data = request.get_json(silent=True) or {}
    query_text = data.get('query', '').strip()
    lang = data.get('lang', 'en')

    if not query_text:
        return jsonify({
            'status': 'error',
            'spoken_response': 'I didn\'t catch that. Could you please say it again?',
            'results': [],
            'intent': 'empty'
        })

    # Classify intent
    intent_data = classify_intent(query_text)
    intent = intent_data['intent']

    # ── Handle Greeting ─────────────────────────────────────────
    if intent == 'greeting':
        return jsonify({
            'status': 'success',
            'intent': 'greeting',
            'spoken_response': generate_greeting_response(lang),
            'results': [],
            'suggestions': [
                'I have a headache',
                'Find Paracetamol',
                'Cheapest Dolo 650'
            ]
        })

    # ── Handle Farewell ─────────────────────────────────────────
    if intent == 'farewell':
        return jsonify({
            'status': 'success',
            'intent': 'farewell',
            'spoken_response': generate_farewell_response(lang),
            'results': [],
            'suggestions': []
        })

    # ── Handle Symptom Search ───────────────────────────────────
    if intent in ('symptom_search', 'price_check', 'find_nearby'):
        medicine_names = intent_data.get('medicine_names', [])
        symptoms = intent_data.get('symptoms', [])

        if medicine_names:
            medicines_data = _search_medicines_by_names(medicine_names)
        else:
            # Fallback: search using query text
            medicines_data = _search_medicines_by_query(query_text)

        spoken = generate_symptom_response(symptoms, medicines_data, lang) if symptoms else generate_medicine_response(medicines_data, query_text, lang)

        return jsonify({
            'status': 'success',
            'intent': intent,
            'spoken_response': spoken,
            'results': medicines_data,
            'symptoms': symptoms,
            'suggestions': _generate_suggestions(medicines_data)
        })

    # ── Handle Direct Medicine Search ───────────────────────────
    if intent == 'medicine_search':
        medicines_data = _search_medicines_by_query(query_text)

        if not medicines_data:
            # Try symptom match as fallback
            for symptom in SYMPTOM_MEDICINE_MAP:
                if symptom in query_text.lower():
                    medicine_names = SYMPTOM_MEDICINE_MAP[symptom]
                    medicines_data = _search_medicines_by_names(medicine_names)
                    if medicines_data:
                        break

        spoken = generate_medicine_response(medicines_data, query_text, lang)
        if not medicines_data:
            spoken = generate_no_result_response(query_text, lang)

        return jsonify({
            'status': 'success',
            'intent': 'medicine_search',
            'spoken_response': spoken,
            'results': medicines_data,
            'symptoms': [],
            'suggestions': _generate_suggestions(medicines_data)
        })

    # ── Fallback ────────────────────────────────────────────────
    return jsonify({
        'status': 'success',
        'intent': 'general_query',
        'spoken_response': generate_no_result_response(query_text, lang),
        'results': [],
        'suggestions': [
            'I have fever',
            'Find Cetirizine',
            'Cheapest Paracetamol'
        ]
    })


@voice_bp.route('/api/voice/symptom-map')
def get_symptom_map():
    """Return the symptom-to-medicine mapping for the frontend quick-select chips."""
    # Group symptoms by category for display
    categories = {
        'Pain & Fever': ['headache', 'fever', 'body pain', 'toothache', 'back pain'],
        'Cold & Allergy': ['cold', 'cough', 'allergy', 'sneezing', 'itching'],
        'Stomach': ['acidity', 'stomach pain', 'gas', 'nausea', 'vomiting'],
        'Digestion': ['diarrhea', 'constipation', 'loose motion', 'dehydration'],
    }

    return jsonify({
        'status': 'success',
        'categories': categories,
        'full_map': {k: v for k, v in SYMPTOM_MEDICINE_MAP.items()}
    })


@voice_bp.route('/api/recommendations')
def get_recommendations():
    """
    Get medicine recommendations based on symptom or medicine name.
    GET /api/recommendations?symptom=headache
    GET /api/recommendations?medicine_id=1
    """
    symptom = request.args.get('symptom', '').strip().lower()
    medicine_id = request.args.get('medicine_id', type=int)

    if symptom and symptom in SYMPTOM_MEDICINE_MAP:
        medicine_names = SYMPTOM_MEDICINE_MAP[symptom]
        medicines_data = _search_medicines_by_names(medicine_names)
        return jsonify({
            'status': 'success',
            'symptom': symptom,
            'recommendations': medicines_data
        })

    if medicine_id:
        medicine = db.session.get(Medicine, medicine_id)
        if medicine:
            from services.recommendation_service import find_alternatives
            alt_names = find_alternatives(
                medicine.medicine_name,
                medicine.generic_name,
                medicine.category
            )
            alternatives_data = _search_medicines_by_names(alt_names)
            return jsonify({
                'status': 'success',
                'medicine': medicine.medicine_name,
                'alternatives': alternatives_data
            })

    return jsonify({
        'status': 'error',
        'message': 'Please provide a symptom or medicine_id parameter.'
    })


# ── Helper Functions ────────────────────────────────────────────────────

def _search_medicines_by_names(medicine_names):
    """Search the database for medicines matching a list of names."""
    today = date.today()
    results = []
    seen_ids = set()

    for name in medicine_names:
        pattern = f"%{name}%"
        meds = Medicine.query.filter(
            db.or_(
                Medicine.medicine_name.ilike(pattern),
                Medicine.generic_name.ilike(pattern)
            )
        ).all()

        for m in meds:
            if m.medicine_id in seen_ids:
                continue
            seen_ids.add(m.medicine_id)

            items = PharmacyInventory.query.filter_by(
                medicine_id=m.medicine_id, is_active=True
            ).all()
            items = [i for i in items if not i.expiry_date or i.expiry_date >= today]
            available_items = [i for i in items if i.stock_quantity > 0]
            lowest_price = min([float(i.price) for i in available_items]) if available_items else None

            # Find the pharmacy with lowest price
            cheapest_pharmacy = None
            if available_items and lowest_price:
                for i in available_items:
                    if float(i.price) == lowest_price:
                        cheapest_pharmacy = i.pharmacy.shop_name
                        break

            results.append({
                'medicine_id': m.medicine_id,
                'name': m.medicine_name,
                'generic_name': m.generic_name,
                'category': m.category,
                'uses': m.uses,
                'lowest_price': lowest_price,
                'available_count': len(available_items),
                'total_pharmacies': len(items),
                'cheapest_pharmacy': cheapest_pharmacy
            })

    return results


def _search_medicines_by_query(query_text):
    """Search the database for medicines matching a free-text query."""
    today = date.today()
    results = []

    # Extract potential medicine-related words (skip common filler words)
    stop_words = {'i', 'have', 'need', 'want', 'find', 'search', 'get', 'me', 'my',
                  'the', 'a', 'an', 'for', 'to', 'is', 'of', 'can', 'you', 'please',
                  'show', 'give', 'where', 'what', 'how', 'much', 'does', 'do', 'any',
                  'some', 'near', 'nearby', 'price', 'cost', 'cheap', 'cheapest'}

    words = query_text.lower().split()
    search_terms = [w for w in words if w not in stop_words and len(w) > 2]

    if not search_terms:
        search_terms = [query_text.strip()]

    # Search using each meaningful term
    seen_ids = set()
    for term in search_terms:
        pattern = f"%{term}%"
        meds = Medicine.query.filter(
            db.or_(
                Medicine.medicine_name.ilike(pattern),
                Medicine.generic_name.ilike(pattern),
                Medicine.category.ilike(pattern)
            )
        ).all()

        for m in meds:
            if m.medicine_id in seen_ids:
                continue
            seen_ids.add(m.medicine_id)

            items = PharmacyInventory.query.filter_by(
                medicine_id=m.medicine_id, is_active=True
            ).all()
            items = [i for i in items if not i.expiry_date or i.expiry_date >= today]
            available_items = [i for i in items if i.stock_quantity > 0]
            lowest_price = min([float(i.price) for i in available_items]) if available_items else None

            cheapest_pharmacy = None
            if available_items and lowest_price:
                for i in available_items:
                    if float(i.price) == lowest_price:
                        cheapest_pharmacy = i.pharmacy.shop_name
                        break

            results.append({
                'medicine_id': m.medicine_id,
                'name': m.medicine_name,
                'generic_name': m.generic_name,
                'category': m.category,
                'uses': m.uses,
                'lowest_price': lowest_price,
                'available_count': len(available_items),
                'total_pharmacies': len(items),
                'cheapest_pharmacy': cheapest_pharmacy
            })

    return results


def _generate_suggestions(medicines_data):
    """Generate follow-up suggestion chips for the voice assistant UI."""
    suggestions = []
    if medicines_data:
        top = medicines_data[0]
        suggestions.append(f"Show {top['name']} pharmacies")
        if len(medicines_data) > 1:
            suggestions.append(f"Compare {medicines_data[0]['name']} vs {medicines_data[1]['name']}")
        suggestions.append("Find cheapest option")
    else:
        suggestions = [
            'I have a headache',
            'Find Paracetamol near me',
            'Check ORS availability'
        ]
    return suggestions[:3]
