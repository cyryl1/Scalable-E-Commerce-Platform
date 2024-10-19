from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from model import db, Payment

app = Flask(__name__)
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'Praise2020'

db.init_app(app)

@app.before_request
def initialize_tables():
    with app.app_context():
        db.create_all()


@app.route('/payments', methods=["POST"])
@jwt_required()
def create_payment():
    username = get_jwt_identity()

    data = request.get_json()
    order_id = data['order_id']
    amount = data['amount']
    currency = data['currency']
    payment_method = data['payment_method']
    payment_gateway = data['payment_gateway']

    new_payment = Payment(order_id=order_id, username = username, amount=amount, currency=currency, payment_method=payment_method, payment_gateway=payment_gateway)
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        'payment_id': new_payment.id,
        'status': new_payment.status,
        'created_at': new_payment.created_at
    }), 201

@app.route('/payments/<payment_id>', methods=["GET"])
def get_payment(payment_id):
    payment = Payment.query.filter_by(id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    
    return jsonify({
        'payment_id': payment.id,
        'order_id': payment.order_id,
        'username': payment.username,
        'amount': payment.amount,
        'currency': payment.currency,
        'payment_method': payment.payment_method,
        'payment_gateway': payment.payment_gateway,
        'transaction_id': payment.transaction_id,
        'created_at': payment.created_at,
        'updated_at': payment.updated_at
    }), 200

@app.route('/payments/<payment_id>', methods=["PUT"])
def update_payment_status(payment_id):
    payment = Payment.query.filter_by(id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    
    data = request.get_json()
    if 'status' in data:
        payment.status = data['status']
    if 'transaction_id' in data:
        payment.transaction_id = data['transaction_id']

    db.session.commit()
    return jsonify({
        'payment_id': payment.id,
        'status': payment.status,
        'transaction_id': payment.transaction_id,
        'updated_at': payment.updated_at
    }), 200


@app.route('/payments/<payment_id>/refund', methods=['POST'])

def refund_payment(payment_id):
    payment = Payment.query.filter_by(id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    if payment.status != 'completed':
        return jsonify({"message": "Payment must becompleted to refund"}), 400
    refund_amount = request.json.get('amount', payment.amount)
    payment.status = 'refunded'
    db.session.commit()

    return jsonify({
        'payment_id': payment.id,
        'status': 'refunded',
        'refund_amount': refund_amount,
        'updated_at': payment.updated_at
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)