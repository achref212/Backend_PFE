from datetime import datetime
import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

# Champs à vérifier / remplir
EXPECTED_FIELDS = [
    "titre", "etablissement", "type_formation", "filieres_bac", "specialites_favorisees", "lieu",
    "prix_annuel", "duree", "formation_controlee_par_etat", "apprentissage", "type_etablissement",
    "debouches", "poursuite_etudes", "salaire_moyen", "taux_insertion", "matieres_enseignees",
    "lien_onisep", "resume_programme"
]

def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""

def update_if_empty(field, value, formation):
    if not formation.get(field) and value:
        formation[field] = clean_text(value)
    elif field not in formation:
        formation[field] = clean_text(value) if value else ""

def enrich_with_onisep(formation, driver):
    lien = formation.get("lien_onisep", "")
    if not lien or lien.startswith("Aucun"):
        for field in EXPECTED_FIELDS:
            if field not in formation:
                formation[field] = "" if field != "debouches" else {"metiers": [], "secteurs": ""}
        return formation

    try:
        driver.get(lien)
        time.sleep(2)

        # ✅ Type de formation + durée (div tag)
        try:
            container = driver.find_element(By.ID, "type-de-formation")
            html = container.get_attribute("innerHTML")
            duree_el = driver.find_element(By.XPATH, "//div[contains(@class, 'tag') and contains(., 'Durée de la formation')]//strong")

            match_type = re.search(r"Type de formation\s*:\s*</span>\s*<span[^>]*>\s*<strong>(.*?)</strong>", html)

            update_if_empty("type_formation", match_type.group(1) if match_type else "", formation)
            update_if_empty("duree", duree_el.text if duree_el else "", formation)
        except Exception as e:
            print("[⚠️] Type ou durée non trouvée :", e)

        # ✅ Résumé programme
        try:
            resume = driver.find_element(By.CSS_SELECTOR, "#objectifs-formation p").text
            update_if_empty("resume_programme", resume, formation)
        except:
            update_if_empty("resume_programme", "", formation)

        # ✅ Métiers
        metiers = []
        try:
            # Structure avec des <strong> dans .card-body
            cards = driver.find_elements(By.CSS_SELECTOR, "#exemples-metiers .card-body strong")
            metiers = [m.text for m in cards if m.text.strip()]
        except:
            pass

        # Structure alternative : plusieurs <ul><li><a> dans #exemples-metiers
        if not metiers:
            try:
                metiers = [a.text.strip() for a in driver.find_elements(By.CSS_SELECTOR, "#exemples-metiers ul li a") if
                           a.text.strip()]
            except:
                pass

        # ✅ Secteurs
        try:
            secteurs = driver.find_element(By.CSS_SELECTOR, "#debouches-professionnels p").text
        except:
            secteurs = ""

        if not formation.get("debouches") or not isinstance(formation.get("debouches"), dict):
            formation["debouches"] = {"metiers": metiers, "secteurs": clean_text(secteurs)}
        else:
            if not formation["debouches"].get("metiers"):
                formation["debouches"]["metiers"] = metiers
            if not formation["debouches"].get("secteurs"):
                formation["debouches"]["secteurs"] = clean_text(secteurs)

        # ✅ Poursuite d'études
        poursuite_txt, poursuite_list = "", []
        try:
            poursuite_txt = driver.find_element(By.CSS_SELECTOR, "#poursuites-etudes p").text
        except:
            pass
        try:
            poursuite_list = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "#poursuites-etudes li a")]
        except:
            pass
        poursuite_final = poursuite_txt + " | " + ", ".join(poursuite_list) if poursuite_txt else ", ".join(poursuite_list)
        update_if_empty("poursuite_etudes", poursuite_final, formation)

        # ✅ Taux d'insertion
        try:
            taux = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='inserjeune']//p/span/strong")]
            update_if_empty("taux_insertion", " | ".join(taux) if taux else "", formation)
        except:
            update_if_empty("taux_insertion", "", formation)

    except Exception as e:
        print(f"❌ Erreur enrichissement ONISEP : {e}")

    # Complétion des champs vides
    for field in EXPECTED_FIELDS:
        if field not in formation:
            if field == "debouches":
                formation[field] = {"metiers": [], "secteurs": ""}
            else:
                formation[field] = ""

    return formation


def run_onisep_agent(input_file="formations_parcoursup.json", output_file="parcoursup_updated.json"):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    print("🤖 Agent IA ONISEP démarré...")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    updated_data = []
    for formation in tqdm(data, desc="🔁 Traitement des formations"):
        enriched = enrich_with_onisep(formation, driver)
        updated_data.append(enriched)

    driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Données enrichies sauvegardées dans : {output_file}")


if __name__ == "__main__":
    run_onisep_agent()
