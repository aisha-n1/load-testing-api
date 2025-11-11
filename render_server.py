# render_server.py - Production-Ready API for Cloud Deployment
"""
E-Commerce Load Testing API - Cloud Optimized with Dashboard
=============================================================
COMPLETE version for Render.com/Heroku deployment
Includes BOTH API endpoints AND beautiful dashboard!

Deploy to: Render.com (Free) or Heroku ($7/month)
URL: https://your-app.onrender.com
Dashboard: https://your-app.onrender.com/dashboard

Author: [Your Name]
Project: Multi-Tool Performance Testing Suite
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
import random
from datetime import datetime
import threading
import time

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Get port from environment (cloud platforms provide this)
PORT = int(os.environ.get("PORT", 5000))

# Thread lock for thread-safe operations
stock_lock = threading.Lock()

# In-memory storage (resets on restart - that's okay for demo!)
users_db = {}
products_db = {}
carts_db = {}
orders_db = []
out_of_stock_attempts = 0

# Initialize 100 products on startup
print("🚀 Initializing product catalog...")
for i in range(1, 101):
    initial_stock = random.randint(5, 50)
    products_db[i] = {
        "id": i,
        "name": f"Product {i}",
        "price": round(random.uniform(10, 500), 2),
        "stock": initial_stock,
        "initial_stock": initial_stock,
        "category": random.choice(["Electronics", "Clothing", "Books", "Home"]),
        "times_purchased": 0
    }
print(f"✅ Created {len(products_db)} products")

# ============================================================================
# DASHBOARD HTML - THE BEAUTIFUL WEB INTERFACE!
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
        .badge-info { background: #dbeafe; color: #1e40af; }
        
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
        
        .cloud-badge {
            background: #4f46e5;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛒 E-Commerce API Dashboard <span class="cloud-badge">☁️ LIVE</span></h1>
            <div class="status">● Server Online</div>
            {% if low_stock_count > 0 %}
            <div class="status warning">⚠ {{ low_stock_count }} Products Low Stock</div>
            {% endif %}
            {% if out_of_stock_count > 0 %}
            <div class="status warning">❌ {{ out_of_stock_count }} Products Out of Stock</div>
            {% endif %}
            <p style="margin-top: 15px; color: #666;">
                Live view with REAL stock management - Deployed on Cloud ☁️
            </p>
        </header>
        
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
            <h2>📊 Stock Status (First 20 Products - <a href="/api/stats" style="color: #667eea;">View All Stats</a>)</h2>
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
        // Auto-refresh every 5 seconds to show live updates
        setTimeout(() => location.reload(), 5000);
    </script>
</body>
</html>
"""

# ============================================================================
# DASHBOARD ROUTE
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """
    Beautiful web dashboard showing all data in real-time
    This works perfectly in the cloud!
    """
    
    # Calculate statistics
    in_stock = sum(1 for p in products_db.values() if p['stock'] > 10)
    low_stock = sum(1 for p in products_db.values() if 0 < p['stock'] <= 10)
    out_of_stock = sum(1 for p in products_db.values() if p['stock'] == 0)
    
    # Prepare cart data
    carts_data = []
    for username, cart in carts_db.items():
        total = sum(item['price'] * item['quantity'] for item in cart)
        carts_data.append({
            'user': username,
            'items_count': len(cart),
            'total': total
        })
    
    # Render the beautiful HTML template
    return render_template_string(
        DASHBOARD_HTML,
        products_count=len(products_db),
        in_stock_count=in_stock,
        low_stock_count=low_stock,
        out_of_stock_count=out_of_stock,
        active_users=len(users_db),
        carts_count=len(carts_db),
        orders_count=len(orders_db),
        sample_products=list(products_db.values())[:20],  # First 20 for display
        carts_data=carts_data,
        recent_orders=orders_db[-10:] if orders_db else [],
        out_of_stock_attempts=out_of_stock_attempts
    )

# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint - required by most cloud platforms"""
    return jsonify({
        "status": "healthy",
        "products": len(products_db),
        "orders": len(orders_db),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/')
def homepage():
    """Homepage - shows API information"""
    return jsonify({
        "message": "🛒 E-Commerce Load Testing API",
        "version": "2.0",
        "status": "online",
        "description": "Production-ready REST API for performance testing",
        "endpoints": {
            "health": "/health",
            "products": "/api/products",
            "product_detail": "/api/products/<id>",
            "search": "/api/search?q=<query>",
            "login": "/api/auth/login (POST)",
            "cart": "/api/cart (GET/POST)",
            "checkout": "/api/checkout (POST)"
        },
        "statistics": {
            "total_products": len(products_db),
            "in_stock": sum(1 for p in products_db.values() if p['stock'] > 0),
            "out_of_stock": sum(1 for p in products_db.values() if p['stock'] == 0),
            "total_orders": len(orders_db),
            "active_users": len(users_db),
            "active_carts": len(carts_db)
        },
        "github": "https://github.com/yourusername/load-testing-suite",
        "author": "[Your Name]"
    }), 200

# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login - returns auth token"""
    time.sleep(random.uniform(0.1, 0.3))  # Simulate processing
    
    data = request.get_json() or {}
    username = data.get('username', 'guest')
    
    # Generate unique token
    token = f"token_{username}_{int(time.time())}_{random.randint(1000,9999)}"
    
    # Store session
    users_db[token] = {
        "username": username,
        "login_time": datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "token": token,
        "username": username,
        "message": "Login successful"
    }), 200

# ============================================================================
# PRODUCTS
# ============================================================================

@app.route('/api/products')
def list_products():
    """List products with pagination"""
    time.sleep(random.uniform(0.1, 0.3))
    
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    product_list = list(products_db.values())[start:end]
    
    return jsonify({
        "products": product_list,
        "page": page,
        "per_page": per_page,
        "total": len(products_db)
    }), 200

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Get specific product by ID"""
    time.sleep(random.uniform(0.05, 0.15))
    
    if product_id in products_db:
        product = products_db[product_id].copy()
        
        # Add availability status
        if product['stock'] == 0:
            product['available'] = False
            product['status'] = 'Out of Stock'
        elif product['stock'] < 10:
            product['available'] = True
            product['status'] = 'Low Stock'
        else:
            product['available'] = True
            product['status'] = 'In Stock'
        
        return jsonify(product), 200
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/api/search')
def search_products():
    """Search products by keyword"""
    time.sleep(random.uniform(0.15, 0.4))
    
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    # Search in name and category, only in-stock items
    results = [
        product for product in products_db.values()
        if (query in product['name'].lower() or query in product['category'].lower())
        and product['stock'] > 0
    ]
    
    return jsonify({
        "query": query,
        "results": results[:20],
        "count": len(results)
    }), 200

# ============================================================================
# SHOPPING CART
# ============================================================================

def get_user_from_token(token):
    """Extract username from auth token"""
    token = token.replace('Bearer ', '')
    user_info = users_db.get(token)
    return user_info['username'] if user_info else None

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """View shopping cart"""
    time.sleep(random.uniform(0.05, 0.1))
    
    token = request.headers.get('Authorization', '')
    username = get_user_from_token(token)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    cart = carts_db.get(username, [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    return jsonify({
        "cart": cart,
        "items_count": len(cart),
        "total": round(total, 2)
    }), 200

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart with stock validation"""
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
    
    # STOCK VALIDATION - Thread-safe
    with stock_lock:
        product = products_db[product_id]
        
        if product['stock'] < quantity:
            out_of_stock_attempts += 1
            return jsonify({
                "error": "Insufficient stock",
                "message": f"Only {product['stock']} items available",
                "requested": quantity,
                "available": product['stock']
            }), 400
    
    # Add to cart
    if username not in carts_db:
        carts_db[username] = []
    
    # Check if product already in cart
    existing_item = None
    for item in carts_db[username]:
        if item['product_id'] == product_id:
            existing_item = item
            break
    
    if existing_item:
        new_quantity = existing_item['quantity'] + quantity
        if new_quantity > product['stock']:
            out_of_stock_attempts += 1
            return jsonify({
                "error": "Insufficient stock",
                "message": f"Cart has {existing_item['quantity']}, only {product['stock']} available total"
            }), 400
        existing_item['quantity'] += quantity
    else:
        carts_db[username].append({
            "product_id": product_id,
            "name": product['name'],
            "price": product['price'],
            "quantity": quantity
        })
    
    return jsonify({
        "message": "Item added to cart",
        "cart_items": len(carts_db[username])
    }), 201

# ============================================================================
# CHECKOUT
# ============================================================================

@app.route('/api/checkout', methods=['POST'])
def checkout():
    """Process checkout and reduce stock"""
    time.sleep(random.uniform(0.3, 0.8))
    
    token = request.headers.get('Authorization', '')
    username = get_user_from_token(token)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    cart = carts_db.get(username, [])
    
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
    
    data = request.get_json() or {}
    payment_method = data.get('payment_method', 'credit_card')
    shipping_address = data.get('shipping_address', 'Not provided')
    
    # FINAL STOCK CHECK AND REDUCTION - Thread-safe
    with stock_lock:
        # Verify all items still in stock
        for item in cart:
            product_id = item['product_id']
            quantity = item['quantity']
            
            if product_id not in products_db:
                return jsonify({
                    "error": "Product no longer available",
                    "product_id": product_id
                }), 400
            
            if products_db[product_id]['stock'] < quantity:
                return jsonify({
                    "error": "Insufficient stock during checkout",
                    "message": f"Product {product_id} only has {products_db[product_id]['stock']} left",
                    "product_id": product_id
                }), 400
        
        # All items available - reduce stock now
        for item in cart:
            product_id = item['product_id']
            quantity = item['quantity']
            products_db[product_id]['stock'] -= quantity
            products_db[product_id]['times_purchased'] += 1
    
    # Calculate total
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    # Simulate payment processing (5% failure rate)
    if random.random() < 0.05:
        # Payment failed - restore stock
        with stock_lock:
            for item in cart:
                products_db[item['product_id']]['stock'] += item['quantity']
        
        return jsonify({
            "error": "Payment processing failed",
            "message": "Please try again"
        }), 500
    
    # Success - create order
    order_id = f"ORDER_{username}_{int(time.time())}"
    
    order_items = []
    for item in cart:
        order_items.append({
            "product_id": item['product_id'],
            "name": item['name'],
            "quantity": item['quantity'],
            "price": item['price']
        })
    
    orders_db.append({
        "order_id": order_id,
        "username": username,
        "total": round(total, 2),
        "items_count": len(cart),
        "items": order_items,
        "payment_method": payment_method,
        "shipping_address": shipping_address,
        "timestamp": datetime.now().isoformat()
    })
    
    # Clear cart
    carts_db[username] = []
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": round(total, 2),
        "items_purchased": len(order_items),
        "payment_method": payment_method,
        "shipping_address": shipping_address,
        "estimated_delivery": "3-5 business days",
        "message": "Order placed successfully!"
    }), 200

