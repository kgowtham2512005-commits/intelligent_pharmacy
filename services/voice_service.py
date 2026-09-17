"""
RuralCare AI — Voice Assistant NLP Service (Phase 13)
Handles intent classification, symptom-to-medicine mapping, and response generation.
Works fully offline using keyword/pattern matching — no external AI API needed.
"""

# ── Symptom-to-Medicine Mapping Knowledge Base ──────────────────────────
# Maps common symptoms to medicine names that may treat them.
# These are matched against the master medicine catalog in the database.

SYMPTOM_MEDICINE_MAP = {
    # Pain & Fever
    'fever': ['Dolo 650', 'Paracetamol', 'Calpol 650', 'Ibuprofen'],
    'headache': ['Dolo 650', 'Paracetamol', 'Calpol 650', 'Ibuprofen', 'Aspirin'],
    'head pain': ['Dolo 650', 'Paracetamol', 'Calpol 650', 'Ibuprofen'],
    'body pain': ['Dolo 650', 'Paracetamol', 'Ibuprofen'],
    'muscle pain': ['Ibuprofen', 'Dolo 650', 'Paracetamol'],
    'joint pain': ['Ibuprofen', 'Aspirin'],
    'toothache': ['Ibuprofen', 'Paracetamol', 'Dolo 650'],
    'back pain': ['Ibuprofen', 'Paracetamol'],
    'period pain': ['Ibuprofen', 'Paracetamol', 'Dolo 650'],
    'menstrual pain': ['Ibuprofen', 'Paracetamol'],

    # Cold, Cough & Allergy
    'cold': ['Cetirizine', 'Levocetirizine', 'Paracetamol', 'Fexofenadine'],
    'cough': ['Montelukast', 'Levocetirizine', 'Cetirizine'],
    'allergy': ['Cetirizine', 'Levocetirizine', 'Fexofenadine', 'Loratadine'],
    'sneezing': ['Cetirizine', 'Levocetirizine', 'Fexofenadine', 'Loratadine'],
    'runny nose': ['Cetirizine', 'Levocetirizine', 'Fexofenadine'],
    'itching': ['Cetirizine', 'Levocetirizine', 'Fexofenadine', 'Loratadine'],
    'skin allergy': ['Cetirizine', 'Loratadine', 'Fexofenadine'],
    'rash': ['Cetirizine', 'Loratadine', 'Fexofenadine'],
    'hives': ['Cetirizine', 'Levocetirizine', 'Fexofenadine'],
    'watery eyes': ['Cetirizine', 'Levocetirizine'],
    'dust allergy': ['Cetirizine', 'Fexofenadine', 'Loratadine'],
    'asthma': ['Montelukast'],
    'wheezing': ['Montelukast'],
    'breathing difficulty': ['Montelukast'],

    # Stomach & Digestion
    'acidity': ['Omeprazole', 'Pantoprazole', 'Rabeprazole', 'Famotidine', 'Antacid Gel'],
    'stomach pain': ['Pantoprazole', 'Omeprazole', 'Antacid Gel'],
    'gas': ['Antacid Gel', 'Pantoprazole', 'Omeprazole'],
    'bloating': ['Antacid Gel', 'Pantoprazole'],
    'heartburn': ['Omeprazole', 'Pantoprazole', 'Rabeprazole', 'Famotidine'],
    'acid reflux': ['Omeprazole', 'Pantoprazole', 'Rabeprazole'],
    'indigestion': ['Omeprazole', 'Pantoprazole', 'Antacid Gel'],
    'ulcer': ['Omeprazole', 'Pantoprazole', 'Rabeprazole'],
    'nausea': ['Ondansetron', 'Domperidone'],
    'vomiting': ['Ondansetron', 'Domperidone'],
    'motion sickness': ['Ondansetron', 'Domperidone'],

    # Diarrhea & Dehydration
    'diarrhea': ['ORS', 'Ondansetron'],
    'loose motion': ['ORS', 'Ondansetron'],
    'dehydration': ['ORS'],
    'weakness': ['ORS'],
    'electrolyte': ['ORS'],

    # Constipation
    'constipation': ['Lactulose', 'Isabgol'],
    'hard stool': ['Lactulose', 'Isabgol'],
    'irregular bowel': ['Isabgol', 'Lactulose'],
    'fiber': ['Isabgol'],

    # Heart
    'blood thinner': ['Aspirin'],
    'heart': ['Aspirin'],
    'chest pain': ['Aspirin'],
}

# ── Greeting Patterns ───────────────────────────────────────────────────
GREETING_KEYWORDS = [
    'hello', 'hi', 'hey', 'namaste', 'vanakkam', 'good morning',
    'good afternoon', 'good evening', 'help', 'what can you do',
    'who are you', 'how are you'
]

# ── Thank/Bye Patterns ──────────────────────────────────────────────────
FAREWELL_KEYWORDS = [
    'thank', 'thanks', 'bye', 'goodbye', 'see you', 'quit', 'exit', 'close'
]


