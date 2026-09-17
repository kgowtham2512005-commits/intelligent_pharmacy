"""
RuralCare AI — Intelligent Recommendation Service (Phase 15)
Provides symptom-based medicine suggestions, generic alternatives, and health guidance.
"""

from datetime import date, timedelta


# ── Generic Name ↔ Brand Mapping ────────────────────────────────────────
# Maps generic ingredient names to common brand equivalents in the database.
GENERIC_ALTERNATIVES = {
    'paracetamol': ['Dolo 650', 'Calpol 650', 'Paracetamol 500 mg'],
    'acetaminophen': ['Dolo 650', 'Calpol 650', 'Paracetamol 500 mg'],
    'ibuprofen': ['Ibuprofen 400 mg'],
    'cetirizine': ['Cetirizine 10 mg', 'Levocetirizine 5 mg'],
    'levocetirizine': ['Levocetirizine 5 mg', 'Cetirizine 10 mg'],
    'omeprazole': ['Omeprazole 20 mg', 'Pantoprazole 40 mg', 'Rabeprazole 20 mg'],
    'pantoprazole': ['Pantoprazole 40 mg', 'Omeprazole 20 mg', 'Rabeprazole 20 mg'],
    'rabeprazole': ['Rabeprazole 20 mg', 'Pantoprazole 40 mg', 'Omeprazole 20 mg'],
    'fexofenadine': ['Fexofenadine 120 mg', 'Cetirizine 10 mg', 'Loratadine 10 mg'],
    'loratadine': ['Loratadine 10 mg', 'Cetirizine 10 mg', 'Fexofenadine 120 mg'],
    'domperidone': ['Domperidone 10 mg', 'Ondansetron 4 mg'],
    'ondansetron': ['Ondansetron 4 mg', 'Domperidone 10 mg'],
    'famotidine': ['Famotidine 20 mg', 'Rabeprazole 20 mg'],
    'montelukast': ['Montelukast 10 mg'],
    'aspirin': ['Aspirin 75 mg'],
    'lactulose': ['Lactulose Syrup', 'Isabgol Powder'],
    'isabgol': ['Isabgol Powder', 'Lactulose Syrup'],
}

# ── Category-based related medicines ────────────────────────────────────
CATEGORY_RELATIONS = {
    'Pain & Fever': ['Dolo 650', 'Paracetamol', 'Calpol 650', 'Ibuprofen', 'Aspirin'],
    'Antihistamine': ['Cetirizine', 'Levocetirizine', 'Fexofenadine', 'Loratadine'],
    'Antacid': ['Omeprazole', 'Pantoprazole', 'Rabeprazole', 'Famotidine', 'Antacid Gel'],
    'Anti-nausea': ['Ondansetron', 'Domperidone'],
    'Laxative': ['Lactulose', 'Isabgol'],
    'Respiratory': ['Montelukast'],
    'Rehydration': ['ORS'],
}


def find_alternatives(medicine_name, generic_name=None, category=None):
    """
    Find alternative medicines based on generic name and category.

    Returns:
        List of alternative medicine name strings (excluding the original).
    """
    alternatives = set()

    # Check generic name alternatives
    if generic_name:
        gen_lower = generic_name.lower()
        for gen_key, brands in GENERIC_ALTERNATIVES.items():
            if gen_key in gen_lower or gen_lower in gen_key:
                alternatives.update(brands)

    # Check by medicine name
    med_lower = medicine_name.lower() if medicine_name else ''
    for gen_key, brands in GENERIC_ALTERNATIVES.items():
        for brand in brands:
            if brand.lower() in med_lower or med_lower in brand.lower():
                alternatives.update(brands)
                break

    # Check category relations
    if category:
        for cat, related in CATEGORY_RELATIONS.items():
            if cat.lower() in category.lower() or category.lower() in cat.lower():
                alternatives.update(related)

    # Remove the original medicine from alternatives
    alternatives.discard(medicine_name)
    # Also remove close matches
    alternatives = {alt for alt in alternatives if alt.lower() != med_lower}

    return list(alternatives)[:6]  # Return top 6 alternatives


def get_expiry_alerts(inventory_items, days_threshold=30):
    """
    Check inventory items for upcoming expiry.

    Args:
        inventory_items: list of PharmacyInventory objects
        days_threshold: number of days to check ahead

    Returns:
        List of dicts with expiry alert info.
    """
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)
    alerts = []

    for item in inventory_items:
        if not item.is_active or not item.expiry_date:
            continue

        if item.expiry_date < today:
            alerts.append({
                'medicine_name': item.medicine.medicine_name,
                'inventory_id': item.inventory_id,
                'expiry_date': item.expiry_date.isoformat(),
                'status': 'expired',
                'severity': 'danger',
                'message': f"{item.medicine.medicine_name} has expired on {item.expiry_date.strftime('%b %d, %Y')}!"
            })
        elif item.expiry_date <= threshold_date:
            days_left = (item.expiry_date - today).days
            alerts.append({
                'medicine_name': item.medicine.medicine_name,
                'inventory_id': item.inventory_id,
                'expiry_date': item.expiry_date.isoformat(),
                'days_left': days_left,
                'status': 'expiring_soon',
                'severity': 'warning',
                'message': f"{item.medicine.medicine_name} expires in {days_left} day(s) on {item.expiry_date.strftime('%b %d, %Y')}."
            })

    # Sort: expired first, then by soonest expiry
    alerts.sort(key=lambda a: (0 if a['status'] == 'expired' else 1, a['expiry_date']))
    return alerts


def get_low_stock_alerts(inventory_items, low_threshold=10):
    """
    Check inventory items for low stock levels.

    Returns:
        List of dicts with low stock alert info.
    """
    alerts = []

    for item in inventory_items:
        if not item.is_active:
            continue

        if item.stock_quantity <= 0:
            alerts.append({
                'medicine_name': item.medicine.medicine_name,
                'inventory_id': item.inventory_id,
                'stock_quantity': item.stock_quantity,
                'status': 'out_of_stock',
                'severity': 'danger',
                'message': f"{item.medicine.medicine_name} is OUT OF STOCK!"
            })
        elif item.stock_quantity <= low_threshold:
            alerts.append({
                'medicine_name': item.medicine.medicine_name,
                'inventory_id': item.inventory_id,
                'stock_quantity': item.stock_quantity,
                'status': 'low_stock',
                'severity': 'warning',
                'message': f"{item.medicine.medicine_name} has only {item.stock_quantity} units left."
            })

    alerts.sort(key=lambda a: (0 if a['status'] == 'out_of_stock' else 1, a['stock_quantity']))
    return alerts