# ============================================================================
# ADDITIONAL ENDPOINTS
# ============================================================================

@app.route('/api/user/<int:user_id>')
def get_user(user_id):
    """Get user information (fake data for testing)"""
    time.sleep(random.uniform(0.05, 0.15))
    
    return jsonify({
        "id": user_id,
        "username": f"user_{user_id}",
        "email": f"user_{user_id}@example.com",
        "joined": "2024-01-01",
        "orders_count": random.randint(0, 50)
    }), 200

@app.route('/api/stats')
def get_stats():
    """Get system statistics - useful for monitoring"""
    return jsonify({
        "products": {
            "total": len(products_db),
            "in_stock": sum(1 for p in products_db.values() if p['stock'] > 0),
            "low_stock": sum(1 for p in products_db.values() if 0 < p['stock'] <= 10),
            "out_of_stock": sum(1 for p in products_db.values() if p['stock'] == 0)
        },
        "orders": {
            "total": len(orders_db),
            "total_revenue": sum(order['total'] for order in orders_db)
        },
        "users": {
            "active_sessions": len(users_db),
            "active_carts": len(carts_db)
        },
        "validation": {
            "blocked_attempts": out_of_stock_attempts
        }
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal Server Error",
        "message": "Something went wrong on our end"
    }), 500

# ============================================================================
# START SERVER
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 E-Commerce Load Testing API - Production Mode")
    print("=" * 70)
    print(f"📍 Port: {PORT}")
    print(f"📦 Products: {len(products_db)}")
    print(f"🌐 Ready to accept requests!")
    print("=" * 70)
    
    # Run server
    # debug=False for production
    # host='0.0.0.0' to accept external requests
    app.run(debug=False, host='0.0.0.0', port=PORT)