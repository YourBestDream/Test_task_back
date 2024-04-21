import os
from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_cors import CORS
from flask_jwt_extended import JWTManager

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = f'{os.environ.get("SECRET_KEY")}'
    app.config['JWT_SECRET_KEY'] = f'{os.environ.get("JWT_SECRET_KEY")}'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{os.environ.get("POSTGRES_USERNAME")}:{os.environ.get("POSTGRES_PASSWORD")}@{os.environ.get("POSTGRES_URL")}/{os.environ.get("POSTGRES_DATABASE")}'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(hours=2)

    db.init_app(app)
    jwt = JWTManager(app)

    from .models import TokenBlacklist

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = db.session.query(TokenBlacklist).filter_by(jti=jti).scalar()
        return token is not None

    CORS(app, supports_credentials=True)

    from .auth import auth
    from .queries import queries

    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(queries, url_prefix='/')

    return app