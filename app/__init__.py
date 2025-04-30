from flask import Flask
from app.service.database import db
from app.model.models import *


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://achref:mypasswordac@localhost:5432/pfe_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    return app


def app_context():
    return None