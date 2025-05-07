import os, json, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""
def force_open_tab4(driver, max_retries=5):
    """Force l'ouverture de l'onglet chiffres (tabpanel-4) avec retry"""
    for attempt in range(max_retries):
        try:
            tab4 = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "tabpanel-4")))
            driver.execute_script("arguments[0].scrollIntoView(true);", tab4)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", tab4)
            time.sleep(1.5)

            # Vérifie si le bloc est bien visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "pca-div-container"))
            )
            return True
        except Exception as e:
            print(f"[⏳] Retry ouverture tab chiffres ({attempt + 1}/{max_retries})...")
            time.sleep(1.2)
    return False


def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""


def extract_taux(driver):
    ts_taux_par_bac = {}

    # ▶️ Ouvrir l’onglet chiffres
    tab4 = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tabpanel-4")))
    driver.execute_script("arguments[0].click();", tab4)
    time.sleep(1.5)

    # 🌐 Étape 1 : Bloc global d'abord
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pca-infographie-null")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        bloc = soup.select_one("#pca-infographie-null")

        def get_val_from_img(img_class):
            img = bloc.select_one(f"img.{img_class}")
            if img:
                texte = img.find_next("div", class_="pca-timeline-cadre-texte")
                if texte:
                    val = texte.select_one("p")
                    return int(val.text.strip()) if val and val.text.strip().isdigit() else 0
            return 0

        postulants_global = get_val_from_img("pca-img-1")
        appelables_global = get_val_from_img("pca-img-2")

    except Exception as e:
        print("[❌] Échec lecture bloc global :", e)
        postulants_global = appelables_global = 0

    # Étape 2 : Collecter les bacs
    radio_ids = {
        "TS Tle système français G": ("rad-1", "pca-infographie-1"),
        "TS Tle système français T": ("rad-2", "pca-infographie-2"),
        "TS Tle système français P": ("rad-3", "pca-infographie-3")
    }

    total_post = total_appel = 0

    for label, (radio_id, bloc_id) in radio_ids.items():
        try:
            radio = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, radio_id)))
            driver.execute_script("arguments[0].click();", radio)
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, bloc_id)))
            time.sleep(1.2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            bloc = soup.select_one(f"#{bloc_id}")

            def extract_bloc_val(img_class):
                img = bloc.select_one(f"img.{img_class}")
                if img:
                    texte = img.find_next("div", class_="pca-timeline-cadre-texte")
                    if texte:
                        val = texte.select_one("p")
                        return int(val.text.strip()) if val and val.text.strip().isdigit() else 0
                return 0

            postulants = extract_bloc_val("pca-img-1")
            appelables = extract_bloc_val("pca-img-2")
            admis = extract_bloc_val("pca-img-3")
            taux_tag = bloc.select_one(".fr-badge.fr-badge--yellow-tournesol.fr-badge--sm")
            taux = clean_text(taux_tag.text).replace("Soit un taux d'accès de", "").replace("%",
                                                                                            "").strip() if taux_tag else "0"

            total_post += postulants
            total_appel += appelables

            ts_taux_par_bac[label] = {
                "postulants": postulants,
                "appelables": appelables,
                "admis": admis,
                "taux": taux
            }

        except Exception as e:
            print(f"[⚠️] Bac {label} erreur :", e)
            ts_taux_par_bac[label] = {
                "postulants": 0, "appelables": 0, "admis": 0, "taux": "0"
            }

    # Calcul des "autres"
    postulants_autres = max(1, postulants_global - total_post)
    appelables_autres = max(0, appelables_global - total_appel)
    taux_autres = round((appelables_autres / postulants_autres) * 100, 2)

    ts_taux_par_bac["TS autres élèves"] = {
        "postulants": postulants_autres,
        "appelables": appelables_autres,
        "admis": 0,
        "taux": str(taux_autres)
    }

    return ts_taux_par_bac
def is_formation_selective(soup):
    badges = [clean_text(b.text).lower() for b in soup.select("#header-ff-liste-badges span.fr-badge")]
    return any("formation sélective" in b for b in badges)
MAX_RETRIES = 3

def extract_minimal_info(driver, url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[🔄] Tentative {attempt}/{max_retries} : {url}")
            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            titre_el = soup.select_one("h2.fr-h3.fr-my-1w")
            titre = clean_text(titre_el.contents[0]) if titre_el and titre_el.contents else ""

            badges = [clean_text(b.text) for b in soup.select("#header-ff-liste-badges span.fr-badge")]
            selective = is_formation_selective(soup)

            # 🔓 Forcer ouverture de l'onglet chiffres
            if not force_open_tab4(driver):
                raise RuntimeError("Échec ouverture tab chiffres")

            # 📊 Récupération des taux complets (inclut les autres)
            full_ts_data = extract_all_taux_par_bac(driver)

            if not full_ts_data or "TS Tle système français G" not in full_ts_data:
                raise ValueError("Données bac manquantes ou incomplètes")

            ts_taux_par_bac = {
                label: data.get("taux", "0") for label, data in full_ts_data.items()
            }

            return {
                "url": url,
                "titre": titre,
                "formation_selective": selective,
                "badges": badges,
                "ts_taux_par_bac": ts_taux_par_bac
            }

        except Exception as e:
            print(f"[⚠️] Erreur tentative {attempt}: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                print(f"[❌] Échec définitif pour : {url}")
                return {
                    "url": url,
                    "titre": "",
                    "formation_selective": False,
                    "badges": [],
                    "ts_taux_par_bac": {}
                }
def run_scraper(input_file="all_links.json", output_file="resultats_parcoursup.json"):
    # Charger les liens depuis le fichier JSON
    with open(input_file, "r", encoding="utf-8") as f:
        links = json.load(f)

    results = []

    for i, url in enumerate(links):
        print(f"\n[{i+1}/{len(links)}] Traitement : {url}")

        options = Options()
        # options.add_argument("--headless=new")  # Active si tu veux exécuter sans afficher Chrome
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(2)

        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            titre_el = soup.select_one("h2.fr-h3.fr-my-1w")
            titre = clean_text(titre_el.contents[0]) if titre_el else ""
            badges = [clean_text(b.text) for b in soup.select("#header-ff-liste-badges span.fr-badge")]
            selective = is_formation_selective(soup)

            taux_data = extract_taux(driver)

            results.append({
                "url": url,
                "titre": titre,
                "badges": badges,
                "formation_selective": selective,
                "ts_taux_par_bac": {k: v["taux"] for k, v in taux_data.items()}
            })

        except Exception as e:
            print(f"[❌] Erreur lors de l'extraction de {url} : {e}")

        driver.quit()
        time.sleep(1)

    # Sauvegarder les résultats dans le fichier de sortie
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Données enregistrées dans : {output_file}")
# Lancer
if __name__ == "__main__":
    run_scraper()