def classify_intent(text):
    """
    Classify the user's natural language input into an intent.
    Returns a dict with 'intent' and relevant extracted entities.

    Intents:
      - greeting: User is saying hello or asking for help
      - farewell: User is saying bye/thanks
      - symptom_search: User describes a symptom (headache, fever, etc.)
      - medicine_search: User asks for a specific medicine by name
      - price_check: User asks about medicine price
      - find_nearby: User asks for nearby pharmacies
      - general_query: Fallback for unrecognized queries
    """
    if not text or not text.strip():
        return {'intent': 'general_query', 'query': '', 'symptoms': [], 'medicine_names': []}

    text_lower = text.lower().strip()

    # Check greetings
    for greeting in GREETING_KEYWORDS:
        if greeting in text_lower:
            return {'intent': 'greeting', 'query': text}

    # Check farewells
    for farewell in FAREWELL_KEYWORDS:
        if farewell in text_lower:
            return {'intent': 'farewell', 'query': text}

    # Check for price-related queries
    price_keywords = ['price', 'cost', 'how much', 'rate', 'expensive', 'cheap', 'cheapest', 'lowest price', 'best price']
    is_price_query = any(kw in text_lower for kw in price_keywords)

    # Check for nearby/location queries
    nearby_keywords = ['near', 'nearby', 'closest', 'nearest', 'where', 'which shop', 'which pharmacy', 'find pharmacy', 'locate']
    is_nearby_query = any(kw in text_lower for kw in nearby_keywords)

    # Check for symptom matches
    matched_symptoms = []
    matched_medicines_from_symptoms = []
    for symptom, medicines in SYMPTOM_MEDICINE_MAP.items():
        if symptom in text_lower:
            matched_symptoms.append(symptom)
            for med in medicines:
                if med not in matched_medicines_from_symptoms:
                    matched_medicines_from_symptoms.append(med)

    if matched_symptoms:
        intent = 'symptom_search'
        if is_price_query:
            intent = 'price_check'
        elif is_nearby_query:
            intent = 'find_nearby'
        return {
            'intent': intent,
            'query': text,
            'symptoms': matched_symptoms,
            'medicine_names': matched_medicines_from_symptoms
        }

    # Check for direct medicine name mention (will be matched against DB)
    if is_price_query:
        return {'intent': 'price_check', 'query': text, 'symptoms': [], 'medicine_names': []}
    if is_nearby_query:
        return {'intent': 'find_nearby', 'query': text, 'symptoms': [], 'medicine_names': []}

    # Default: treat as medicine search
    return {'intent': 'medicine_search', 'query': text, 'symptoms': [], 'medicine_names': []}


def generate_greeting_response(lang='en'):
    """Generate a greeting response for the voice assistant."""
    responses = {
        'en': (
            "Hello! I'm your RuralCare AI assistant. "
            "You can ask me things like: 'I have a headache', 'Find Paracetamol near me', "
            "or 'What is the cheapest Dolo 650?' — How can I help you today?"
        ),
        'ta': (
            "வணக்கம்! நான் உங்கள் RuralCare AI உதவியாளர். "
            "நீங்கள் 'எனக்கு தலைவலி', 'பாராசிட்டமால் கிடைக்குமா' என்று கேட்கலாம். "
            "இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?"
        ),
        'hi': (
            "नमस्ते! मैं आपका RuralCare AI सहायक हूँ। "
            "आप मुझसे पूछ सकते हैं: 'मुझे सिरदर्द है', 'पैरासिटामोल कहाँ मिलेगा', "
            "या 'सबसे सस्ता डोलो 650 कहाँ है?' — मैं आज आपकी कैसे मदद कर सकता हूँ?"
        )
    }
    return responses.get(lang, responses['en'])


def generate_farewell_response(lang='en'):
    """Generate a farewell response."""
    responses = {
        'en': "Thank you for using RuralCare AI! Stay healthy and take care. Goodbye!",
        'ta': "RuralCare AI பயன்படுத்தியதற்கு நன்றி! ஆரோக்கியமாக இருங்கள். நன்றி!",
        'hi': "RuralCare AI का उपयोग करने के लिए धन्यवाद! स्वस्थ रहें। अलविदा!"
    }
    return responses.get(lang, responses['en'])


