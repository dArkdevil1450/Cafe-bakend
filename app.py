import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app) # Allows React to talk to Python

# Ensure we have a table to store the specific food items
def init_db():
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS orders')
    # The upgraded vault with the total_price drawer
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_no TEXT,
            items TEXT,
            total_price REAL,
            cafe_id TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.json
    
    # Grab data from frontend
    table_no = data.get('table_no', 'Unknown')
    items = data.get('items', [])
    total_price = data.get('total_price', 0.0) 
    
    # Compress the food list into a single text string so it fits in the drawer perfectly
    items_string = json.dumps(items)
    
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    
    # Save EVERYTHING into the main orders cabinet
    cursor.execute(
        "INSERT INTO orders (table_no, items, total_price, status) VALUES (?, ?, ?, 'pending')", 
        (table_no, items_string, total_price)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Order sent to kitchen!"})

# --- NEW STAFF DASHBOARD APIs ---

# 1. Ask the database for all active orders
@app.route('/get_orders', methods=['GET'])
def get_orders():
    conn = sqlite3.connect('cafe_system.db')
    cursor = conn.cursor()
    # Notice we added total_price here
    cursor.execute("SELECT id, table_no, items, status, total_price FROM orders WHERE status != 'paid'")
    orders = cursor.fetchall()
    conn.close()
    
    order_list = []
    for order in orders:
        order_list.append({
            "id": order[0],
            "table_no": order[1],
            "items": order[2],
            "status": order[3],
            "total_price": order[4] # Passing the money to the frontend
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
    
# Force the database to rebuild EVERY time the server wakes up
init_db()

if __name__ == '__main__':
    print("🚀 Server starting... Waiting for orders on port 5000!")
    app.run(debug=True, port=5000)
