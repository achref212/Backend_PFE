import os
import json
from dotenv import load_dotenv
from groq import Groq

# Charger les variables d'environnement
load_dotenv()

# Initialiser le client Groq avec la clé API
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Agent 1 : Nettoyeur (Cleaner)
def cleaner_agent(data, model="llama3-70b-8192"):
    prompt = f"""
Réponds UNIQUEMENT avec un JSON valide. Ne mets pas de ```json ni de texte autour. Ne commence jamais par 'Voici'.

Voici une formation brute :
{json.dumps(data, indent=2, ensure_ascii=False)}

Nettoie et reformule les données comme suit :
- Reformule le champ "titre" pour qu’il soit clair et court.
- Transforme "matieres_enseignees" en liste simple.
- Résume "resume_programme" de façon concise.
- Nettoie les champs "debouches" (métiers + secteurs) en style clair.
- Corrige les formats numériques : prix_annuel, salaire_moyen, etc.
- Laisse les champs vides vides (ne les remplis pas).
- Format final = JSON valide.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[❌ Cleaner Erreur] {e}")
        return data


# Agent 2 : Enricher Agent (LLaMA3)
import re

def enricher_agent(data, model="gemma2-9b-it"):
    prompt = f"""
Réponds uniquement avec un JSON. Ne mets jamais de texte autour, pas d'explication.

Voici une formation avec des champs possiblement vides :
{json.dumps(data, indent=2, ensure_ascii=False)}

Complète les champs vides en te basant sur les autres champs, ton savoir ou tes déductions logiques. Exemple :
- `filieres_bac` : Si vide, propose les types de baccalauréats pertinents comme ["bac général", "bac technologique", "bac professionnel", "bac informatique",...] selon le domaine de la formation.
- `specialites_favorisees` : Si vide, déduis les spécialités de bac qui correspondent le mieux à cette formation (ex : Bac général, Bac technologique, Bac professionnel,...).
- `debouches.metiers` et `debouches.secteurs` : Complète si vide, en restant cohérent avec le type de formation.
- `matieres_enseignees` : Complète si vide, en restant cohérent avec le type de formation.
- `poursuite_etudes`, `taux_insertion`, `resume_programme`, etc. doivent être renseignés si faisable.
- Ne change pas les champs déjà remplis.
- Retourne un JSON VALIDE, uniquement le JSON.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        content = response.choices[0].message.content.strip()

        # 🧠 Tentative directe
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 🔍 Tentative via extraction brute entre accolades
            print("[⚠️] JSON brut invalide, tentative d'extraction entre accolades...")
            match = re.search(r"{.*}", content, re.DOTALL)
            if match:
                cleaned = match.group(0)
                return json.loads(cleaned)
            else:
                print(f"[❌ Enricher Erreur] JSON non détecté : {content[:250]}...")
                return data

    except Exception as e:
        print(f"[❌ Enricher Exception] {e}")
        return data

# Pipeline principal
if __name__ == "__main__":
    input_file = "parcoursup_updated.json"
    output_file = "parcoursup_final_data_cleaned.json"

    with open(input_file, "r", encoding="utf-8") as f:
        formations = json.load(f)

    results = []
    for i, formation in enumerate(formations):
        print(f"\n🧼 [Cleaner] Formation {i+1}/{len(formations)}: {formation.get('titre', 'Sans titre')}")
        cleaned = cleaner_agent(formation)

        print("✨ [Enricher] Complétion des champs vides...")
        enriched = enricher_agent(cleaned)

        results.append(enriched)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Données nettoyées et complétées enregistrées dans {output_file}")
