from datetime import datetime, date, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db
from models.models import Admin, Pharmacy, Medicine, PharmacyInventory

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to enforce authenticated session for admin routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access the pharmacy admin area.', 'warning')
            return redirect(url_for('admin_bp.login'))
        
        # Enforce multi-pharmacy ownership isolation
        pharmacy = Pharmacy.query.filter_by(admin_id=session['admin_id']).first()
        if not pharmacy:
            session.clear()
            flash('Associated pharmacy record not found. Please log in again.', 'danger')
            return redirect(url_for('admin_bp.login'))
            
        g.pharmacy = pharmacy
        g.admin_id = session['admin_id']
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# AUTHENTICATION ROUTES (Phases 3 & 4)
# ==========================================

@admin_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Pharmacy Admin Registration Route."""
    if 'admin_id' in session:
        return redirect(url_for('admin_bp.dashboard'))

    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()

        errors = []
        if not shop_name:
            errors.append("Shop Name is required.")
        if not owner_name:
            errors.append("Owner Name is required.")
        if not username:
            errors.append("Username is required.")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if not address:
            errors.append("Address is required.")
        if not phone:
            errors.append("Phone number is required.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/register.html', 
                                   shop_name=shop_name, 
                                   owner_name=owner_name, 
                                   username=username, 
                                   address=address, 
                                   phone=phone)

        # Check if username already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash("Username already exists. Please choose another username.", "danger")
            return render_template('admin/register.html', 
                                   shop_name=shop_name, 
                                   owner_name=owner_name, 
                                   username="", 
                                   address=address, 
                                   phone=phone)

        try:
            password_hash = generate_password_hash(password)
            new_admin = Admin(username=username, password_hash=password_hash)
            db.session.add(new_admin)
            db.session.flush()

            new_pharmacy = Pharmacy(
                admin_id=new_admin.admin_id,
                shop_name=shop_name,
                owner_name=owner_name,
                address=address,
                phone=phone
            )
            db.session.add(new_pharmacy)
            db.session.commit()

            flash("Registration successful! Please log in with your credentials.", "success")
            return redirect(url_for('admin_bp.login'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {str(e)}", "danger")
            return render_template('admin/register.html', 
                                   shop_name=shop_name, 
                                   owner_name=owner_name, 
                                   username=username, 
                                   address=address, 
                                   phone=phone)

    return render_template('admin/register.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pharmacy Admin Login Route."""
    if 'admin_id' in session:
        return redirect(url_for('admin_bp.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('admin/login.html', username=username)

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password_hash, password):
            pharmacy = Pharmacy.query.filter_by(admin_id=admin.admin_id).first()
            
            session.clear()
            session['admin_id'] = admin.admin_id
            session['username'] = admin.username
            session['pharmacy_id'] = pharmacy.pharmacy_id if pharmacy else None
            session['shop_name'] = pharmacy.shop_name if pharmacy else "Pharmacy Portal"
            session['owner_name'] = pharmacy.owner_name if pharmacy else admin.username

            flash(f"Welcome back, {session['owner_name']}!", "success")
            return redirect(url_for('admin_bp.dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "danger")
            return render_template('admin/login.html', username=username)

    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Logout route clearing session."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('admin_bp.login'))

# ==========================================
# DASHBOARD (Phases 5, 17 & 18)
# ==========================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Protected Admin Dashboard displaying stats, smart alerts & visual analytics."""
    pharmacy = g.pharmacy

    # Retrieve all inventory items belonging strictly to this pharmacy
    inventory_query = PharmacyInventory.query.filter_by(pharmacy_id=pharmacy.pharmacy_id)
    all_items = inventory_query.all()

    total_medicines = len(all_items)
    
    today = date.today()
    exp_threshold = today + timedelta(days=30)
    
    available_medicines = sum(1 for item in all_items if item.is_active and item.stock_quantity > 0 and (not item.expiry_date or item.expiry_date >= today))
    low_stock_medicines = sum(1 for item in all_items if item.is_active and 0 < item.stock_quantity <= 10)
    out_of_stock_medicines = sum(1 for item in all_items if item.is_active and item.stock_quantity <= 0)
    expired_medicines = sum(1 for item in all_items if item.is_active and item.expiry_date and item.expiry_date < today)
    expiring_soon_medicines = sum(1 for item in all_items if item.is_active and item.expiry_date and today <= item.expiry_date <= exp_threshold)
    inactive_medicines = sum(1 for item in all_items if not item.is_active)

    # Expiry & Low Stock Alert lists
    expiry_alerts = []
    low_stock_alerts = []
    category_counts = {}

    for item in all_items:
        # Category counting for Chart.js
        cat = item.medicine.category or 'General'
        category_counts[cat] = category_counts.get(cat, 0) + 1

        if item.is_active:
            # Expiry check
            if item.expiry_date:
                days_left = (item.expiry_date - today).days
                if days_left < 0:
                    expiry_alerts.append({
                        'medicine_name': item.medicine.medicine_name,
                        'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
                        'days_left': days_left,
                        'urgency': 'critical',
                        'message': f"Expired {abs(days_left)} days ago",
                        'inventory_id': item.inventory_id
                    })
                elif days_left <= 30:
                    expiry_alerts.append({
                        'medicine_name': item.medicine.medicine_name,
                        'expiry_date': item.expiry_date.strftime('%Y-%m-%d'),
                        'days_left': days_left,
                        'urgency': 'warning' if days_left <= 15 else 'info',
                        'message': f"Expires in {days_left} days",
                        'inventory_id': item.inventory_id
                    })
            # Low stock check
            if item.stock_quantity <= 10:
                low_stock_alerts.append({
                    'medicine_name': item.medicine.medicine_name,
                    'stock_quantity': item.stock_quantity,
                    'urgency': 'critical' if item.stock_quantity == 0 else 'warning',
                    'message': 'Out of Stock' if item.stock_quantity == 0 else f'Low Stock ({item.stock_quantity} left)',
                    'inventory_id': item.inventory_id
                })

    # Recently updated medicines (limit 5)
    recently_updated = inventory_query.order_by(PharmacyInventory.last_updated.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        pharmacy=pharmacy,
        total_medicines=total_medicines,
        available_medicines=available_medicines,
        low_stock_medicines=low_stock_medicines,
        out_of_stock_medicines=out_of_stock_medicines,
        expired_medicines=expired_medicines,
        expiring_soon_medicines=expiring_soon_medicines,
        inactive_medicines=inactive_medicines,
        recently_updated=recently_updated,
        expiry_alerts=expiry_alerts,
        low_stock_alerts=low_stock_alerts,
        category_counts=category_counts
    )

# ==========================================
# INVENTORY & MEDICINES (Phases 6, 7 & 8)
# ==========================================

@admin_bp.route('/medicines')
@admin_required
def medicines():
    """Admin Inventory UI with Search, Filter & Sort."""
    pharmacy = g.pharmacy

    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all').lower()
    sort_by = request.args.get('sort', 'updated').lower()

    # Join PharmacyInventory with Medicine master table
    query = db.session.query(PharmacyInventory).join(Medicine).filter(PharmacyInventory.pharmacy_id == pharmacy.pharmacy_id)

    # Search filter (Medicine Name, Generic Name, or Category)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Medicine.medicine_name.ilike(search_pattern),
                Medicine.generic_name.ilike(search_pattern),
                Medicine.category.ilike(search_pattern)
            )
        )

    # Fetch all matching items
    items = query.all()
    today = date.today()

    # Dynamic status filter
    if status_filter == 'available':
        items = [i for i in items if i.is_active and i.stock_quantity > 0 and (not i.expiry_date or i.expiry_date >= today)]
    elif status_filter == 'out_of_stock':
        items = [i for i in items if i.is_active and i.stock_quantity <= 0]
    elif status_filter == 'expired':
        items = [i for i in items if i.is_active and i.expiry_date and i.expiry_date < today]
    elif status_filter == 'inactive':
        items = [i for i in items if not i.is_active]

    # Sorting
    if sort_by == 'name':
        items.sort(key=lambda i: i.medicine.medicine_name.lower())
    elif sort_by == 'price_asc':
        items.sort(key=lambda i: float(i.price))
    elif sort_by == 'price_desc':
        items.sort(key=lambda i: float(i.price), reverse=True)
    elif sort_by == 'stock_asc':
        items.sort(key=lambda i: i.stock_quantity)
    elif sort_by == 'stock_desc':
        items.sort(key=lambda i: i.stock_quantity, reverse=True)
    else:  # default 'updated'
        items.sort(key=lambda i: i.last_updated or datetime.min, reverse=True)

    return render_template(
        'admin/medicines.html',
        pharmacy=pharmacy,
        inventory=items,
        search_query=search_query,
        status_filter=status_filter,
        sort_by=sort_by
    )

@admin_bp.route('/medicines/add', methods=['GET', 'POST'])
@admin_required
def add_medicine():
    """Add Medicine to Pharmacy Inventory with Master Medicine Deduplication."""
    pharmacy = g.pharmacy

    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        category = request.form.get('category', '').strip()
        medicine_type = request.form.get('medicine_type', '').strip()
        uses = request.form.get('uses', '').strip()
        purpose = request.form.get('purpose', '').strip()
        how_to_use = request.form.get('how_to_use', '').strip()
        warnings = request.form.get('warnings', '').strip()
        precautions = request.form.get('precautions', '').strip()
        price_str = request.form.get('price', '').strip()
        stock_str = request.form.get('stock_quantity', '').strip()
        expiry_str = request.form.get('expiry_date', '').strip()

        # Validation
        errors = []
        if not medicine_name:
            errors.append("Medicine Name is required.")

        price = None
        try:
            price = float(price_str)
            if price <= 0:
                errors.append("Price must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid price (e.g. 15.50).")

        stock_quantity = 0
        try:
            stock_quantity = int(stock_str)
            if stock_quantity < 0:
                errors.append("Stock quantity cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid stock quantity (e.g. 50).")

        expiry_date = None
        if expiry_str:
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid expiry date format. Use YYYY-MM-DD.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/add_medicine.html',
                                   pharmacy=pharmacy,
                                   medicine_name=medicine_name,
                                   generic_name=generic_name,
                                   medicine_type=medicine_type,
                                   category=category,
                                   uses=uses,
                                   purpose=purpose,
                                   how_to_use=how_to_use,
                                   warnings=warnings,
                                   precautions=precautions,
                                   price=price_str,
                                   stock_quantity=stock_str,
                                   expiry_date=expiry_str)

        try:
            # Step 1: Master Medicine Lookup / Creation (Deduplication)
            med = Medicine.query.filter(db.func.lower(Medicine.medicine_name) == medicine_name.lower()).first()
            if not med:
                med = Medicine(
                    medicine_name=medicine_name,
                    generic_name=generic_name if generic_name else None,
                    medicine_type=medicine_type if medicine_type else None,
                    category=category if category else None,
                    uses=uses if uses else None,
                    purpose=purpose if purpose else None,
                    how_to_use=how_to_use if how_to_use else None,
                    warnings=warnings if warnings else None,
                    precautions=precautions if precautions else None
                )
                db.session.add(med)
                db.session.flush()  # obtain med.medicine_id
            else:
                # Update optional metadata if missing
                if generic_name and not med.generic_name:
                    med.generic_name = generic_name
                if medicine_type and not med.medicine_type:
                    med.medicine_type = medicine_type
                if category and not med.category:
                    med.category = category
                if uses and not med.uses:
                    med.uses = uses
                if purpose and not med.purpose:
                    med.purpose = purpose
                if how_to_use and not med.how_to_use:
                    med.how_to_use = how_to_use
                if warnings and not med.warnings:
                    med.warnings = warnings
                if precautions and not med.precautions:
                    med.precautions = precautions

            # Step 2: Pharmacy Inventory Creation or Update
            inv = PharmacyInventory.query.filter_by(pharmacy_id=pharmacy.pharmacy_id, medicine_id=med.medicine_id).first()
            if inv:
                inv.price = price
                inv.stock_quantity = stock_quantity
                inv.expiry_date = expiry_date
                inv.is_active = True
                inv.last_updated = datetime.utcnow()
                flash(f"Updated inventory for '{med.medicine_name}' in your pharmacy.", "info")
            else:
                inv = PharmacyInventory(
                    pharmacy_id=pharmacy.pharmacy_id,
                    medicine_id=med.medicine_id,
                    price=price,
                    stock_quantity=stock_quantity,
                    expiry_date=expiry_date,
                    is_active=True
                )
                db.session.add(inv)
                flash(f"Medicine '{med.medicine_name}' successfully added to your inventory!", "success")

            db.session.commit()
            return redirect(url_for('admin_bp.medicines'))

        except Exception as e:
            db.session.rollback()
            flash(f"Failed to save medicine: {str(e)}", "danger")
            return render_template('admin/add_medicine.html', pharmacy=pharmacy)

    return render_template('admin/add_medicine.html', pharmacy=pharmacy)

