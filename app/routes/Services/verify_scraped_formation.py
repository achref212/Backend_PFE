import json
import os
import subprocess

LINKS_FILE = "parcoursup_links.json"
SCRAPED_FILE = "formations_parcoursup.json"
UPDATED_FILE = "parcoursup_updated.json"
MISSING_FORMATIONS_FILE = "missing_formations_for_onisep.json"

def load_json_set(file, key=None):
    if not os.path.exists(file):
        return set()
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        if key:
            return set(d.get(key) for d in data if d.get(key))
        return set(data)

def load_json_list(file):
    if not os.path.exists(file):
        return []
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_missing_formations(formations):
    with open(MISSING_FORMATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(formations, f, indent=2, ensure_ascii=False)
    print(f"📁 {len(formations)} formation(s) manquante(s) pour enrichissement sauvegardée(s) dans : {MISSING_FORMATIONS_FILE}")

def launch_agent_onisep():
    print("🚀 Lancement de l'agent IA Onisep sur les formations manquantes...")
    try:
        subprocess.run(["python", "agent_onisep_ia.py"], check=True)
        print("✅ Agent IA Onisep terminé.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur durant l'exécution de l'agent Onisep : {e}")

def main():
    print("🔍 Vérification des formations enrichies...")

    scraped_data = load_json_list(SCRAPED_FILE)
    updated_urls = load_json_set(UPDATED_FILE, key="url")

    missing_formations = [f for f in scraped_data if f.get("url") not in updated_urls]

    if not missing_formations:
        print("✅ Toutes les formations ont déjà été enrichies.")
        return

    print(f"⚠️ {len(missing_formations)} formation(s) à enrichir détectée(s).")

    save_missing_formations(missing_formations)
    launch_agent_onisep()

if __name__ == "__main__":
    main()
