import os

def run_parcoursup_scraping():
    print("🔍 Lancement du scraping réel Parcoursup (Selenium)...")
    status = os.system("python scraping/scripts/parcoursup_selenium_scraper.py")
    if status != 0:
        print("❌ Erreur lors du scraping Parcoursup.")
        return False
    print("✅ Scraping Parcoursup terminé.")
    return True

def run_faiss_encoding():
    print("🧠 Lancement de l'encodage sémantique + indexation FAISS...")
    status = os.system("python indexing/encode_and_index.py")
    if status != 0:
        print("❌ Erreur pendant l'encodage/indexation FAISS.")
        return False
    print("✅ Indexation FAISS terminée avec succès.")
    return True

def launch_flask_api():
    print("🚀 Lancement de l'API Flask (http://127.0.0.1:5000/query_rag)...")
    os.system("python app.py")

def main():
    print("📦 PIPELINE DE SCRAPING ET ENCODAGE LLM POUR PFE\n")

    if not run_parcoursup_scraping():
        return

    if not run_faiss_encoding():
        return

    launch_flask_api()

if __name__ == "__main__":
    main()
