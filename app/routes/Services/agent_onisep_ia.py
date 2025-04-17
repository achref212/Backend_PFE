from datetime import datetime
import json
import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import requests

# Champs à vérifier / remplir
EXPECTED_FIELDS = [
    "titre", "etablissement", "type_formation", "filieres_bac", "specialites_favorisees", "lieu",
    "prix_annuel", "duree", "formation_controlee_par_etat", "apprentissage", "type_etablissement",
    "debouches", "poursuite_etudes", "salaire_moyen", "taux_insertion", "matieres_enseignees",
    "lien_onisep", "resume_programme"
]

def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""

def update_if_empty(field, value, formation, changes):
    cleaned = clean_text(value)
    if not formation.get(field) and cleaned:
        formation[field] = cleaned
        changes.append(field)
    elif field not in formation:
        formation[field] = cleaned if cleaned else ""
        changes.append(field)

def enrich_with_onisep(formation, driver):
    lien = formation.get("lien_onisep", "")
    changes = []

    if not lien or lien.startswith("Aucun"):
        for field in EXPECTED_FIELDS:
            if field not in formation:
                formation[field] = "" if field != "debouches" else {"metiers": [], "secteurs": ""}
        return formation, changes

    try:
        driver.set_page_load_timeout(60)
        driver.get(lien)
        time.sleep(2)

        # ✅ Type + durée
        try:
            container = driver.find_element(By.ID, "type-de-formation")
            html = container.get_attribute("innerHTML")
            duree_el = driver.find_element(By.XPATH, "//div[contains(@class, 'tag') and contains(., 'Durée de la formation')]//strong")
            match_type = re.search(r"Type de formation\s*:\s*</span>\s*<span[^>]*>\s*<strong>(.*?)</strong>", html)
            update_if_empty("type_formation", match_type.group(1) if match_type else "", formation, changes)
            update_if_empty("duree", duree_el.text if duree_el else "", formation, changes)
        except Exception as e:
            print("[⚠️] Type ou durée non trouvée :", e)

        # ✅ Résumé
        try:
            resume = driver.find_element(By.CSS_SELECTOR, "#objectifs-formation p").text
            update_if_empty("resume_programme", resume, formation, changes)
        except:
            update_if_empty("resume_programme", "", formation, changes)

        # ✅ Métiers
        metiers = []
        try:
            cards = driver.find_elements(By.CSS_SELECTOR, "#exemples-metiers .card-body strong")
            metiers = [m.text for m in cards if m.text.strip()]
        except:
            pass
        if not metiers:
            try:
                metiers = [a.text.strip() for a in driver.find_elements(By.CSS_SELECTOR, "#exemples-metiers ul li a") if a.text.strip()]
            except:
                pass

        # ✅ Secteurs
        try:
            secteurs = driver.find_element(By.CSS_SELECTOR, "#debouches-professionnels p").text
        except:
            secteurs = ""

        if not formation.get("debouches") or not isinstance(formation.get("debouches"), dict):
            formation["debouches"] = {"metiers": metiers, "secteurs": clean_text(secteurs)}
            changes.append("debouches")
        else:
            if not formation["debouches"].get("metiers") and metiers:
                formation["debouches"]["metiers"] = metiers
                changes.append("debouches.metiers")
            if not formation["debouches"].get("secteurs") and secteurs:
                formation["debouches"]["secteurs"] = clean_text(secteurs)
                changes.append("debouches.secteurs")

        # ✅ Poursuite
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
        update_if_empty("poursuite_etudes", poursuite_final, formation, changes)

        # ✅ Insertion
        try:
            taux = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='inserjeune']//p/span/strong")]
            update_if_empty("taux_insertion", " | ".join(taux) if taux else "", formation, changes)
        except:
            update_if_empty("taux_insertion", "", formation, changes)

    except Exception as e:
        print(f"❌ Erreur enrichissement ONISEP : {e}")
        raise e

    # Finaliser les champs
    for field in EXPECTED_FIELDS:
        if field not in formation:
            formation[field] = "" if field != "debouches" else {"metiers": [], "secteurs": ""}
            changes.append(field)

    return formation, changes

def run_onisep_agent(
    input_file="formations_parcoursup.json",
    output_file="parcoursup_updated.json",
    retry_file="onisep_retry.json"
):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    print("🤖 Agent IA ONISEP démarré...")

    with open(input_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    if not isinstance(all_data, list):
        all_data = [all_data]

    # Charger les formations déjà enrichies
    existing_data = []
    processed_links = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                processed_links = {f["url"] for f in existing_data if "url" in f}
            except:
                existing_data = []

    # Calculer les formations manquantes à enrichir
    input_urls = {f["url"] for f in all_data if "url" in f}
    not_yet_processed = [f for f in all_data if f.get("url") not in processed_links]
    already_enriched = [f for f in existing_data if f.get("url") in input_urls]

    updated_data = already_enriched.copy()
    failed_links = []
    counter = 0

    for formation in tqdm(not_yet_processed, desc="🔁 Enrichissement Onisep"):
        url = formation.get("url")
        try:
            enriched, modified_fields = enrich_with_onisep(formation, driver)
            updated_data.append(enriched)

            if modified_fields:
                print(f"🛠️ {formation.get('titre')} → Champs modifiés : {modified_fields}")
            else:
                print(f"✅ {formation.get('titre')} → Aucune mise à jour")
        except Exception as e:
            print(f"⛔️ Formation ignorée (échec) : {url}")
            failed_links.append(formation)

        counter += 1
        if counter % 500 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Sauvegarde intermédiaire après {counter} formations...")

    driver.quit()

    # Enregistrement final
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ {len(updated_data)} formations enrichies sauvegardées dans : {output_file}")

    if failed_links:
        with open(retry_file, "w", encoding="utf-8") as f:
            json.dump(failed_links, f, indent=2, ensure_ascii=False)
        print(f"⚠️ {len(failed_links)} formations échouées sauvegardées dans : {retry_file}")

if __name__ == "__main__":
    run_onisep_agent()
