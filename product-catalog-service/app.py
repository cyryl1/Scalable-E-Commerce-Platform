from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Category, Product

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Praise2020'

db.init_app(app)

@app.before_request
def initialize_tables():
    with app.app_context():
        db.create_all()

# create categories
@app.route("/category", methods=["POST"])
def create_category():
    data = request.get_json()
    name = data['name']

    if Category.query.filter_by(name=name).first():
        return jsonify({"message": "Category already exists"}), 400
    
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()

    return jsonify({"message": "Category successfully added"}), 201

# get all categories
@app.route("/category", methods=["GET"])
def get_categories():
    categories = Category.query.all()
    response = [{"id": category.id, "name": category.name} for category in categories]
    return jsonify(response), 200

@app.route("/category/delete", methods=["DELETE"])
def delete_category():
    data = request.json
    category_name = data.get("name")

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"message": "category not found"}), 404
    
    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category successfully deleted"}), 200

# @app.route("/category/delete", methods=["DELETE"])
# def delete_category():
#     data = request.json
#     category_name = data.get("name")  # Get the category name from the request

#     # Find the category by its name
#     category = Category.query.filter_by(name=category_name).first()
    
#     if not category:
#         return jsonify({"message": "Category not found"}), 404
    
#     # Delete the category
#     db.session.delete(category)
#     db.session.commit()

#     return jsonify({"message": "Category deleted successfully"}), 200

# add a product
@app.route("/products", methods=["POST"])
def create_product():
    data = request.json
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    inventory_count = data.get("inventory_count", 0)
    category_name = data.get('category_name')

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    new_product = Product(name=name, description=description, price=price, inventory_count=inventory_count, category_name=category_name)
    db.session.add(new_product)
    db.session.commit()

    return jsonify ({"message": "Product created"}), 201
# get all product
@app.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    response = [{
        "id": product.id, 
        "name": product.name, 
        "description": product.description, 
        "price": product.price, 
        "inventory_count": product.inventory_count, 
        "category": product.category.name
    } for product in products]

    return jsonify(response), 200

@app.route("/products/<product_name>", methods=["GET"])
def get_product_by_name(product_name):
    product = Product.query.filter_by(name=product_name).first()
    if not product:
        return jsonify({"message": "Product not found"}), 404
    
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "inventory_count": product.inventory_count,
        "category": product.category.name
    }), 201
# update inventory
@app.route('/products/inventory', methods=["PUT"])
def update_inventory():
    data = request.json
    product_name = data.get('product_name')
    category_name = data.get('category_name')
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    product = Product.query.filter_by(name=product_name).first()
    if not product:
        return jsonify({"message": "Product not found"}), 404
    
    
    product.inventory_count = data.get('inventory_count', product.inventory_count)
    db.session.commit()

    return jsonify({"message": "Inventory updated successfully"}), 200


@app.route("/products/delete", methods=["DELETE"])
def delete_product():
    data = request.json
    product_name = data.get('product_name')
    category_name = data.get('category_name')

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    product = Product.query.filter_by(name=product_name).first()
    if not product:
        return jsonify({"message": "Product not found"})
    
    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)