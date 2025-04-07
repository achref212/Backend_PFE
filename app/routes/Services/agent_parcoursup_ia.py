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

def is_etat_controlled(soup):
    badges = [b.text.lower() for b in soup.select("#header-ff-liste-badges span.fr-badge")]
    has_logo = soup.select_one("img.img_labellisation") is not None
    has_etat_badge = any("contrôlé par l'état" in b for b in badges)
    return has_logo and has_etat_badge

def click_tab(driver, tab_id):
    try:
        tab = driver.find_element(By.ID, tab_id)
        ActionChains(driver).move_to_element(tab).click().perform()
        time.sleep(0.5)
    except Exception as e:
        print(f"[⚠️] Tab {tab_id} non cliquable : {e}")

def extract_info_as_agent(driver, url):
    driver.get(url)
    time.sleep(2)

    for i in range(1, 7):
        click_tab(driver, f"tabpanel-{i}")

    soup = BeautifulSoup(driver.page_source, "html.parser")

    titre_el = soup.select_one("h2.fr-h3.fr-my-1w")
    titre = titre_el.text.strip() if titre_el else ""

    badges = [clean_text(b.text) for b in soup.select("#header-ff-liste-badges span.fr-badge")]
    is_controlled = is_etat_controlled(soup)
    lien_onisep = soup.find("a", string=lambda t: "Onisep" in t)
    lien_onisep_url = lien_onisep.get("href") if lien_onisep else "Aucun lien Onisep"

    return {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "titre": clean_text(titre),
        "etablissement": clean_text(
            soup.select_one("#tabpanel-6-panel b").text.split("(")[0]
        ) if soup.select_one("#tabpanel-6-panel b") else "",
        "type_formation": clean_text(
            soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4") and soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4").text
        ),
        "type_etablissement": clean_text(
            soup.select_one("span#badge-type-contrat") and soup.select_one("span#badge-type-contrat").text
        ),
        "formation_controlee_par_etat": is_controlled,
        "badges": badges if badges else [],
        "apprentissage": "Oui" if "apprentissage" in soup.text.lower() else "Non",
        "lieu": clean_text(" ".join(soup.select_one("#tabpanel-6-panel").stripped_strings)) if soup.select_one("#tabpanel-6-panel") else "",
        "prix_annuel": clean_price(
            soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p") and soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p").text
        ),
        "salaire_moyen": clean_price(
            soup.select_one("p.ff-salaires-median") and soup.select_one("p.ff-salaires-median").text
        ),
        "salaire_bornes": {
            "min": clean_price(soup.select_one("div.ff-salaires-borne-1") and soup.select_one("div.ff-salaires-borne-1").text),
            "max": clean_price(soup.select_one("div.ff-salaires-borne-2") and soup.select_one("div.ff-salaires-borne-2").text),
        },
        "filieres_bac": [clean_text(el.text) for el in soup.select("#tabpanel-4-panel *") if "bac" in el.text.lower()],
        "specialites_favorisees": [clean_text(el.text) for el in soup.select("#tabpanel-4-panel *") if "spécialité" in el.text.lower()],
        "matieres_enseignees": "\n".join(clean_text(e.text) for e in soup.select("#tabpanel-1-panel, #tabpanel-2-panel, #tabpanel-3-panel")),
        "debouches": {
            "metiers": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:contains('métiers') + ul li")],
            "secteurs": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:contains('secteurs') + ul li")]
        },
        "lien_onisep": lien_onisep_url
    }

def run_agent_on_all_links(input_file="parcoursup_links.json", output_file="formations_scraped.json"):
    print("🤖 Démarrage de l'agent IA Parcoursup...")
    with open(input_file, "r", encoding="utf-8") as f:
        links = json.load(f)

    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    results = []
    for i, link in enumerate(links):
        print(f"\n🔍 ({i+1}/{len(links)}) Scraping : {link}")
        try:
            data = extract_info_as_agent(driver, link)
            if data:
                results.append(data)
                print("✅ Formation ajoutée.")
            else:
                print("⚠️ Ignorée : Erreur ou données manquantes.")
        except Exception as e:
            print(f"❌ Erreur sur le lien : {e}")
        time.sleep(1)

    driver.quit()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📁 Enregistrement terminé : {len(results)} formations sauvegardées dans {output_file}")

# Lancement automatique
if __name__ == "__main__":
    run_agent_on_all_links()
