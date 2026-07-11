import db_helper
import os

def test_db_operations():
    print("[TEST] Starting local database operations test...")
    
    # 1. Initialize DB
    db_helper.init_db()
    print("[SUCCESS] Database initialized successfully.")
    
    # 2. Add inventory item
    item_added = db_helper.add_or_update_inventory("Maggi Noodles", 50, 12.50)
    print(f"[SUCCESS] Added item: {item_added} (50 units @ Rs. 12.50)")
    
    # 3. Add credit entry
    customer_added = db_helper.add_udhari("Ramesh Kumar", 250.0, "Bought 20 packets of Maggi on credit")
    print(f"[SUCCESS] Credit entry logged for: {customer_added} (Rs. 250.0)")
    
    # 4. Read data
    inventory_items = db_helper.get_inventory()
    print(f"[INFO] Inventory list: {inventory_items}")
    
    udhari_logs = db_helper.get_udhari_summary()
    print(f"[INFO] Outstanding balances: {udhari_logs}")
    
    # 5. Check if Excel was written
    excel_path = db_helper.EXCEL_PATH
    if os.path.exists(excel_path):
        print(f"[SUCCESS] Excel workbook was generated and saved at: {excel_path}")
    else:
        print("[ERROR] FAILED: Excel workbook was not created.")

if __name__ == "__main__":
    test_db_operations()
