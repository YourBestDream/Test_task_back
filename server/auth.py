from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, create_refresh_token
from .models import User, TokenBlacklist
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    name = request.json.get('firstName')
    surname = request.json.get('lastName')
    email = request.json.get('email')
    password = request.json.get('password')
    
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"message": "User already exists"}), 409
    
    user = User(name=name, surname=surname ,email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

@auth.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400
    
    user = User.query.filter_by(email=email).first()
    if user is not None and user.check_password(password):
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

@auth.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token), 200

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the unique identifier for the JWT
    blacklisted_token = TokenBlacklist(jti=jti)
    db.session.add(blacklisted_token)
    db.session.commit()
    return jsonify({"msg": "Successfully logged out"}), 200
