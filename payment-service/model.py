from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.String(36), primary_key=True, default=lambda:str(uuid.uuid4), nullable=False)
    order_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    payment_method = db.Column(db.String(50), nullable=False)
    payment_gateway = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False) #External transaction ID from gateway
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

