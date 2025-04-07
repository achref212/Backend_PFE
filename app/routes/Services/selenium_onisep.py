from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import os

def update_if_empty(field, value, formation):
    if not formation.get(field):
        formation[field] = value.strip() if isinstance(value, str) else value

def enrich_with_onisep(formation):
    lien = formation.get("lien_onisep")
    if not lien:
        print(f"⚠️ Pas de lien Onisep pour la formation : {formation.get('titre', 'Titre inconnu')}")
        return formation

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(lien)
        time.sleep(2)

        try:
            duree = driver.find_element(By.XPATH, "//*[contains(text(),'Durée de la formation')]/strong").text
            update_if_empty("duree", duree, formation)
        except:
            pass

        try:
            resume = driver.find_element(By.XPATH, "//div[@id='objectifs-formation']//p[1]").text
            update_if_empty("resume_programme", resume, formation)
        except:
            pass

        try:
            metiers = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='exemples-metiers']//ul/li/a")]
        except:
            metiers = []

        try:
            secteurs = driver.find_element(By.XPATH, "//div[@id='debouches-professionnels']//p").text
        except:
            secteurs = ""

        if not formation.get("debouches") or not isinstance(formation.get("debouches"), dict):
            formation["debouches"] = {
                "metiers": metiers,
                "secteurs": secteurs.strip()
            }
        else:
            if not formation["debouches"].get("metiers"):
                formation["debouches"]["metiers"] = metiers
            if not formation["debouches"].get("secteurs"):
                formation["debouches"]["secteurs"] = secteurs.strip()

        try:
            poursuite_txt = driver.find_element(By.XPATH, "//div[@id='poursuites-etudes']//p").text
        except:
            poursuite_txt = ""
        try:
            poursuite_list = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='poursuites-etudes']//ul/li/a")]
        except:
            poursuite_list = []

        poursuite_final = poursuite_txt + " | " + ", ".join(poursuite_list) if poursuite_txt else ", ".join(poursuite_list)
        update_if_empty("poursuite_etudes", poursuite_final, formation)

        try:
            taux = [el.text for el in driver.find_elements(By.XPATH, "//div[@id='inserjeune']//p/span/strong")]
            if taux:
                taux_str = " | ".join(taux)
                update_if_empty("taux_insertion", taux_str, formation)
        except:
            pass

    finally:
        driver.quit()

    return formation

if __name__ == "__main__":
    json_path = "parcoursup.json"
    output_path = "parcoursup_updated.json"

    with open(json_path, "r", encoding="utf-8") as f:
        parcoursup_data = json.load(f)

    print(f"🔍 Traitement de : {parcoursup_data.get('titre', 'Sans titre')}")
    updated = enrich_with_onisep(parcoursup_data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent=2, ensure_ascii=False)

    print(f"✅ Données enrichies sauvegardées dans : {output_path}")