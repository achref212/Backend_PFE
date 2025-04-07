from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time, json
from datetime import datetime

def update_if_empty(field, value, formation):
    if not formation.get(field) and value:
        formation[field] = value.strip() if isinstance(value, str) else value

def enrich_with_onisep(formation, driver):
    lien = formation.get("lien_onisep")
    if not lien:
        print(f"⚠️ Pas de lien Onisep pour la formation : {formation.get('titre', 'Titre inconnu')}")
        return formation

    try:
        driver.get(lien)
        time.sleep(2)

        # ✅ Durée de la formation
        try:
            duree = driver.find_element(By.XPATH, "//*[contains(text(),'Durée de la formation')]/following-sibling::strong").text
            update_if_empty("duree", duree, formation)
        except Exception as e:
            print(f"[Durée non trouvée] {e}")

        # ✅ Résumé du programme
        try:
            resume = driver.find_element(By.CSS_SELECTOR, "#objectifs-formation p").text
            update_if_empty("resume_programme", resume, formation)
        except Exception as e:
            print(f"[Résumé non trouvé] {e}")

        # ✅ Exemples de métiers (cartes ou liste)
        metiers = []
        try:
            metier_cards = driver.find_elements(By.CSS_SELECTOR, "#exemples-metiers .card-body strong")
            metiers = [m.text for m in metier_cards if m.text.strip()]
        except:
            try:
                metiers = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='exemples-metiers']//ul/li/a")]
            except:
                metiers = []

        # ✅ Secteurs d’activité
        try:
            secteurs = driver.find_element(By.CSS_SELECTOR, "#debouches-professionnels p").text
        except:
            secteurs = ""

        # Injection dans le champ "debouches"
        if not formation.get("debouches") or not isinstance(formation.get("debouches"), dict):
            formation["debouches"] = {"metiers": metiers, "secteurs": secteurs.strip()}
        else:
            if not formation["debouches"].get("metiers"):
                formation["debouches"]["metiers"] = metiers
            if not formation["debouches"].get("secteurs"):
                formation["debouches"]["secteurs"] = secteurs.strip()

        # ✅ Poursuite d’études
        try:
            poursuite_txt = driver.find_element(By.CSS_SELECTOR, "#poursuites-etudes p").text
        except:
            poursuite_txt = ""
        try:
            poursuite_list = [el.text for el in driver.find_elements(By.CSS_SELECTOR, "#poursuites-etudes li a")]
        except:
            poursuite_list = []

        poursuite_final = poursuite_txt + " | " + ", ".join(poursuite_list) if poursuite_txt else ", ".join(poursuite_list)
        update_if_empty("poursuite_etudes", poursuite_final, formation)

        # ✅ Taux d'insertion (multiple %)
        try:
            taux = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='inserjeune']//p/span/strong")]
            if taux:
                update_if_empty("taux_insertion", " | ".join(taux), formation)
        except:
            pass

    except Exception as e:
        print(f"❌ Erreur de chargement de la page ONISEP : {e}")

    return formation

def run_onisep_agent(input_file="formations_scraped.json", output_file="parcoursup_updated.json"):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    print("🚀 Agent ONISEP en cours...")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Si fichier contient une liste
    if isinstance(data, list):
        updated_data = []
        for i, formation in enumerate(data):
            print(f"🔍 ({i+1}/{len(data)}) {formation.get('titre', 'Titre inconnu')}")
            enriched = enrich_with_onisep(formation, driver)
            updated_data.append(enriched)
    else:
        print(f"🔍 Traitement : {data.get('titre', 'Titre inconnu')}")
        updated_data = enrich_with_onisep(data, driver)

    driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Données enrichies enregistrées dans : {output_file}")

if __name__ == "__main__":
    run_onisep_agent()
