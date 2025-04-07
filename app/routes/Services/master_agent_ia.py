import subprocess
import time

def run_script(name, script):
    print(f"\n🚀 Lancement de : {name}")
    try:
        subprocess.run(["python", script], check=True)
        print(f"✅ Terminé : {name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur dans {name} : {e}")

def main():
    start = time.time()

    # Étape 1 : Collecte des liens depuis la carte Parcoursup
    run_script("Agent Collecteur de liens (Parcoursup)", "agent_links_collector.py")

    # Étape 2 : Scraping IA des pages formations
    run_script("Agent IA Parcoursup", "agent_parcoursup_ia.py")

    # Étape 3 : Enrichissement via Onisep
    run_script("Agent IA Onisep", "agent_onisep_ia.py")

    end = time.time()
    print(f"\n🎉 Master Agent terminé en {round(end - start, 2)} secondes")

if __name__ == "__main__":
    main()
