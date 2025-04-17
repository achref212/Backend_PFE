import json
import re
import unicodedata

def normalize(text):
    """Supprime les accents + minuscule pour comparaison robuste"""
    if not isinstance(text, str):
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def verify_apprentissage_etat(formation):
    titre = formation.get("titre", "").lower()
    apprentissage = formation.get("apprentissage", "").lower()
    badges = [normalize(b) for b in formation.get("badges", [])]
    controle_etat = formation.get("formation_controlee_par_etat", False)
    modified = False

    # ✅ Vérifier et corriger apprentissage
    if "apprentissage" in titre and apprentissage != "oui":
        formation["apprentissage"] = "Oui"
        print(f"[🛠️ Corrigé] Apprentissage mis à Oui → {formation.get('titre')}")
        modified = True
    elif "apprentissage" not in titre and apprentissage == "oui":
        formation["apprentissage"] = "Non"
        print(f"[🛠️ Corrigé] Apprentissage mis à Non → {formation.get('titre')}")
        modified = True

    # ✅ Vérifier et corriger formation contrôlée par l'État
    has_controle_badge = any(re.search(r"controle.*par.*l[’']?etat", badge) for badge in badges)

    if has_controle_badge and not controle_etat:
        formation["formation_controlee_par_etat"] = True
        print(f"[🛠️ Corrigé] Contrôle État mis à True → {formation.get('titre')}")
        modified = True
    elif not has_controle_badge and controle_etat:
        formation["formation_controlee_par_etat"] = False
        print(f"[🛠️ Corrigé] Contrôle État mis à False → {formation.get('titre')}")
        modified = True

    if not modified:
        print(f"[✅ OK] Aucun changement nécessaire → {formation.get('titre')}")

    return formation

# === Mise à jour directe du fichier formations_parcoursup.json ===
if __name__ == "__main__":
    path = "formations_parcoursup.json"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = [verify_apprentissage_etat(f) for f in data]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fichier mis à jour : {path}")
