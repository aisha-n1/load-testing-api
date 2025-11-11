# render_server.py - WITH RESET FUNCTIONALITY
"""
E-Commerce Load Testing API with RESET button!
=====================================================
- Run load tests
- Stock depletes, orders created
- Click RESET button to restore everything
- Perfect for demos and presentations!

🔄 Reset endpoint: /api/admin/reset (POST)
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
import random
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get("PORT", 5000))
stock_lock = threading.Lock()

# Storage
users_db = {}
products_db = {}
carts_db = {}
orders_db = []
out_of_stock_attempts = 0

def initialize_products():
    """Initialize or RESET products to starting state, ensuring <= 30 low stock."""
    global products_db
    products_db = {}
    
    print("🔄 Initializing product catalog...")
    
    # Randomly choose a number of products (between 5 and 30) to start with low stock
    target_low_stock_count = random.randint(5, 30) 
    
    low_stock_ids = random.sample(range(1, 101), target_low_stock_count)
    
    for i in range(1, 101):
        if i in low_stock_ids:
            # Low Stock (5 to 10 items)
            initial_stock = random.randint(5, 10)
        else:
            # Normal Stock (11 to 50 items)
            initial_stock = random.randint(11, 50)
            
        products_db[i] = {
            "id": i,
            "name": f"Product {i}",
            "price": round(random.uniform(10, 500), 2),
            "stock": initial_stock,
            "initial_stock": initial_stock,
            "category": random.choice(["Electronics", "Clothing", "Books", "Home"]),
            "times_purchased": 0
        }
    print(f"✅ Created {len(products_db)} products. {target_low_stock_count} products started low.")

# Initialize on startup
initialize_products() 
# ============================================================================
# DASHBOARD HTML - WITH RESET BUTTON!
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>E-Commerce API Dashboard - LIVE</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
            position: relative;
        }
        h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .status {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 5px;
        }
        .status.warning { background: #f59e0b; }
        .cloud-badge {
            background: #4f46e5;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-left: 10px;
        }
        .reset-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s;
        }
        .reset-btn:hover {
            background: #dc2626;
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .stat {
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            text-align: center;
            margin: 20px 0;
        }
        .stat.warning { color: #f59e0b; }
        .stat.danger { color: #ef4444; }
        .label {
            text-align: center;
            color: #666;
            font-size: 1.1em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        tr:hover { background: #f8f9fa; }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .badge-success { background: #d1fae5; color: #065f46; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-danger { background: #fee2e2; color: #991b1b; }
        .stock-bar {
            width: 100%;
            height: 8px;
            background: #fee2e2;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .stock-fill {
            height: 100%;
            background: #10b981;
            transition: width 0.3s;
        }
        .stock-fill.low { background: #f59e0b; }
        .stock-fill.out { background: #ef4444; width: 100% !important; }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 5px;
            transition: all 0.3s;
        }
        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .alert {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
        }
        .alert.danger {
            background: #fee2e2;
            border-left-color: #ef4444;
        }
        .alert.success {
            background: #d1fae5;
            border-left-color: #10b981;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <button class="reset-btn" onclick="resetSystem()">🔄 RESET SYSTEM</button>
            <h1>🛒 E-Commerce API Dashboard <span class="cloud-badge">☁️ LIVE</span></h1>
            <div class="status">● Server Online</div>
            {% if low_stock_count > 0 %}
            <div class="status warning">⚠ {{ low_stock_count }} Products Low Stock</div>
            {% endif %}
            {% if out_of_stock_count > 0 %}
            <div class="status warning">❌ {{ out_of_stock_count }} Products Out of Stock</div>
            {% endif %}
            <p style="margin-top: 15px; color: #666;">
                Live view with REAL stock management - Click RESET to restore inventory
            </p>
        </header>
        
        <div id="alert-area"></div>
        
        {% if out_of_stock_attempts > 0 %}
        <div class="alert danger">
            <strong>🚫 Stock Validation Working!</strong><br>
            {{ out_of_stock_attempts }} purchase attempts were blocked due to insufficient stock.
        </div>
        {% endif %}
        
        <div class="grid">
            <div class="card">
                <h2>📦 Products</h2>
                <div class="stat">{{ products_count }}</div>
                <div class="label">Total Products</div>
                <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    ✅ In Stock: {{ in_stock_count }}<br>
                    ⚠️ Low Stock: {{ low_stock_count }}<br>
                    ❌ Out: {{ out_of_stock_count }}
                </div>
            </div>
            
            <div class="card">
                <h2>👥 Active Sessions</h2>
                <div class="stat">{{ active_users }}</div>
                <div class="label">Logged In Users</div>
            </div>
            
            <div class="card">
                <h2>🛒 Shopping Carts</h2>
                <div class="stat">{{ carts_count }}</div>
                <div class="label">Active Carts</div>
            </div>
            
            <div class="card">
                <h2>✅ Orders</h2>
                <div class="stat">{{ orders_count }}</div>
                <div class="label">Completed Orders</div>
            </div>
            
            <div class="card">
                <h2>🚫 Blocked</h2>
                <div class="stat {% if out_of_stock_attempts > 0 %}warning{% endif %}">{{ out_of_stock_attempts }}</div>
                <div class="label">Out-of-Stock Attempts</div>
            </div>
        </div>
        
        <div class="card">
            <h2>📊 Stock Status (First 20 Products)</h2>
            <div style="max-height: 600px; overflow-y: auto;">
            <table>
                <thead style="position: sticky; top: 0; background: white; z-index: 10;">
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Stock Level</th>
                        <th>Purchased</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in sample_products %}
                    <tr>
                        <td>{{ product.id }}</td>
                        <td>{{ product.name }}</td>
                        <td>${{ "%.2f"|format(product.price) }}</td>
                        <td>
                            {% if product.stock == 0 %}
                            <span class="badge badge-danger">OUT OF STOCK</span>
                            {% elif product.stock < 10 %}
                            <span class="badge badge-warning">{{ product.stock }} left</span>
                            {% else %}
                            <span class="badge badge-success">{{ product.stock }}</span>
                            {% endif %}
                        </td>
                        <td style="width: 150px;">
                            <div class="stock-bar">
                                {% set percentage = (product.stock / product.initial_stock * 100) if product.initial_stock > 0 else 0 %}
                                <div class="stock-fill {% if product.stock == 0 %}out{% elif percentage < 30 %}low{% endif %}" 
                                    style="width: {{ percentage }}%"></div>
                            </div>
                            <small style="color: #666;">{{ product.stock }}/{{ product.initial_stock }}</small>
                        </td>
                        <td>{{ product.times_purchased }}x</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            </div>
        </div>
        
        <div class="card">
            <h2>🛒 Active Shopping Carts</h2>
            {% if carts_data %}
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Items</th>
                        <th>Total Value</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cart in carts_data %}
                    <tr>
                        <td>{{ cart.user }}</td>
                        <td>{{ cart.items_count }}</td>
                        <td>${{ "%.2f"|format(cart.total) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999; padding: 20px;">
                No active carts yet. Run load tests to see carts populate!
            </p>
            {% endif %}
        </div>
        
        <div class="card">
            <h2>✅ Recent Orders (Last 10)</h2>
            {% if recent_orders %}
            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Items</th>
                        <th>Total</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in recent_orders %}
                    <tr>
                        <td>{{ order.order_id }}</td>
                        <td>{{ order.items_count }} items</td>
                        <td><strong>${{ "%.2f"|format(order.total) }}</strong></td>
                        <td><span class="badge badge-success">✓ Completed</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #999; padding: 20px;">
                No orders yet. Run load tests to see orders!
            </p>
            {% endif %}
        </div>
        
        <button style="position: fixed; bottom: 30px; right: 30px; border-radius: 50%; width: 60px; height: 60px; font-size: 1.5em;" 
                onclick="location.reload()">🔄</button>
    </div>
    
    <script>
        // Auto-refresh every 5 seconds
        setTimeout(() => location.reload(), 5000);
        
        // Reset system function
        async function resetSystem() {
            if (!confirm('Reset the entire system? This will:\\n\\n✓ Restore all product stock\\n✓ Clear all orders\\n✓ Clear all carts\\n✓ Clear all sessions\\n\\nContinue?')) {
                return;
            }
            
            const alertArea = document.getElementById('alert-area');
            alertArea.innerHTML = '<div class="alert">⏳ Resetting system...</div>';
            
            try {
                const response = await fetch('/api/admin/reset', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alertArea.innerHTML = '<div class="alert success">✅ ' + data.message + '</div>';
                    setTimeout(() => location.reload(), 1500);
                } else {
                    alertArea.innerHTML = '<div class="alert danger">❌ Reset failed: ' + data.message + '</div>';
                }
            } catch (error) {
                alertArea.innerHTML = '<div class="alert danger">❌ Error: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    """Dashboard with reset button"""
    in_stock = sum(1 for p in products_db.values() if p['stock'] > 10)
    low_stock = sum(1 for p in products_db.values() if 0 < p['stock'] <= 10)
    out_of_stock = sum(1 for p in products_db.values() if p['stock'] == 0)
    
    carts_data = []
    for username, cart in carts_db.items():
        total = sum(item['price'] * item['quantity'] for item in cart)
        carts_data.append({
            'user': username,
            'items_count': len(cart),
            'total': total
        })
    
    return render_template_string(
        DASHBOARD_HTML,
        products_count=len(products_db),
        in_stock_count=in_stock,
        low_stock_count=low_stock,
        out_of_stock_count=out_of_stock,
        active_users=len(users_db),
        carts_count=len(carts_db),
        orders_count=len(orders_db),
        sample_products=list(products_db.values())[:20],
        carts_data=carts_data,
        recent_orders=orders_db[-10:] if orders_db else [],
        out_of_stock_attempts=out_of_stock_attempts
    )

# ============================================================================
# RESET ENDPOINT - THE MAGIC BUTTON!
# ============================================================================

@app.route('/api/admin/reset', methods=['POST'])
def reset_system():
    """
    RESET endpoint - Restores everything to initial state
    Perfect for demos and presentations!
    """
    global users_db, carts_db, orders_db, out_of_stock_attempts
    
    try:
        with stock_lock:
            # Reinitialize products (fresh stock!)
            initialize_products()
            
            # Clear everything else
            users_db = {}
            carts_db = {}
            orders_db = []
            out_of_stock_attempts = 0
        
        return jsonify({
            "success": True,
            "message": "System reset successfully! All stock restored, orders cleared.",
            "stats": {
                "products": len(products_db),
                "users": len(users_db),
                "carts": len(carts_db),
                "orders": len(orders_db)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ============================================================================
# ALL YOUR OTHER ENDPOINTS (same as before)
# ============================================================================

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "products": len(products_db),
        "orders": len(orders_db)
    }), 200

@app.route('/')
def homepage():
    return jsonify({
        "message": "🛒 E-Commerce Load Testing API",
        "version": "2.0 - WITH RESET!",
        "status": "online",
        "endpoints": {
            "dashboard": "/dashboard (WITH RESET BUTTON!)",
            "reset": "/api/admin/reset (POST)",
            "health": "/health",
            "products": "/api/products",
            "login": "/api/auth/login (POST)",
            "cart": "/api/cart",
            "checkout": "/api/checkout (POST)"
        },
        "statistics": {
            "total_products": len(products_db),
            "in_stock": sum(1 for p in products_db.values() if p['stock'] > 0),
            "total_orders": len(orders_db)
        }
    }), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    time.sleep(random.uniform(0.1, 0.3))
    data = request.get_json() or {}
    username = data.get('username', 'guest')
    token = f"token_{username}_{int(time.time())}_{random.randint(1000,9999)}"
    users_db[token] = {
        "username": username,
        "login_time": datetime.now().isoformat()
    }
    return jsonify({
        "success": True,
        "token": token,
        "username": username
    }), 200

@app.route('/api/products')
def list_products():
    time.sleep(random.uniform(0.1, 0.3))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page
    return jsonify({
        "products": list(products_db.values())[start:end],
        "page": page,
        "per_page": per_page,
        "total": len(products_db)
    }), 200

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    time.sleep(random.uniform(0.05, 0.15))
    if product_id in products_db:
        product = products_db[product_id].copy()
        product['available'] = product['stock'] > 0
        product['status'] = 'In Stock' if product['stock'] > 10 else ('Low Stock' if product['stock'] > 0 else 'Out of Stock')
        return jsonify(product), 200
    return jsonify({"error": "Product not found"}), 404

@app.route('/api/search')
def search_products():
    time.sleep(random.uniform(0.15, 0.4))
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({"error": "No search query"}), 400
    results = [p for p in products_db.values() if query in p['name'].lower() or query in p['category'].lower() and p['stock'] > 0]
    return jsonify({"query": query, "results": results[:20], "count": len(results)}), 200

def get_user_from_token(token):
    token = token.replace('Bearer ', '')
    user_info = users_db.get(token)
    return user_info['username'] if user_info else None

@app.route('/api/cart', methods=['GET'])
def get_cart():
    time.sleep(random.uniform(0.05, 0.1))
    token = request.headers.get('Authorization', '')
    username = get_user_from_token(token)
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    cart = carts_db.get(username, [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    return jsonify({"cart": cart, "items_count": len(cart), "total": round(total, 2)}), 200

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    global out_of_stock_attempts
    time.sleep(random.uniform(0.1, 0.2))
    token = request.headers.get('Authorization', '')
    username = get_user_from_token(token)
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    if product_id not in products_db:
        return jsonify({"error": "Product not found"}), 404
    with stock_lock:
        product = products_db[product_id]
        if product['stock'] < quantity:
            out_of_stock_attempts += 1
            return jsonify({"error": "Insufficient stock", "available": product['stock']}), 400
    if username not in carts_db:
        carts_db[username] = []
    existing = next((item for item in carts_db[username] if item['product_id'] == product_id), None)
    if existing:
        existing['quantity'] += quantity
    else:
        carts_db[username].append({
            "product_id": product_id,
            "name": product['name'],
            "price": product['price'],
            "quantity": quantity
        })
    return jsonify({"message": "Added to cart", "cart_items": len(carts_db[username])}), 201

@app.route('/api/checkout', methods=['POST'])
def checkout():
    time.sleep(random.uniform(0.3, 0.8))
    token = request.headers.get('Authorization', '')
    username = get_user_from_token(token)
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    cart = carts_db.get(username, [])
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
    with stock_lock:
        for item in cart:
            if products_db[item['product_id']]['stock'] < item['quantity']:
                return jsonify({"error": "Insufficient stock"}), 400
        for item in cart:
            products_db[item['product_id']]['stock'] -= item['quantity']
            products_db[item['product_id']]['times_purchased'] += 1
    total = sum(item['price'] * item['quantity'] for item in cart)
    if random.random() < 0.05:
        with stock_lock:
            for item in cart:
                products_db[item['product_id']]['stock'] += item['quantity']
        return jsonify({"error": "Payment failed"}), 500
    order_id = f"ORDER_{username}_{int(time.time())}"
    orders_db.append({
        "order_id": order_id,
        "username": username,
        "total": round(total, 2),
        "items_count": len(cart),
        "timestamp": datetime.now().isoformat()
    })
    carts_db[username] = []
    return jsonify({"success": True, "order_id": order_id, "total": round(total, 2)}), 200

@app.route('/api/stats')
def get_stats():
    return jsonify({
        "products": {
            "total": len(products_db),
            "in_stock": sum(1 for p in products_db.values() if p['stock'] > 0),
            "out_of_stock": sum(1 for p in products_db.values() if p['stock'] == 0)
        },
        "orders": {
            "total": len(orders_db)
        },
        "users": {
            "active": len(users_db),
            "carts": len(carts_db)
        }
    }), 200

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 E-Commerce Load Testing API - WITH RESET!")
    print("=" * 70)
    print(f"📍 Port: {PORT}")
    print(f"📦 Products: {len(products_db)}")
    print(f"🔄 Reset available at: /api/admin/reset (POST)")
    print("=" * 70)
    app.run(debug=False, host='0.0.0.0', port=PORT)