def generate_symptom_response(symptoms, medicines_data, lang='en'):
    """
    Generate a natural language response for symptom-based search results.

    Args:
        symptoms: list of matched symptom strings
        medicines_data: list of dicts with medicine info from the DB query
            Each dict: {name, lowest_price, available_count, pharmacy_name, medicine_id}
        lang: language code ('en', 'ta', 'hi')
    """
    if not medicines_data:
        no_result = {
            'en': f"I understand you're experiencing {', '.join(symptoms)}. Unfortunately, I couldn't find any matching medicines in stock right now. Please consult a nearby doctor or pharmacist.",
            'ta': f"நீங்கள் {', '.join(symptoms)} அனுபவிக்கிறீர்கள் என்று புரிகிறது. துரதிர்ஷ்டவசமாக, தற்போது கையிருப்பில் மருந்துகள் இல்லை. அருகிலுள்ள மருத்துவரை அணுகவும்.",
            'hi': f"मैं समझता हूँ कि आपको {', '.join(symptoms)} की समस्या है। दुर्भाग्य से, अभी कोई दवा स्टॉक में नहीं मिली। कृपया नजदीकी डॉक्टर से संपर्क करें।"
        }
        return no_result.get(lang, no_result['en'])

    # Build response
    symptom_text = ' and '.join(symptoms)
    top_med = medicines_data[0]

    if lang == 'en':
        response = f"For {symptom_text}, I found {len(medicines_data)} medicine(s). "
        response += f"The top recommendation is {top_med['name']}"
        if top_med.get('lowest_price'):
            response += f", available from ₹{top_med['lowest_price']:.2f}"
        if top_med.get('available_count', 0) > 0:
            response += f" at {top_med['available_count']} pharmacy"
            if top_med['available_count'] > 1:
                response += " shops"
        response += ". "
        if len(medicines_data) > 1:
            other_names = [m['name'] for m in medicines_data[1:4]]
            response += f"Other options include {', '.join(other_names)}. "
        response += "Would you like me to show pharmacy details?"

    elif lang == 'ta':
        response = f"{symptom_text} க்கு, {len(medicines_data)} மருந்துகள் கிடைக்கின்றன. "
        response += f"சிறந்த பரிந்துரை {top_med['name']}"
        if top_med.get('lowest_price'):
            response += f", ₹{top_med['lowest_price']:.2f} முதல் கிடைக்கிறது"
        response += ". "

    elif lang == 'hi':
        response = f"{symptom_text} के लिए, {len(medicines_data)} दवाइयाँ मिलीं। "
        response += f"शीर्ष सिफारिश {top_med['name']} है"
        if top_med.get('lowest_price'):
            response += f", ₹{top_med['lowest_price']:.2f} से उपलब्ध"
        response += "। "

    else:
        response = generate_symptom_response(symptoms, medicines_data, 'en')

    return response


def generate_medicine_response(medicines_data, query, lang='en'):
    """
    Generate a natural language response for direct medicine search results.

    Args:
        medicines_data: list of dicts with medicine info
        query: original search query text
        lang: language code
    """
    if not medicines_data:
        no_result = {
            'en': f"I couldn't find any medicine matching '{query}' in our database. Please check the spelling or try a different name.",
            'ta': f"'{query}' என்ற மருந்து எங்கள் தரவுத்தளத்தில் கிடைக்கவில்லை. பெயரை சரிபார்க்கவும்.",
            'hi': f"'{query}' नाम की दवा हमारे डेटाबेस में नहीं मिली। कृपया नाम जाँचें।"
        }
        return no_result.get(lang, no_result['en'])

    med = medicines_data[0]

    if lang == 'en':
        response = f"I found {med['name']}. "
        if med.get('lowest_price'):
            response += f"The lowest available price is ₹{med['lowest_price']:.2f}. "
        if med.get('available_count', 0) > 0:
            response += f"It's available at {med['available_count']} nearby pharmacy"
            if med['available_count'] > 1:
                response += " shops"
            response += ". "
        else:
            response += "Unfortunately, it appears to be out of stock at all nearby pharmacies. "
        if med.get('category'):
            response += f"Category: {med['category']}. "
        if med.get('uses'):
            response += f"Uses: {med['uses']}. "

    elif lang == 'ta':
        response = f"{med['name']} கிடைக்கிறது. "
        if med.get('lowest_price'):
            response += f"குறைந்த விலை ₹{med['lowest_price']:.2f}. "
        if med.get('available_count', 0) > 0:
            response += f"{med['available_count']} மருந்தகங்களில் கிடைக்கும். "

    elif lang == 'hi':
        response = f"{med['name']} उपलब्ध है। "
        if med.get('lowest_price'):
            response += f"सबसे कम कीमत ₹{med['lowest_price']:.2f} है। "
        if med.get('available_count', 0) > 0:
            response += f"{med['available_count']} फार्मेसी में उपलब्ध है। "

    else:
        response = generate_medicine_response(medicines_data, query, 'en')

    return response


def generate_no_result_response(query, lang='en'):
    """Generate response when no results are found."""
    responses = {
        'en': f"I'm sorry, I couldn't find results for '{query}'. Try saying a symptom like 'headache' or 'fever', or a medicine name like 'Paracetamol' or 'Dolo 650'.",
        'ta': f"'{query}' க்கு முடிவுகள் கிடைக்கவில்லை. 'தலைவலி' அல்லது 'காய்ச்சல்' போன்ற அறிகுறிகளை கூறவும்.",
        'hi': f"'{query}' के लिए कोई परिणाम नहीं मिला। 'सिरदर्द' या 'बुखार' जैसे लक्षण बताएं।"
    }
    return responses.get(lang, responses['en'])
