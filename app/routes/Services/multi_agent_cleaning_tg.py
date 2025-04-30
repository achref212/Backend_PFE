import os
import json
import re
from tqdm import tqdm
from dotenv import load_dotenv
from together import Together

# === Init
load_dotenv()
client = Together(api_key=os.getenv("tgp_v1_jPoZ7Q5VDYvGMCNpZeSMNN3crX1pLz-um1AgPlgSCMw"))

def save_failed(formation, path="failed_cleaning.json"):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(formation)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Formation sauvegardée dans {path}")
    except Exception as e:
        print(f"[❌ Échec de la sauvegarde dans {path}] : {e}")

# === CLEANER AGENT ===

def cleaner_agent(data, model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free", backup_model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"):
    original = data.copy()
    prompt = f"""
Réponds UNIQUEMENT avec un JSON valide. Ne mets pas de ```json ni de texte autour. Ne commence jamais par 'Voici'.
Évite les erreurs de format comme "Expecting ',' delimiter" ou guillemets non fermés. Assure-toi que :
- Toutes les chaînes sont entre guillemets doubles `"`, bien échappées.
- Chaque paire clé/valeur est bien séparée par `,`.
- Le JSON commence par {{ et se termine par }}.
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

    models = [model, backup_model]
    for attempt, current_model in enumerate(models, start=1):
        try:
            print(f"🔁 Tentative {attempt} (modèle: {current_model}) pour nettoyer : {data.get('titre', 'Sans titre')}")
            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=200
            )
            output = response.choices[0].message.content.strip()

            try:
                result = json.loads(output)
            except json.JSONDecodeError:
                print("[⚠️ Cleaner] JSON invalide, tentative d'extraction brute…")
                match = re.search(r"\{.*\}", output, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("Aucun bloc JSON détecté")

            modified = [k for k in result if result.get(k) != original.get(k)]
            print(f"🧼 Champs nettoyés : {modified}")
            return result

        except Exception as e:
            print(f"[❌ Cleaner Erreur] {e}")
            if model != backup_model:
                print("🔁 Passage au modèle de secours CLEANER.")
                return cleaner_agent(data, model=backup_model, backup_model=backup_model)
            else:
                save_failed(data)
                return data

# === DEBOUCHES AGENT ===
def debouches_agent(data, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", backup_model="meta-llama/Llama-Vision-Free " ,max_retries=3):
    if "debouches" not in data or not isinstance(data["debouches"], dict):
        data["debouches"] = {"metiers": [], "secteurs": []}

    metiers = data["debouches"].get("metiers", [])
    secteurs = data["debouches"].get("secteurs", [])

    if metiers and secteurs:
        print("✅ Champs 'debouches' déjà remplis.")
        return data

    prompt = f"""
Tu es un assistant IA spécialisé dans les débouchés métiers/secteurs pour les formations. Complète uniquement les champs vides.
Évite les erreurs de format comme "Expecting ',' delimiter" ou guillemets non fermés. Assure-toi que :
- Toutes les chaînes sont entre guillemets doubles `"`, bien échappées.
- Chaque paire clé/valeur est bien séparée par `,`.
- Le JSON commence par {{ et se termine par }}.
Voici la formation :
{json.dumps(data, indent=2, ensure_ascii=False)}

Complète :
- debouches.metiers : liste des métiers typiques et liés pour cette formation.
- debouches.secteurs : secteurs d’activité typiques et liés à cette formation.

Format de sortie attendu :
"debouches": {{
    "metiers": [...],
    "secteurs": [...]
}}

Ne retourne que le champ "debouches" sous forme de JSON. Ne mets rien autour.
"""

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔁 Tentative {attempt} enrichissement débouchés : {data.get('titre', 'Sans titre')} (model={model})")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                timeout=200
            )
            content = response.choices[0].message.content.strip()

            try:
                extracted = json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    extracted = json.loads(match.group(0))
                else:
                    raise ValueError("Aucun bloc JSON valide détecté")

            data["debouches"] = extracted
            print("🛠️ Champs 'debouches' enrichis.")
            return data

        except Exception as e:
            print(f"[❌ DebouchesAgent Erreur] Tentative {attempt} échouée : {e}")
            if attempt == max_retries:
                if model != backup_model:
                    print("🔁 Passage au modèle de secours pour débouchés.")
                    return debouches_agent(data, model=backup_model, max_retries=max_retries)
                else:
                    print("⛔️ Échec final enrichissement débouchés. On garde l’original.")
                    save_failed(data)
                    return data

# === ENRICHER AGENT ===
def enricher_agent(data, model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",backup_model="meta-llama/Llama-Vision-Free" ,max_retries=3):
    original = data.copy()
    prompt = f"""
Réponds uniquement avec un JSON. Ne mets jamais de texte autour, pas d'explication.
Évite les erreurs de format comme "Expecting ',' delimiter" ou guillemets non fermés. Assure-toi que :
- Toutes les chaînes sont entre guillemets doubles `"`, bien échappées.
- Chaque paire clé/valeur est bien séparée par `,`.
- Le JSON commence par {{ et se termine par }}.
Voici une formation avec des champs possiblement vides :
{json.dumps(data, indent=2, ensure_ascii=False)}

Complète les champs vides :
- `filieres_bac`, `specialites_favorisees` : listes.
- `debouches.metiers`, `debouches.secteurs` : si vide, compléter.
- `matieres_enseignees`, `poursuite_etudes`, `resume_programme`, `taux_insertion`...
- Pour tout autre champ vide → déduire si faisable.
- Ne change pas les champs déjà remplis.
- Retourne un JSON VALIDE, uniquement le JSON.
"""

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔁 Tentative {attempt} enrichissement général : {data.get('titre', 'Sans titre')}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                timeout=200
            )

            content = response.choices[0].message.content.strip()

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                print("[⚠️ Enricher] JSON invalide, tentative d'extraction brute...")
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    result = json.loads(match.group(0))
                else:
                    raise ValueError("Aucun JSON détecté dans la réponse.")

            modified = [k for k in result if not original.get(k) and result.get(k)]
            print(f"✨ Champs enrichis : {modified}" if modified else "✅ Aucun champ enrichi.")
            return result

        except Exception as e:
            print(f"[❌ Enricher Erreur] Tentative {attempt} échouée : {e}")
            if attempt == max_retries:
                if model != backup_model:
                    print("🔁 Passage au modèle de secours pour enrichissement.")
                    return enricher_agent(data, model=backup_model, backup_model=backup_model)
                else:
                    save_failed(data)
                    return data

# === MAIN EXECUTION ===
if __name__ == "__main__":
    #input_file = "parcoursup_updated.json"
    input_file = "parcoursup_sanitized.json"
    output_file = "parcoursup_final_data_cleaned.json"

    # Charger les données
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
            print(f"✅ Déjà traité : {formation.get('titre')}")
            continue

        print(f"\n🧼 [Cleaner] Formation {i+1}/{len(formations)} : {formation.get('titre', 'Sans titre')}")
        cleaned = cleaner_agent(formation)

        print("🧠 [Débouchés] Complétion debouches...")
        debouched = debouches_agent(cleaned)

        print("✨ [Enricher] Final enrichissement...")
        enriched = enricher_agent(debouched)

        results.append(enriched)

        # 🔁 Sauvegarde partielle toutes les 5 formations
        if (len(results) % 5) == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Sauvegarde partielle après {len(results)} formations.")

    # 💾 Sauvegarde finale
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Toutes les données enrichies et nettoyées ont été enregistrées dans : {output_file}")
