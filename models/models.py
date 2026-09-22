from datetime import date, datetime, timezone
from models.database import db

def utc_now():
    return datetime.now(timezone.utc)

class Admin(db.Model):
    __tablename__ = 'admins'

    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # One-to-one relationship with Pharmacy
    pharmacy = db.relationship('Pharmacy', backref='admin', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Admin {self.username}>"

class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'

    pharmacy_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.admin_id', ondelete='CASCADE'), unique=True, nullable=False)
    shop_name = db.Column(db.String(150), nullable=False)
    owner_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    distance_km = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # One-to-many relationship with PharmacyInventory
    inventory_items = db.relationship('PharmacyInventory', backref='pharmacy', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Pharmacy {self.shop_name}>"

class Medicine(db.Model):
    __tablename__ = 'medicines'

    medicine_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    medicine_name = db.Column(db.String(150), nullable=False, index=True)
    generic_name = db.Column(db.String(150), nullable=True, index=True)
    medicine_type = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    uses = db.Column(db.Text, nullable=True)
    purpose = db.Column(db.Text, nullable=True)
    how_to_use = db.Column(db.Text, nullable=True)
    warnings = db.Column(db.Text, nullable=True)
    precautions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # One-to-many relationship with PharmacyInventory
    inventory_items = db.relationship('PharmacyInventory', backref='medicine', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Medicine {self.medicine_name}>"

class PharmacyInventory(db.Model):
    __tablename__ = 'pharmacy_inventory'

    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacies.pharmacy_id', ondelete='CASCADE'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.medicine_id', ondelete='CASCADE'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_updated = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('pharmacy_id', 'medicine_id', name='uq_pharmacy_medicine'),
    )

    @property
    def status(self):
        """Dynamic inventory status based on active flag, expiry date, and stock quantity."""
        if not self.is_active:
            return "Inactive"
        if self.expiry_date and self.expiry_date < date.today():
            return "Expired"
        if self.stock_quantity <= 0:
            return "Out of Stock"
        return "Available"

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < date.today())

    def __repr__(self):
        return f"<PharmacyInventory Pharmacy:{self.pharmacy_id} Med:{self.medicine_id}>"


