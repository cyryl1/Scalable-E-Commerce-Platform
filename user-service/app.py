from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, User, TokenBlacklist
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

db.init_app(app)
jwt = JWTManager(app)



# create database table
@app.before_request
def initialize_tables():
    with app.app_context():
        db.create_all()

# user profile
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data['username']
    password = data['password']
    email = data['email']
    full_name = data.get('full_name')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "User already exists"}), 400
    
    new_user = User(username=username, email=email, full_name=full_name)
    new_user.hash_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# user login
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials, check username or pasword"}), 401
    
    access_token = create_access_token(identity=username, expires_delta=timedelta(hours=1))
    refresh_token = create_refresh_token(identity=username, expires_delta=timedelta(days=7))
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

# refresh token

@app.route('/refresh', methods=["POST"])
def refresh_tokens(refresh=True):
    user = get_jwt_identity()
    access_token = create_access_token(identity=user)
    return jsonify(access_token=access_token), 200

# Get user profile

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_username = get_jwt_identity()
    user = User.query.filter_by(username=current_username).first()

    if not user:
        return jsonify({"message": "User not found"}), 404
    
    return jsonify({
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
    }), 200

# update user profile

@app.route('/profile', methods=["PUT"])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    data = request.json
    user.email = data.get('email', user.email)
    user.full_name = data.get('full_name', user.full_name)

    db.session.commit()
    return jsonify({
        "message": "Profile updated successfully"
    }), 200

@app.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    token_type = get_jwt()["type"]
    blacklisted_token = TokenBlacklist(jti=jti, token_type=token_type)
    db.session.add(blacklisted_token)
    db.session.commit()
    return jsonify({"message": "Logged out"}), 200

# TODO- Add logout and delete user.


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)