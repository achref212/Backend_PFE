from app import create_app
from app.service.database import db
from sqlalchemy import text

app = create_app()  # charge le contexte Flask

def execute_sql(query: str):
    with app.app_context():  # ⬅️ Ajout fondamental ici
        try:
            result = db.session.execute(text(query)).fetchall()
            return [dict(row._mapping) for row in result]
        except Exception as e:
            return f"Erreur SQL : {str(e)}"