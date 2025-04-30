from flask import Flask
from app.service.database import db
from app.service.insert_data import insert_formations_from_json

app = Flask(__name__)

# Configuration PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://achref:mypasswordac@localhost:5432/pfe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():

    insert_formations_from_json(app)

if __name__ == "__main__":
    app.run(debug=True)