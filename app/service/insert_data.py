import json
import re
from app.service.database import db
from app.model.models import (
    Formation, Lieu, Badge, FiliereBac,
    SpecialiteFavorisee, MatiereEnseignee,
    DeboucheMetier, DeboucheSecteur
)
from sqlalchemy import text

# 📦 Nettoyer les champs numériques
def clean_numeric(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip().lower()
        if "gratuit" in value:
            return 0.0
        value = re.sub(r"[^\d.]", "", value.replace(",", "."))  # supprime € / espaces
        try:
            return float(value)
        except ValueError:
            return None
    return None

# 📦 Fonction pour récupérer une clé même si elle a une faute (accent...)
def get_value_smart(d, keys):
    """
    Cherche dans le dict `d` une des clés dans la liste `keys`.
    """
    for key in keys:
        if key in d:
            return d[key]
    return None

# 🧹 Fonction pour tout vider avant de réinsérer
def clean_all_tables():
    db.session.execute(text('TRUNCATE lieux CASCADE'))
    db.session.execute(text('TRUNCATE badges CASCADE'))
    db.session.execute(text('TRUNCATE filieres_bac CASCADE'))
    db.session.execute(text('TRUNCATE specialites_favorisees CASCADE'))
    db.session.execute(text('TRUNCATE matieres_enseignees CASCADE'))
    db.session.execute(text('TRUNCATE debouches_metiers CASCADE'))
    db.session.execute(text('TRUNCATE debouches_secteurs CASCADE'))
    db.session.execute(text('TRUNCATE formations CASCADE'))
    db.session.commit()
    print("🧹 Base nettoyée : toutes les tables vidées.")

def insert_formations_from_json(app, filepath='data/Final Data.json'):
    with app.app_context():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                formations_data = json.load(f)
            print(f"📄 JSON chargé : {len(formations_data)} formations.")
        except Exception as e:
            print(f"❌ Erreur de chargement : {e}")
            return

        db.create_all()
        print("🛠️ Tables vérifiées/créées.")

        # 1️⃣ Nettoyer toutes les tables avant
        clean_all_tables()

        for f in formations_data:
            try:
                formation = Formation(
                    timestamp=f.get('timestamp'),
                    url=f.get('url'),
                    titre=f.get('titre'),
                    etablissement=f.get('etablissement'),
                    type_formation=f.get('type_formation'),
                    type_etablissement=f.get('type_etablissement'),
                    formation_controlee_par_etat=f.get('formation_controlee_par_etat'),
                    apprentissage=f.get('apprentissage'),
                    prix_annuel=clean_numeric(f.get('prix_annuel')),
                    salaire_moyen=clean_numeric(f.get('salaire_moyen')),
                    salaire_min=clean_numeric(f.get('salaire_bornes', {}).get('min')),
                    salaire_max=clean_numeric(f.get('salaire_bornes', {}).get('max')),
                    poursuite_etudes=f.get('poursuite_etudes'),
                    taux_insertion=f.get('taux_insertion'),
                    lien_onisep=f.get('lien_onisep'),
                    duree=f.get('duree'),
                    resume_programme=f.get('resume_programme')
                )
                db.session.add(formation)
                db.session.flush()
                print(f"✅ Formation insérée : {formation.titre}")

                # ➡️ Ajouter les relations
                lieu_data = f.get('lieu')
                if isinstance(lieu_data, dict):
                    db.session.add(Lieu(
                        formation_id=formation.id,
                        ville=get_value_smart(lieu_data, ['ville']),
                        region=get_value_smart(lieu_data, ['région', 'region']),
                        departement=get_value_smart(lieu_data, ['département', 'departement'])
                    ))

                for badge in f.get('badges', []):
                    db.session.add(Badge(formation_id=formation.id, badge=badge))

                for filiere in f.get('filieres_bac', []):
                    db.session.add(FiliereBac(formation_id=formation.id, filiere=filiere))

                for specialite in f.get('specialites_favorisees', []):
                    db.session.add(SpecialiteFavorisee(formation_id=formation.id, specialite=specialite))

                for matiere in f.get('matieres_enseignees', []):
                    if isinstance(matiere, dict):
                        matiere = json.dumps(matiere, ensure_ascii=False)
                    db.session.add(MatiereEnseignee(
                        formation_id=formation.id,
                        matiere=matiere
                    ))

                for metier in f.get('debouches', {}).get('metiers', []):
                    db.session.add(DeboucheMetier(formation_id=formation.id, metier=metier))

                for secteur in f.get('debouches', {}).get('secteurs', []):
                    db.session.add(DeboucheSecteur(formation_id=formation.id, secteur=secteur))

                # ✅ Commit formation par formation
                db.session.commit()
                print(f"🎯 Formation '{formation.titre}' COMMITÉE avec succès.")

            except Exception as e:
                db.session.rollback()
                print(f"❗ Erreur d'insertion/commit d'une formation : {e}")

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    insert_formations_from_json(app)