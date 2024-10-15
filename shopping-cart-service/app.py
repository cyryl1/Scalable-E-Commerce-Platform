from flask import Flask, request, jsonify
from models import db, Cart, CartItem
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
import requests


app = Flask(__name__)
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shoppingcart_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Praise2020'

db.init_app(app)

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()


@app.route("/cart", methods=["POST"])
@jwt_required()
def create_cart():
    username = get_jwt_identity()
    cart = Cart.query.filter_by(username=username).first()
    if cart:
        return jsonify({"message": "Cart already exists"}), 400
    new_cart = Cart(username=username, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.session.add(new_cart)
    db.session.commit()

    return ({"message": "New cart created", "cart_id": new_cart.id}), 201

@app.route("/cart/items", methods=["GET"])
@jwt_required()
def get_cart_items():
    username = get_jwt_identity

    cart = Cart.query.filter_by(username=username).first()
    if not cart:
        return ({"message": "Cart not found"}), 404
    
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

    cart_list = [{
        "product_id": item.product_id,
        "quantity": item.quantity,
        "price": item.price
    } for item in cart_items]

    return jsonify({"cart_id": cart.id, "cart_items": cart_list}), 200

@app.route('/cart/add', methods=["POST"])
@jwt_required()
def add_items():
    username = get_jwt_identity()
    cart = Cart.query.filter_by(username=username).first()

    if not cart:
        return jsonify({"message": "Cart not found for this user"}), 404

    data = request.get_json()
    product_name = data.get('name')
    
    # Fetch product details from the product catalog
    product_url = "http://127.0.0.1:5003/products"
    try:
        response = requests.get(product_url)
        response.raise_for_status()
        response_data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"message": f"Failed to fetch product details: {str(e)}"}), 500
    
    # Find product by name in the response data
    # for product in response_data:
    #     if product["name"] != product_name:
    #         return jsonify({"message": "Product not found"}), 404
            
    product = next((p for p in response_data if p["name"] == product_name), None)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    # Get price and quantity from the product API response
    price = product.get("price")
    quantity = product.get("quantity", 1)  # Default to 1 if quantity is not available

    # Check if the product is already in the cart
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_name=product_name).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(cart_id=cart.id, product_name=product_name, quantity=quantity, price=price)
        db.session.add(cart_item)

    db.session.commit()

    return jsonify({"message": "Item added successfully", "cart_item_id": cart_item.id}), 201


# @app.route('/cart/add', methods=["POST"])
# @jwt_required()
# def add_items():
#     username = get_jwt_identity()
#     cart = Cart.query.filter_by(username=username).first()
#     if not cart:
#         return jsonify({"message": "Cart not found for this user"}), 404
#     data = request.get_json()
#     product_name = data.get('name')
#     product_url = "http://127.0.0.1:5003/products"
#     response = requests.get(product_url)
#     response_data = response.json()
#     for product in response_data:
#         if product["name"] == product_name:
#             quantity = data.get('quantity', 1)
#             price = product["price"]
#             break
#     # if response.status_code == 200:
    #     product_data = response.json()
    #     price = product_data["price"]
    #     quantity = product_data["quauntity"]
    # else:
    #     return jsonify({"message": "Product not found"}), 404

    
    # cart_item = CartItem.query.filter_by(product_name=product_name).first()
    # cart_item = CartItem(cart_id=cart.id, product_name=product_name, quantity=quantity, price=price)
    # db.session.add(cart_item)
    # db.session.commit()

    # if cart_item:
    #     cart_item.quantity += quantity
    # else:
    #     cart_item = CartItem(cart_id=cart.id, product_name=product_name, quantity=quantity, price=price)
    #     db.session.add(cart_item)
    #     db.session.commit()

    # return jsonify({"message": "Item added successfully", "cart_item_id": cart_item.id}), 201

@app.route("/cart/remove", methods=["POST"])
@jwt_required()

def remove_from_cart():
    username = get_jwt_identity()
    data = request.get_json()

    product_id = data["product_id"]

    cart = Cart.query.filter_by(username=username).first()
    if not cart:
        return jsonify({"message": "Cart not found for this user"}), 404
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

    if not cart_item:
        return jsonify({"message": "item not found in cart"}), 404
    
    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({"message": "Item successfully removed"}), 200

@app.route("/cart/update_quantity")
@jwt_required()

def update_quantity():
    username = get_jwt_identity()
    data = request.get_json()

    product_id = data["product_id"]
    quantity = data["quantity"]

    cart = Cart.query.filter_by(username=username).first()
    if not cart:
        return jsonify({"message": "Cart not found for this user"}), 404
    
    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Item not found in cart"}), 404
    
    cart_item.quantity = quantity
    db.session.commit()

    return jsonify({"message": "Item quantity updated successfuly", "cart_item_id": cart_item.id}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)