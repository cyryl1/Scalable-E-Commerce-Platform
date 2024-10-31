from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
import os
from models import db, Notification
from dotenv import load_dotenv
import requests
import smtplib


load_dotenv()

Email="aribisalapraise12@gmail.com"
Password=os.getenv("APP_PASSWORD")

app = Flask(__name__)
jwt = JWTManager()

app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///notification.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

db.init_app(app)


@app.before_request
def initialize_tables():
    with app.app_context():
        db.create_all()

@app.route('/notification', methods=["POST"])
@jwt_required
def send_notification():
    username = get_jwt_identity()
    data = request.get_json()
    payment_id = data.get("payment_id")
    # title = data.get("title")
    user = requests.get("http://127.0.0.1:5003")
    user_data = user.json()
    if user.username == username:
        email = user_data["email"]

    #Verifies for payment success first
    try:
        verify_payment =  requests.get(f"http://127.0.0.1:5002/payments/{payment_id}/callback")
        response = verify_payment.json()
    except Exception as e:
        return jsonify({"message": "Failed to verify payment"})
    
    if response.status == "success":
        title = f"Payment Successful - {response.amount}"
        message = f"""Dear {email},\n
        Your payment has been processed successfully.\n
        Payment Details:
        Amount: {response.amount}
        Order ID: {response.order_id}
        Payment Method: {response.channel}
        Transaction ID: {response.transaction_id}
        Date: {datetime.now}\n
        If you have any questions, please contact our support team.\n
        Best regards,
        Your E-commerce Team"""
    else:
        return jsonify({"message": "Payment not successful"}), 401
    
    notification = Notification(username=username, title=title, message=message)
    db.session.add(notification)
    db.session.commit()

    with smtplib.SMTP("smtp.gmail.com, 587") as server:
        server.starttls()
        server.login(Email, Password)
        server.sendmail(
            from_addr=Email,
            to_addrs=email,
            msg=f"Subject: {title}\n\n{message}"
        )
    

    


@app.route('/about')
def about():
    return 'This is the About Page!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)