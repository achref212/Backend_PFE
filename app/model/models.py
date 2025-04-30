from app.service.database import db

class Formation(db.Model):
    __tablename__ = 'formations'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    url = db.Column(db.Text)
    titre = db.Column(db.Text)
    etablissement = db.Column(db.Text)
    type_formation = db.Column(db.Text)
    type_etablissement = db.Column(db.Text)
    formation_controlee_par_etat = db.Column(db.Boolean)
    apprentissage = db.Column(db.Text)
    prix_annuel = db.Column(db.Numeric)
    salaire_moyen = db.Column(db.Numeric)
    salaire_min = db.Column(db.Numeric)
    salaire_max = db.Column(db.Numeric)
    poursuite_etudes = db.Column(db.Text)
    taux_insertion = db.Column(db.Text)
    lien_onisep = db.Column(db.Text)
    duree = db.Column(db.Text)
    resume_programme = db.Column(db.Text)

class Lieu(db.Model):
    __tablename__ = 'lieux'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    ville = db.Column(db.Text)
    region = db.Column(db.Text)
    departement = db.Column(db.Text)

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    badge = db.Column(db.Text)

class FiliereBac(db.Model):
    __tablename__ = 'filieres_bac'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    filiere = db.Column(db.Text)

class SpecialiteFavorisee(db.Model):
    __tablename__ = 'specialites_favorisees'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    specialite = db.Column(db.Text)

class MatiereEnseignee(db.Model):
    __tablename__ = 'matieres_enseignees'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    matiere = db.Column(db.Text)

class DeboucheMetier(db.Model):
    __tablename__ = 'debouches_metiers'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    metier = db.Column(db.Text)

class DeboucheSecteur(db.Model):
    __tablename__ = 'debouches_secteurs'
    id = db.Column(db.Integer, primary_key=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id', ondelete="CASCADE"))
    secteur = db.Column(db.Text)