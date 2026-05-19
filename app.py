import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allows React to talk to Python

# Ensure we have a table to store the specific food items
def init_db():
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    
    # Cabinet 1: The main orders table (This was missing and caused yesterday's crash!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_no TEXT,
            items TEXT,
            cafe_id TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Cabinet 2: The specific items inside the order (What you originally had)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_name TEXT,
            price REAL,
            quantity INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    
    # Grab the data sent from your React app
    table_no = data.get('table_no', 'Unknown')
    items = data.get('items', [])
    
    # Connect to the vault
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    
    try:
        # 1. Create the main order (Assuming this is Cafe #1 for now)
        cursor.execute("INSERT INTO orders (cafe_id, table_no, status) VALUES (?, ?, 'Pending')", (1, table_no))
        order_id = cursor.lastrowid # Gets the unique ID of the order we just made
        
        # 2. Loop through the cart and save each dish to this order
        for item in items:
            cursor.execute("INSERT INTO order_items (order_id, item_name, price, quantity) VALUES (?, ?, ?, ?)", 
                           (order_id, item.get('name'), item.get('price'), item.get('quantity', 1)))
        
        conn.commit()
        print(f"\n✅ SUCCESS: Order #{order_id} saved for Table {table_no}!")
        print(f"Dishes ordered: {len(items)}")
        print("-" * 30)
        
    except Exception as e:
        print("Database Error:", e)
        return jsonify({"status": "error", "message": "Failed to save order"}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "order_id": order_id}), 200

# --- NEW STAFF DASHBOARD APIs ---

# 1. Ask the database for all active orders
@app.route('/get_orders', methods=['GET'])
def get_orders():
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    # We only want orders that haven't been paid yet
    cursor.execute("SELECT id, table_no, items, status FROM orders WHERE status != 'paid'")
    orders = cursor.fetchall()
    conn.close()
    
    # Format the data cleanly for the frontend
    order_list = []
    for order in orders:
        order_list.append({
            "id": order[0],
            "table_no": order[1],
            "items": order[2],
            "status": order[3]
        })
    return jsonify(order_list)

# 2. Update the status (Pending -> Cooked -> Paid)
@app.route('/update_order', methods=['POST'])
def update_order():
    data = request.json
    order_id = data.get('id')
    new_status = data.get('status')
    
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Order {order_id} updated to {new_status}!"})
    
if __name__ == '__main__':
    print("🚀 Server starting... Waiting for orders on port 5000!")
    app.run(debug=True, port=5000)
