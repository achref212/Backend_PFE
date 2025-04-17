import os
import time
import subprocess
from langchain_core.runnables import RunnableLambda


def run_script(name, script):
    print(f"\n🚀 Lancement de : {name}")
    try:
        subprocess.run(["python", script], check=True)
        print(f"✅ Terminé : {name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur dans {name} : {e}")
        raise e


# === Agents convertis en RunnableLangChain ===
# Étape 1 : Collecte des liens depuis la carte Parcoursup
    # run_script("Agent Collecteur de liens (Parcoursup)", "agent_parcoursup_links.py")

    # Étape 2 : Scraping IA des pages formations
    #run_script("Agent IA Parcoursup", "agent_parcoursup_ia.py")
agent_collect_links = RunnableLambda(lambda x: run_script("Agent Collect Links", "agent_parcoursup_links.py") or x)
agent_Parcoursup = RunnableLambda(lambda x: run_script("Agent IA Parcoursup", "agent_parcoursup_ia.py") or x)
agent_verify_links = RunnableLambda(lambda x: run_script("Agent Verify Links", "verify_scraped_links.py") or x)
agent_verify_formations = RunnableLambda(lambda x: run_script("Agent Verify Formations", "agent_verify.py") or x)
agent_enrich_onisep = RunnableLambda(lambda x: run_script("Agent IA Onisep", "agent_onisep_ia.py") or x)
agent_verify_onisep = RunnableLambda(lambda x: run_script("Agent IA Onisep", "verify_scraped_formation.py") or x)
agent_data_cleaning = RunnableLambda(lambda x: run_script("Agent Nettoyage IA", "multi_agent_cleaning_tg.py") or x)

# ✅ Séquence multi-agent LangChain
multi_agent_flow = (
    agent_collect_links
    |agent_Parcoursup
    | agent_verify_links
    | agent_verify_formations
    | agent_enrich_onisep
    | agent_verify_onisep
    | agent_data_cleaning
)


def main():
    start = time.time()
    print("🤖 Démarrage du Master Agent Multi-Étapes...")

    try:
        result = multi_agent_flow.invoke("start")
        print(f"\n✅ Orchestration terminée.")
    except Exception as e:
        print(f"\n⛔️ Erreur pendant l’orchestration : {e}")

    print(f"\n⏱️ Temps total : {round(time.time() - start, 2)} secondes")


if __name__ == "__main__":
    main()
