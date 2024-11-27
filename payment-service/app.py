from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from model import db, Payment
from dotenv import load_dotenv
# from paystack import Paystack
import requests
import os

load_dotenv()

app = Flask(__name__)
jwt = JWTManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///payment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['PAYSTACK_SECRET_KEY'] = os.getenv('PAYSTACK_SECRET_KEY')
app.config['PAYSTACK_PUBLIC_KEY'] = os.getenv('PAYSTACK_PUBLIC_KEY')

db.init_app(app)

# paystack_client = Paystack(secret_key=app.config['PAYSTACK_SECRET_KEY'])


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
    

    # try:
    user = requests.get("http://127.0.0.1:5001")
    user_data = user.json()
    if user.username == username:
        email = user_data["email"]
    else:
        return jsonify({"User not found"}), 404
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount
    }
    transaction = requests.post(url=url, headers=headers, data=data)
    print(transaction)
    if transaction.status_code == 200:
        response_data = transaction.json()
            # transaction_uri = response_data["data"]["authorization_url"]
    # except Exception as e:
        # return jsonify({"message": f"Failed to initialize transaction: {str(e)}"}), 500
            

    new_payment = Payment(
        order_id=order_id,
        username = username,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        payment_gateway=payment_gateway,
        transaction_id=response_data["data"]['reference']
    )
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        'payment_id': new_payment.payment_id,
        'status': new_payment.status,
        'created_at': new_payment.created_at
    }), 201

@app.route('/payments/<payment_id>/callback', methods=["GET"])
def get_payment(payment_id):
    payment = Payment.query.filter_by(payment_id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    
    ref = payment.transasction_id
    # ref = request.get_json()['reference']
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }
    response = requests.get(url=url, headers=headers)
    data = response.json
    
    return jsonify({
        'payment_id': payment.payment_id,
        'order_id': payment.order_id,
        'username': payment.username,
        'amount': payment.amount,
        'currency': payment.currency,
        'payment_method': payment.payment_method,
        'payment_gateway': payment.payment_gateway,
        'transaction_id': payment.transaction_id,
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
        'status': data['data']['status'],
        'message': data['data']['message'],
        'transaction_id': data['data']['id'],
        'channel': data['data']['channel']
    }), 200

@app.route('/payments/<payment_id>', methods=["PUT"])
def update_status(payment_id):
    payment = Payment.query.filter_by(payment_id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404

    verify_payment = get_payment()
    if verify_payment['status']!= 'success':
        return jsonify({"message": "Payment must be successful to update status"}), 400
    
    payment.status = verify_payment['status']

    db.session.commit()
    return jsonify({
        'payment_id': payment.payment_id,
        'status': payment.status,
        'transaction_id': payment.transaction_id,
        'updated_at': payment.updated_at
    }), 200


@app.route('/payments/<payment_id>/refund', methods=['POST'])

def refund_payment(payment_id):
    payment = Payment.query.filter_by(payment_id=payment_id).first()
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    
    verify_payment = get_payment()
    if verify_payment['status']!= 'success':
        return jsonify({"message": "Payment must be completed to refund"}), 400
    refund_amount = request.json.get('amount', payment.amount)
    
    url = f"https://api.paystack.co/transaction/refund"
    headers = {
        "Authorization": f"Bearer {app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "transaction_id": verify_payment.transaction_id,
        "amount": refund_amount
    }
    response = requests.post(url=url, headers=headers, data=data)
    if response.status_code == 200:
        res = response.json,
        id = res['data']['id']
        payment.status = 'refunded'
    db.session.commit()

    return jsonify({
        'payment_id': payment.payment_id,
        'trx_id': id,
        'status': payment.status,
        'refund_amount': refund_amount,
        'updated_at': payment.updated_at
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)