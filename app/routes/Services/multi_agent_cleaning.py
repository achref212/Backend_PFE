import os
import json
from dotenv import load_dotenv
from groq import Groq
from tqdm import tqdm

# Charger les variables d'environnement
load_dotenv()


# Initialiser le client Groq avec la clé API
client = Groq(api_key=os.getenv("GROQ_API_KEY=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"))

# Agent 1 : Nettoyeur (Cleaner)
def cleaner_agent(data, model="llama3-70b-8192"):
    original = data.copy()
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
- Reformate le champ "lieu" pour qu’il suive la structure : ville, région, département 
- Laisse les champs vides vides (ne les remplis pas).
- Format final = JSON valide.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            timeout=120
        )
        cleaned = json.loads(response.choices[0].message.content.strip())
        modified = [k for k in cleaned if cleaned.get(k) != original.get(k)]
        print(f"🧼 Champs nettoyés : {modified}")
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[❌ Cleaner Erreur] {e}")
        return data

# === DEBOUCHES AGENT ===
def debouches_agent(data, model="llama-3.1-8b-instant"):
    if "debouches" not in data or not isinstance(data["debouches"], dict):
        data["debouches"] = {"metiers": [], "secteurs": []}

    metiers = data["debouches"].get("metiers", [])
    secteurs = data["debouches"].get("secteurs", [])

    if metiers and secteurs:
        print("✅ Champs 'debouches' déjà remplis.")
        return data

    prompt = f"""
Tu es un assistant IA spécialisé dans les débouchés métiers/secteurs pour les formations. Complète uniquement les champs vides.

Voici la formation :
{json.dumps(data, indent=2, ensure_ascii=False)}

Complète :
- debouches.metiers : liste des métiers typiques pour cette formation.
- debouches.secteurs : secteurs d’activité liés à cette formation.

Format de sortie attendu :
"debouches": {{
    "metiers": [...],
    "secteurs": [...]
}}

Ne retourne que le champ "debouches" sous forme de JSON. Ne mets rien autour.
"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            timeout=90
        )
        content = response.choices[0].message.content.strip()

        try:
            return_data = json.loads(content)
        except json.JSONDecodeError:
            print("[⚠️] JSON brut invalide, tentative d'extraction entre accolades...")
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    return_data = json.loads(match.group(0))
                except Exception as err:
                    print(f"[❌ Parsing échoué] JSON extrait invalide : {err}")
                    print(f"Contenu brut renvoyé : {content[:200]}...")
                    return data
            else:
                print("[❌ Aucun bloc JSON détecté]")
                print(f"Contenu brut renvoyé : {content[:200]}...")
                return data

        data["debouches"] = return_data
        print("🛠️ Champs 'debouches' enrichis.")
        return data

    except Exception as e:
        print(f"[❌ DebouchesAgent Erreur] {e}")
        return data

# Agent 2 : Enricher Agent (LLaMA3)
import re

def enricher_agent(data, model="gemma2-9b-it"):
    original = data.copy()
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
            temperature=0.6,
            timeout=120
        )
        content = response.choices[0].message.content.strip()

        try:
            enriched = json.loads(content)
        except json.JSONDecodeError:
            print("[⚠️] JSON brut invalide, tentative d'extraction entre accolades...")
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    enriched = json.loads(match.group(0))
                except Exception as e:
                    print(f"[❌ Parsing échoué] JSON extrait non valide : {e}")
                    return data
            else:
                print(f"[❌ Enricher Erreur] JSON non détecté : {content[:250]}...")
                return data

        # 🧠 Afficher les champs enrichis
        changes = []
        for key, value in enriched.items():
            if key not in original or (not original.get(key) and value):
                changes.append(key)

        print(f"✨ Champs enrichis : {changes}" if changes else "✅ Aucun champ enrichi.")
        return enriched

    except Exception as e:
        print(f"[❌ Enricher Exception] {e}")
        return data
# === Vérifie si la formation a été traitée complètement

# Pipeline principal
if __name__ == "__main__":
    input_file = "parcoursup_updated.json"
    output_file = "parcoursup_final_data_cleaned.json"

    with open(input_file, "r", encoding="utf-8") as f:
        formations = json.load(f)

    results = []
    processed_urls = set()

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
            processed_urls = {x.get("url") for x in results if "url" in x}

    for i, formation in enumerate(tqdm(formations, desc="🔁 Traitement")):
        if formation.get("url") in processed_urls:
            print(f"✅ Formation déjà traitée : {formation.get('titre')}")
            continue
        print(f"\n🧼 [Cleaner] Formation {i+1}/{len(formations)}: {formation.get('titre', 'Sans titre')}")
        cleaned = cleaner_agent(formation)
        print("✨ [Enricher debouched] Complétion des champs vides...")
        debouched = debouches_agent(formation)
        print("✨ [Enricher] Complétion des champs vides...")
        enriched = enricher_agent(cleaned)

        results.append(enriched)

        if (i + 1) % 5 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Sauvegarde partielle après {i + 1} formations.")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Données nettoyées et complétées enregistrées dans {output_file}")
