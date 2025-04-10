import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("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"))

def clean_with_llm(data, model="llama3-70b-8192"):
    prompt = f"""
Réponds UNIQUEMENT avec un JSON valide. Ne mets pas de ```json ni de texte autour. Ne commence jamais par 'Voici'.

Voici une formation extraite de Parcoursup au format JSON :
{json.dumps(data, indent=2, ensure_ascii=False)}

Nettoie et reformule et Complète les champs vides ce JSON en respectant les règles :
- Reformuler le champ "titre" pour qu’il soit clair et court.
- Reformuler "matieres_enseignees" sous forme de liste de matières simples.
- Réécrire le "resume_programme" de façon concise.
-**lieu** : Garde uniquement "ville, région, département" (extrait proprement ces infos du texte brut).
- Complète les champs vides forme de liste : `filieres_bac`, `specialites_favorisees` sous forme de liste
- Complète les champs vides si possible : `poursuite_etudes`, `taux_insertion`, etc.
- Nettoyer les "debouches" (secteurs et métiers) en style clair.
- Corriger les champs numériques comme prix_annuel, salaire_moyen.
- Extrais uniquement les données nettoyées, format JSON.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"[❌ Erreur IA] {e}")
        return data  # Retour brut en cas d'erreur

# === Exemple d’utilisation ===
if __name__ == "__main__":
    with open("parcoursup_updated.json", "r", encoding="utf-8") as f:
        formations = json.load(f)

    cleaned_formations = []
    for i, formation in enumerate(formations):
        print(f"\n🧠 Nettoyage IA de la formation {i+1}/{len(formations)}: {formation.get('titre', 'Sans titre')}")
        cleaned = clean_with_llm(formation)
        cleaned_formations.append(cleaned)

    with open("parcoursup_data_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_formations, f, indent=2, ensure_ascii=False)

    print("\n✅ Données nettoyées sauvegardées dans final_cleaned.json")
