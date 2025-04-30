import re

from app.routes.Services.multi_agent_cleaning_tg import client


def extract_sql_from_response(response: str) -> str:
    # Cherche le bloc ```sql ... ```
    match = re.search(r"```sql\s+(.*?)```", response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # fallback : tout nettoyer s'il n'y a pas de bloc clair
        return response.strip().split("\n")[-1]

def generate_sql_query(prompt: str, schema: dict, tables: list):
    system_prompt = (
        "Tu es un générateur de requêtes SQL PostgreSQL avancé, connecté à une base de données d'orientation post-bac. "
        "Ton objectif est de produire une requête SQL valide, pertinente et optimisée en réponse à la question de l'utilisateur, "
        "en exploitant l'intégralité des tables et colonnes disponibles, et en adaptant la jointure et les filtres selon le besoin."

        "\n\n📚 Schéma relationnel :\n"
        "- `formations` (id, titre, etablissement, type_formation, type_etablissement, apprentissage, prix_annuel, salaire_moyen, salaire_min, salaire_max, poursuite_etudes, taux_insertion, resume_programme, duree, lien_onisep)\n"
        "- `lieux` (ville, region, departement) ← lié à formations via formation_id\n"
        "- `badges` (badge) ← lié à formations\n"
        "- `filieres_bac` (filiere) ← lié à formations\n"
        "- `specialites_favorisees` (specialite) ← lié à formations\n"
        "- `matieres_enseignees` (matiere) ← lié à formations\n"
        "- `debouches_metiers` (metier) ← lié à formations\n"
        "- `debouches_secteurs` (secteur) ← lié à formations"

        "\n\n🧠 Règles strictes :\n"
        "- Réponds exclusivement avec une requête SQL entre balises ```sql ... ```.\n"
        "- N’ajoute jamais de texte, commentaire, explication, ou balise `<think>`.\n"
        "- Utilise toujours les bonnes jointures si la donnée provient d'une table liée.\n"
        "- Utilise ILIKE avec `%...%` pour tous les filtres textuels si la recherche est floue.\n"
        "- Utilise DISTINCT si la question implique une liste unique (ex. métiers, villes).\n"
        "- Si la question contient des mots comme \"ville\", \"région\", \"à\", alors joint `lieux`.\n"
        "- Si la question parle de \"prix\", utilise `prix_annuel`. Si \"salaire\" → `salaire_moyen`.\n"
        "- Si la question demande des matières → joint `matieres_enseignees`.\n"
        "- Si la question concerne les métiers → joint `debouches_metiers`.\n"
        "- Si elle concerne les secteurs → joint `debouches_secteurs`.\n"
        "- Ne génère jamais de champ qui n'existe pas. N’invente pas.\n"
        "- Respecte le lien entre les tables via `formation_id`."

        "\n\n🔁 Objectif : construire une requête la plus précise, propre et fiable possible, sans texte autour."
    )
    full_prompt = f"""
Schéma :
{schema}

Tables utiles : {tables}

Question : {prompt}

Génère uniquement la requête SQL entre balises ```sql ... ```
"""
    res = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.2
    )
    response = res.choices[0].message.content.strip()
    return extract_sql_from_response(response)