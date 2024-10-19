from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from model import db, Order, OrderItem
from datetime import datetime
import requests


app = Flask(__name__)
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///order.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Praise2020'

db.init_app(app)

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/order', methods=["POST"])
@jwt_required()
def place_order():
    username = get_jwt_identity()

    jwt_token = request.headers.get('Authorization')
    # return jsonify(jwt_token)

    headers = {
        "Authorization": jwt_token
    }
    cart_url = "http://172.20.10.14:5006/cart/items"
    try:
        response = requests.get(cart_url, headers=headers)
        response.raise_for_status()
        cart_data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"message": f"Failed to fetch cart details: {str(e)}"}), 500
    # if response.status_code == 200:
    #     cart_data = response.json()
    #     return cart_data
    # return jsonify({"error": "Error fetching"}), 400

    # if response.status_code != 200:
    #     return jsonify({"message": "Error fetching cart"}), 400
    
    # cart_data = response.json()
    if not cart_data["cart_items"]:
        return jsonify({"message": "Cart is empty"}), 400
    
    total_price = sum(item['price'] * item['quantity'] for item in cart_data["cart_items"])
    order = Order(username=username, total_price=total_price)
    db.session.add(order)
    db.session.flush()

    for item in cart_data['cart_items']:
        order_item = OrderItem(order_id = order.id, product_name = item['product_name'], quantity=item['quantity'], price=item['price'])
        db.session.add(order_item)
    db.session.commit()

    return jsonify({"message": "Order placed successfully", "order_id": order.id}), 201

@app.route('/order/<int:order_id>', methods=["GET"])
@jwt_required()
def get_order_status(order_id):
    username = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, username=username).first()

    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    return jsonify({
        "order_id": order.id,
        "status": order.status,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "total_price": order.total_price
    }), 200

@app.route('/order/history', methods=['GET'])
@jwt_required()
def get_order_history():
    username = get_jwt_identity()
    orders = Order.query.filter_by(username=username).all()

    if not orders:
        return jsonify({"message": "No orders found"}), 404
    
    order_history = []
    for order in orders:
        order_history.append({
            "order_id": order.id,
            "status": order.status,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [{
                "product_name": item.product_name,
                "quantity": item.quantity,
                "price": item.price
            } for item in order.items]
        })

    return jsonify(order_history), 200

@app.route('/order/<int:order_id>/status', methods=["PUT"])
@jwt_required()
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")

    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    order.status = new_status
    order_updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": "Order status updated successfully"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)