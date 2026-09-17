"""
RuralCare AI — Smart Alerts & Notifications API Routes (Phase 17)
Provides endpoints for inventory expiry tracking, low-stock alerts, and admin dashboard notifications.
"""

from datetime import date, timedelta
from flask import Blueprint, jsonify, request, session
from models.database import db
from models.models import PharmacyInventory, Medicine, Pharmacy
from services.recommendation_service import get_expiry_alerts, get_low_stock_alerts

alerts_bp = Blueprint('alerts_bp', __name__)


@alerts_bp.route('/api/alerts/summary', methods=['GET'])
def get_alerts_summary():
    """
    Get aggregated alert counts for the admin dashboard badge & notification bell.
    Filtered by admin's pharmacy if not a super admin.
    """
    pharmacy_id = request.args.get('pharmacy_id', type=int) or session.get('pharmacy_id')
    days_threshold = request.args.get('days', default=30, type=int)
    low_threshold = request.args.get('threshold', default=10, type=int)

    query = PharmacyInventory.query.filter_by(is_active=True)
    if pharmacy_id:
        query = query.filter_by(pharmacy_id=pharmacy_id)
    
    items = query.all()

    expiry_alerts = get_expiry_alerts(items, days_threshold=days_threshold)
    low_stock_alerts = get_low_stock_alerts(items, low_threshold=low_threshold)

    critical_count = sum(1 for a in expiry_alerts if a.get('severity') == 'danger') + \
                     sum(1 for a in low_stock_alerts if a.get('severity') == 'danger')
    warning_count = sum(1 for a in expiry_alerts if a.get('severity') == 'warning') + \
                    sum(1 for a in low_stock_alerts if a.get('severity') == 'warning')

    return jsonify({
        'status': 'success',
        'total_alerts': len(expiry_alerts) + len(low_stock_alerts),
        'critical_count': critical_count,
        'warning_count': warning_count,
        'expiry_count': len(expiry_alerts),
        'low_stock_count': len(low_stock_alerts),
        'alerts': {
            'expiry': expiry_alerts[:10],
            'low_stock': low_stock_alerts[:10]
        }
    })


@alerts_bp.route('/api/alerts/expiry', methods=['GET'])
def expiry_alerts_route():
    """Return all expiring and expired medicines."""
    pharmacy_id = request.args.get('pharmacy_id', type=int) or session.get('pharmacy_id')
    days_threshold = request.args.get('days', default=30, type=int)

    query = PharmacyInventory.query.filter_by(is_active=True)
    if pharmacy_id:
        query = query.filter_by(pharmacy_id=pharmacy_id)

    items = query.all()
    alerts = get_expiry_alerts(items, days_threshold=days_threshold)

    return jsonify({
        'status': 'success',
        'count': len(alerts),
        'days_threshold': days_threshold,
        'alerts': alerts
    })


@alerts_bp.route('/api/alerts/low-stock', methods=['GET'])
def low_stock_alerts_route():
    """Return all low stock or out-of-stock items."""
    pharmacy_id = request.args.get('pharmacy_id', type=int) or session.get('pharmacy_id')
    low_threshold = request.args.get('threshold', default=10, type=int)

    query = PharmacyInventory.query.filter_by(is_active=True)
    if pharmacy_id:
        query = query.filter_by(pharmacy_id=pharmacy_id)

    items = query.all()
    alerts = get_low_stock_alerts(items, low_threshold=low_threshold)

    return jsonify({
        'status': 'success',
        'count': len(alerts),
        'threshold': low_threshold,
        'alerts': alerts
    })
