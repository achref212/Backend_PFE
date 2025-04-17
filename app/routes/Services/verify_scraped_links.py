import json
import os
import subprocess

LINKS_FILE = "parcoursup_links.json"
SCRAPED_FILE = "formations_parcoursup.json"
MISSING_FILE = "missing_links.json"

def load_json_set(file, key=None):
    if not os.path.exists(file):
        return set()
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        if key:
            return set(d.get(key) for d in data if d.get(key))
        return set(data)

def save_missing_links(missing_links):
    with open(MISSING_FILE, "w", encoding="utf-8") as f:
        json.dump(list(missing_links), f, indent=2, ensure_ascii=False)
    print(f"📁 {len(missing_links)} lien(s) manquant(s) sauvegardé(s) dans : {MISSING_FILE}")

def launch_agent_parcoursup_ia():
    print("🚀 Lancement de l'agent IA Parcoursup sur les liens manquants...")
    try:
        subprocess.run(["python", "agent_parcoursup_ia.py"], check=True)
        print("✅ Agent IA terminé.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur durant l'exécution de l'agent : {e}")

def main():
    print("🔍 Vérification des liens scrapés...")

    all_links = load_json_set(LINKS_FILE)
    scraped_links = load_json_set(SCRAPED_FILE, key="url")

    missing_links = all_links - scraped_links
    if not missing_links:
        print("✅ Tous les liens ont déjà été scrapés.")
        return

    print(f"⚠️ {len(missing_links)} lien(s) manquant(s) détecté(s).")

    save_missing_links(missing_links)
    launch_agent_parcoursup_ia()

if __name__ == "__main__":
    main()
