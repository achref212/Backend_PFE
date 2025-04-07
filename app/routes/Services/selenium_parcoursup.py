from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time, re, json

def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""

def clean_price(text):
    if text:
        text = text.replace("€", "").replace(",", ".")
        numbers = re.findall(r"\d+\.?\d*", text)
        return float(numbers[0]) if numbers else 0.0
    return 0.0

def click_tab(driver, tab_id):
    try:
        tab = driver.find_element(By.ID, tab_id)
        ActionChains(driver).move_to_element(tab).click().perform()
        time.sleep(1)
    except Exception as e:
        print(f"Erreur tab {tab_id}: {e}")

def scrape_parcoursup_with_selenium(url):
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)

    for i in range(1, 7):
        click_tab(driver, f"tabpanel-{i}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    data = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "titre": clean_text(soup.select_one("h2.fr-h3.fr-my-1w").text if soup.select_one("h2.fr-h3.fr-my-1w") else ""),
        "etablissement": clean_text(soup.select_one("#tabpanel-6-panel b").text.split("(")[0] if soup.select_one("#tabpanel-6-panel b") else ""),
        "type_formation": clean_text(soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4").text if soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4") else ""),
        "type_etablissement": clean_text(soup.select_one("span#badge-type-contrat").text if soup.select_one("span#badge-type-contrat") else ""),
        "formation_controlee_par_etat": bool(soup.select_one("img.img_labellisation")),
        "verifie_par_labellisation": bool(soup.select_one("img.img_labellisation")),
        "badges": [b.text.strip() for b in soup.select("#header-ff-liste-badges span.fr-badge")],
        "apprentissage": "Oui" if "apprentissage" in soup.text.lower() else "Non",
        "lieu": clean_text(" ".join(soup.select_one("#tabpanel-6-panel").stripped_strings)) if soup.select_one("#tabpanel-6-panel") else "",

        # 💶 Prix annuel
        "prix_annuel": clean_price(soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p").text) if soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p") else 0.0,

        # 💼 Salaire
        "salaire_moyen": clean_price(soup.select_one("p.ff-salaires-median").text if soup.select_one("p.ff-salaires-median") else ""),
        "salaire_bornes": {
            "min": clean_price(soup.select_one("div.ff-salaires-borne-1").text if soup.select_one("div.ff-salaires-borne-1") else ""),
            "max": clean_price(soup.select_one("div.ff-salaires-borne-2").text if soup.select_one("div.ff-salaires-borne-2") else "")
        },

        "filieres_bac": [clean_text(el.text) for el in soup.select("#tabpanel-4-panel") if "bac" in el.text.lower()],
        "specialites_favorisees": [clean_text(el.text) for el in soup.select("#tabpanel-4-panel") if "spécialité" in el.text.lower()],

        "matieres_enseignees": "\n".join(clean_text(e.text) for e in soup.select("#tabpanel-1-panel, #tabpanel-2-panel, #tabpanel-3-panel")),

        "debouches": {
            "metiers": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:contains('métiers') + ul li")],
            "secteurs": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:contains('secteurs') + ul li")]
        },

        "lien_onisep": soup.find("a", string=lambda t: "Onisep" in t).get("href") if soup.find("a", string=lambda t: "Onisep" in t) else ""
    }

    return data

# ✅ Exemple d’utilisation et sauvegarde dans un fichier JSON
if __name__ == "__main__":
    url = "https://dossier.parcoursup.fr/Candidats/public/fiches/afficherFicheFormation?g_ta_cod=5660&typeBac=0&originePc=0"
    result = scrape_parcoursup_with_selenium(url)

    # 💾 Sauvegarde dans un fichier JSON
    with open("formations.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("✅ Données sauvegardées dans formation.json")