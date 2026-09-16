import os
import sys
from datetime import datetime

# Setup Flask application context
from app import app
from models.database import db
from models.models import Pharmacy, Medicine, PharmacyInventory, Admin
from werkzeug.security import generate_password_hash

def import_data():
    dataset_path = 'dataset.txt'
    
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found.")
        return

    with app.app_context():
        # Read the file
        with open(dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("File is empty.")
            return
            
        header = lines[0].strip().split('\t')
        print(f"Found headers: {header}")
        
        # Keep track of created entities to avoid duplicates
        pharmacies = {} # name -> id
        medicines = {} # name -> id
        
        # Load existing pharmacies
        for p in Pharmacy.query.all():
            pharmacies[p.shop_name] = p.pharmacy_id
            
        # Load existing medicines
        for m in Medicine.query.all():
            medicines[m.medicine_name] = m.medicine_id
            
        # Create a default admin if none exists
        default_admin = Admin.query.first()
        admin_id_counter = 1
        
        count = 0
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            # medicine_id, medicine_name, item_type, pharmacy_name, pharmacy_address, distance, price, availability, stock
            if len(parts) < 9:
                print(f"Skipping malformed line: {line}")
                continue
                
            med_id_str, med_name, item_type, pharm_name, pharm_addr, distance_str, price_str, availability, stock_str = parts[:9]
            
            # Handle empty values
            distance = float(distance_str) if distance_str else 0.0
            price = float(price_str) if price_str else 0.0
            stock = int(stock_str) if stock_str else 0
            is_active = (availability.strip().lower() == 'available' and stock > 0)
            
            # Create Pharmacy if it doesn't exist
            if pharm_name not in pharmacies:
                admin_username = f"admin_{pharm_name.replace(' ', '').lower()}"
                
                # Check if admin username exists
                existing_admin = Admin.query.filter_by(username=admin_username).first()
                if not existing_admin:
                    new_admin = Admin(
                        username=admin_username,
                        password_hash=generate_password_hash("password123")
                    )
                    db.session.add(new_admin)
                    db.session.flush() # Get the ID
                    admin_id = new_admin.admin_id
                else:
                    admin_id = existing_admin.admin_id
                
                new_pharmacy = Pharmacy(
                    admin_id=admin_id,
                    shop_name=pharm_name,
                    owner_name="Default Owner",
                    address=pharm_addr,
                    phone="0000000000",
                    distance_km=distance
                )
                db.session.add(new_pharmacy)
                db.session.flush()
                pharmacies[pharm_name] = new_pharmacy.pharmacy_id
                print(f"Created Pharmacy: {pharm_name}")
                
            # Create Medicine if it doesn't exist
            if med_name not in medicines:
                new_med = Medicine(
                    medicine_name=med_name,
                    generic_name=med_name.split(' ')[0], # simple generic name
                    medicine_type=item_type,
                    category="General"
                )
                db.session.add(new_med)
                db.session.flush()
                medicines[med_name] = new_med.medicine_id
                print(f"Created Medicine: {med_name}")
                
            # Create PharmacyInventory
            pharm_id = pharmacies[pharm_name]
            med_id = medicines[med_name]
            
            # Check if inventory already exists
            inv = PharmacyInventory.query.filter_by(pharmacy_id=pharm_id, medicine_id=med_id).first()
            if not inv:
                new_inv = PharmacyInventory(
                    pharmacy_id=pharm_id,
                    medicine_id=med_id,
                    price=price,
                    stock_quantity=stock,
                    is_active=is_active
                )
                db.session.add(new_inv)
            else:
                inv.price = price
                inv.stock_quantity = stock
                inv.is_active = is_active
                
            count += 1
            
        db.session.commit()
        print(f"Successfully processed {count} inventory records.")

if __name__ == '__main__':
    import_data()
