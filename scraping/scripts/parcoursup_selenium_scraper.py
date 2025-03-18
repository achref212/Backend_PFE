from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import json
import os
import time

output_path = os.path.join("data", "parcoursup_real_formations.json")

options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # si tu veux en mode invisible
options.add_argument("--start-maximized")

# Modifier le chemin du chromedriver si nécessaire
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://dossier.parcoursup.fr/Candidat/carte")
time.sleep(120)  # attendre le JS

soup = BeautifulSoup(driver.page_source, "html.parser")

formations = []
cards = soup.find_all("div", class_="card")  # adapter si autre classe réelle

for card in cards:
    formation = {
        "nom_formation": card.find("h3").text.strip() if card.find("h3") else "",
        "etablissement": card.find("span", class_="etablissement").text.strip() if card.find("span", class_="etablissement") else "",
        "ville": card.find("span", class_="ville").text.strip() if card.find("span", class_="ville") else "",
        "attendus": [],  # ajouter si détecté
        "specialites": [],
        "taux_admission": "",
        "debouches": []
    }
    formations.append(formation)

driver.quit()

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(formations, f, ensure_ascii=False, indent=2)

print(f"✅ Scraping réel terminé — {len(formations)} formations extraites.")