@admin_bp.route('/medicines/<int:inventory_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_medicine(inventory_id):
    """Edit Medicine details and inventory properties (Strict ownership protected)."""
    pharmacy = g.pharmacy

    # Strict multi-pharmacy ownership check
    inv = PharmacyInventory.query.filter_by(inventory_id=inventory_id, pharmacy_id=pharmacy.pharmacy_id).first_or_404()
    med = inv.medicine

    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        category = request.form.get('category', '').strip()
        medicine_type = request.form.get('medicine_type', '').strip()
        uses = request.form.get('uses', '').strip()
        purpose = request.form.get('purpose', '').strip()
        how_to_use = request.form.get('how_to_use', '').strip()
        warnings = request.form.get('warnings', '').strip()
        precautions = request.form.get('precautions', '').strip()
        price_str = request.form.get('price', '').strip()
        stock_str = request.form.get('stock_quantity', '').strip()
        expiry_str = request.form.get('expiry_date', '').strip()

        errors = []
        if not medicine_name:
            errors.append("Medicine Name is required.")

        price = None
        try:
            price = float(price_str)
            if price <= 0:
                errors.append("Price must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid price.")

        stock_quantity = 0
        try:
            stock_quantity = int(stock_str)
            if stock_quantity < 0:
                errors.append("Stock quantity cannot be negative.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid stock quantity.")

        expiry_date = None
        if expiry_str:
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append("Invalid expiry date format.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/edit_medicine.html', pharmacy=pharmacy, inventory=inv)

        try:
            # Update master medicine metadata
            med.medicine_name = medicine_name
            med.generic_name = generic_name if generic_name else None
            med.medicine_type = medicine_type if medicine_type else None
            med.category = category if category else None
            med.uses = uses if uses else None
            med.purpose = purpose if purpose else None
            med.how_to_use = how_to_use if how_to_use else None
            med.warnings = warnings if warnings else None
            med.precautions = precautions if precautions else None

            # Update inventory properties
            inv.price = price
            inv.stock_quantity = stock_quantity
            inv.expiry_date = expiry_date
            inv.last_updated = datetime.utcnow()

            db.session.commit()
            flash(f"Updated '{med.medicine_name}' successfully!", "success")
            return redirect(url_for('admin_bp.medicines'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating medicine: {str(e)}", "danger")

    return render_template('admin/edit_medicine.html', pharmacy=pharmacy, inventory=inv)

@admin_bp.route('/medicines/<int:inventory_id>/quick-update', methods=['POST'])
@admin_required
def quick_update(inventory_id):
    """Quickly update price and stock quantity for an inventory item."""
    pharmacy = g.pharmacy
    inv = PharmacyInventory.query.filter_by(inventory_id=inventory_id, pharmacy_id=pharmacy.pharmacy_id).first_or_404()

    price_str = request.form.get('price', '').strip()
    stock_str = request.form.get('stock_quantity', '').strip()

    try:
        if price_str:
            new_price = float(price_str)
            if new_price <= 0:
                flash("Price must be greater than 0.", "danger")
                return redirect(url_for('admin_bp.medicines'))
            inv.price = new_price

        if stock_str:
            new_stock = int(stock_str)
            if new_stock < 0:
                flash("Stock cannot be negative.", "danger")
                return redirect(url_for('admin_bp.medicines'))
            inv.stock_quantity = new_stock

        inv.last_updated = datetime.utcnow()
        db.session.commit()
        flash(f"Updated price (₹{inv.price}) and stock ({inv.stock_quantity}) for '{inv.medicine.medicine_name}'.", "success")

    except ValueError:
        flash("Invalid price or stock format entered.", "danger")

    return redirect(url_for('admin_bp.medicines'))

@admin_bp.route('/medicines/<int:inventory_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(inventory_id):
    """Safely activate or deactivate a medicine inventory item."""
    pharmacy = g.pharmacy
    inv = PharmacyInventory.query.filter_by(inventory_id=inventory_id, pharmacy_id=pharmacy.pharmacy_id).first_or_404()

    inv.is_active = not inv.is_active
    inv.last_updated = datetime.utcnow()
    db.session.commit()

    new_status = "activated" if inv.is_active else "deactivated"
    flash(f"Medicine '{inv.medicine.medicine_name}' has been {new_status}.", "info")
    return redirect(url_for('admin_bp.medicines'))


# ==========================================
# MASTER / OVERALL ADMIN PORTAL
# ==========================================

@admin_bp.route('/master')
@admin_required
def master_dashboard():
    """Overall Super Admin Dashboard with access to all users, pharmacies, medicines, and inventories."""
    pharmacies = Pharmacy.query.order_by(Pharmacy.pharmacy_id.asc()).all()
    medicines = Medicine.query.order_by(Medicine.medicine_name.asc()).all()
    inventories = PharmacyInventory.query.order_by(PharmacyInventory.pharmacy_id.asc(), PharmacyInventory.medicine_id.asc()).all()
    admins = Admin.query.order_by(Admin.admin_id.asc()).all()

    total_pharmacies = len(pharmacies)
    total_medicines = len(medicines)
    total_stock_units = sum(item.stock_quantity for item in inventories if item.is_active)
    total_inventory_value = sum(float(item.price) * item.stock_quantity for item in inventories if item.is_active)

    return render_template(
        'admin/master_dashboard.html',
        pharmacies=pharmacies,
        medicines=medicines,
        inventories=inventories,
        admins=admins,
        total_pharmacies=total_pharmacies,
        total_medicines=total_medicines,
        total_stock_units=total_stock_units,
        total_inventory_value=total_inventory_value
    )


@admin_bp.route('/master/pharmacy/<int:pharmacy_id>/edit', methods=['GET', 'POST'])
@admin_required
def master_edit_pharmacy(pharmacy_id):
    """Master Admin: Edit any pharmacy profile."""
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)

    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        owner_name = request.form.get('owner_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        distance_km = request.form.get('distance_km', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()

        if not shop_name or not owner_name or not phone or not address:
            flash("Shop name, owner name, phone, and address are required.", "danger")
            return render_template('admin/master_edit_pharmacy.html', pharmacy=pharmacy)

        try:
            pharmacy.shop_name = shop_name
            pharmacy.owner_name = owner_name
            pharmacy.phone = phone
            pharmacy.address = address
            pharmacy.distance_km = float(distance_km) if distance_km else None
            pharmacy.latitude = float(latitude) if latitude else None
            pharmacy.longitude = float(longitude) if longitude else None

            db.session.commit()
            flash(f"Pharmacy '{pharmacy.shop_name}' updated successfully!", "success")
            return redirect(url_for('admin_bp.master_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating pharmacy: {str(e)}", "danger")

    return render_template('admin/master_edit_pharmacy.html', pharmacy=pharmacy)


@admin_bp.route('/master/pharmacy/<int:pharmacy_id>/delete', methods=['POST'])
@admin_required
def master_delete_pharmacy(pharmacy_id):
    """Master Admin: Delete a pharmacy and all its inventory items."""
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)
    name = pharmacy.shop_name
    try:
        db.session.delete(pharmacy)
        db.session.commit()
        flash(f"Pharmacy '{name}' and associated inventory deleted successfully.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting pharmacy: {str(e)}", "danger")

    return redirect(url_for('admin_bp.master_dashboard'))


@admin_bp.route('/master/medicine/<int:medicine_id>/edit', methods=['GET', 'POST'])
@admin_required
def master_edit_medicine(medicine_id):
    """Master Admin: Edit global medicine catalog entry."""
    medicine = Medicine.query.get_or_404(medicine_id)

    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name', '').strip()
        generic_name = request.form.get('generic_name', '').strip()
        medicine_type = request.form.get('medicine_type', '').strip()
        category = request.form.get('category', '').strip()
        uses = request.form.get('uses', '').strip()
        purpose = request.form.get('purpose', '').strip()
        how_to_use = request.form.get('how_to_use', '').strip()
        precautions = request.form.get('precautions', '').strip()
        warnings = request.form.get('warnings', '').strip()

        if not medicine_name:
            flash("Medicine name is required.", "danger")
            return render_template('admin/master_edit_medicine.html', medicine=medicine)

        try:
            medicine.medicine_name = medicine_name
            medicine.generic_name = generic_name if generic_name else None
            medicine.medicine_type = medicine_type if medicine_type else None
            medicine.category = category if category else None
            medicine.uses = uses if uses else None
            medicine.purpose = purpose if purpose else None
            medicine.how_to_use = how_to_use if how_to_use else None
            medicine.precautions = precautions if precautions else None
            medicine.warnings = warnings if warnings else None

            db.session.commit()
            flash(f"Global medicine '{medicine.medicine_name}' updated successfully!", "success")
            return redirect(url_for('admin_bp.master_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating medicine: {str(e)}", "danger")

    return render_template('admin/master_edit_medicine.html', medicine=medicine)


@admin_bp.route('/master/medicine/<int:medicine_id>/delete', methods=['POST'])
@admin_required
def master_delete_medicine(medicine_id):
    """Master Admin: Delete a global medicine and its cross-pharmacy inventory links."""
    medicine = Medicine.query.get_or_404(medicine_id)
    name = medicine.medicine_name
    try:
        db.session.delete(medicine)
        db.session.commit()
        flash(f"Medicine '{name}' removed from global catalog.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting medicine: {str(e)}", "danger")

    return redirect(url_for('admin_bp.master_dashboard'))


@admin_bp.route('/master/inventory/<int:inventory_id>/quick-update', methods=['POST'])
@admin_required
def master_quick_update_inventory(inventory_id):
    """Master Admin: Quick update price and stock for any pharmacy's inventory item."""
    inv = PharmacyInventory.query.get_or_404(inventory_id)
    price_str = request.form.get('price', '').strip()
    stock_str = request.form.get('stock_quantity', '').strip()

    try:
        if price_str:
            new_price = float(price_str)
            if new_price <= 0:
                flash("Price must be greater than 0.", "danger")
                return redirect(url_for('admin_bp.master_dashboard'))
            inv.price = new_price

        if stock_str:
            new_stock = int(stock_str)
            if new_stock < 0:
                flash("Stock cannot be negative.", "danger")
                return redirect(url_for('admin_bp.master_dashboard'))
            inv.stock_quantity = new_stock

        inv.last_updated = datetime.utcnow()
        db.session.commit()
        flash(f"Updated '{inv.medicine.medicine_name}' at '{inv.pharmacy.shop_name}': ₹{inv.price}, {inv.stock_quantity} units.", "success")
    except ValueError:
        flash("Invalid price or stock format.", "danger")

    return redirect(url_for('admin_bp.master_dashboard'))

