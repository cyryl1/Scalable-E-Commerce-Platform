from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Product(db.model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    inventory_count = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.Foreign_key("category.id"), nullable=False)
    category = db.relationship('Category', backref=db.backref('products', lazy=True))