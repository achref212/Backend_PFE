import os
from datetime import datetime
import re, json, time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    return has_logo and any("contrôlé par l'état" in b for b in badges)

def force_click(driver, element):
    try:
        driver.execute_script("arguments[0].click();", element)
        time.sleep(1)
    except Exception as e:
        try:
            ActionChains(driver).move_to_element(element).click().perform()
            time.sleep(1)
        except Exception as err:
            print(f"[⚠️] Force click failed: {err}")

def click_tab(driver, tab_id):
    try:
        tab = driver.find_element(By.ID, tab_id)
        force_click(driver, tab)
    except Exception as e:
        print(f"[⚠️] Tab {tab_id} non cliquable : {e}")

def extract_info_as_agent(driver, url):
    driver.get(url)
    time.sleep(2)

    # Cliquer sur tous les onglets
    for i in range(1, 7):
        click_tab(driver, f"tabpanel-{i}")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    titre_el = soup.select_one("h2.fr-h3.fr-my-1w")
    titre = clean_text(titre_el.text) if titre_el else ""
    lien_onisep = soup.find("a", string=lambda t: t and "Onisep" in t)
    lien_onisep_url = lien_onisep.get("href") if lien_onisep else ""

    # 🧠 Filieres bac (radio)
    filieres_bac = [clean_text(label.text) for label in soup.select('#radio-rich-type-bac label.fr-label')]

    # 🧠 Specialités favorisées (badge taux d'accès > 40 %)
    specialites_favorisees = []
    for bloc in soup.select("div.pca-timeline-cadre-texte"):
        taux_badge = bloc.select_one("span.fr-badge")
        if taux_badge and "taux d'accès de" in taux_badge.text:
            taux = int(re.search(r"\d+", taux_badge.text).group())
            if taux > 40:
                b_tag = bloc.select_one("b")
                if b_tag:
                    specialites_favorisees.append(clean_text(b_tag.text))

    # 🔁 SI vide, récupérer via popup modale
    if not filieres_bac or not specialites_favorisees:
        try:
            bouton = driver.find_element(By.ID, "btn-mod-infos-profil")
            force_click(driver, bouton)

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "fr-modal__body"))
            )

            popup_soup = BeautifulSoup(driver.page_source, "html.parser")
            for badge in popup_soup.select(".badge-data"):
                label = badge.select_one(".fr-text--sm")
                value = badge.select_one(".badge-data-value")
                if label and value:
                    filieres_bac.append(clean_text(label.text))
                    taux = int(re.search(r"\d+", value.text).group())
                    if taux > 40:
                        specialites_favorisees.append(clean_text(label.text))

            # Fermer la popup
            try:
                close_btn = driver.find_element(By.ID, "btn-fermer-mod-infos-profil")
                force_click(driver, close_btn)
            except Exception as e:
                print(f"[⚠️] Erreur fermeture popup : {e}")

        except Exception as e:
            print(f"⚠️ Popup non trouvée ou clic impossible : {e}")

    # 🎯 Poursuite d’études et taux d’insertion
    poursuite_etudes, taux_insertion = "", ""
    for block in soup.select("#tabpanel-5-panel div.fr-highlight"):
        percent = block.select_one("span.fr-h3")
        label = block.find("b")
        if "poursuivent" in block.text.lower():
            poursuite_etudes = f"{percent.text} - {label.text}" if percent and label else ""
        elif "emploi" in block.text.lower():
            taux_insertion = f"{percent.text} - {label.text}" if percent and label else ""

    return {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "titre": titre,
        "etablissement": clean_text(soup.select_one("#tabpanel-6-panel b").text.split("(")[0]) if soup.select_one("#tabpanel-6-panel b") else "",
        "type_formation": clean_text(soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4").text) if soup.select_one("h2.fr-h3.fr-my-1w span.fr-h4") else "",
        "type_etablissement": clean_text(soup.select_one("span#badge-type-contrat").text) if soup.select_one("span#badge-type-contrat") else "",
        "formation_controlee_par_etat": is_etat_controlled(soup),
        "badges": [clean_text(b.text) for b in soup.select("#header-ff-liste-badges span.fr-badge")],
        "apprentissage": "Oui" if "apprentissage" in soup.text.lower() else "Non",
        "lieu": clean_text(" ".join(soup.select_one("#tabpanel-6-panel").stripped_strings)) if soup.select_one("#tabpanel-6-panel") else "",
        "prix_annuel": clean_price(soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p").text) if soup.select_one("#tabpanel-1-panel .fr-callout .fr-mb-2w p") else 0.0,
        "salaire_moyen": clean_price(soup.select_one("p.ff-salaires-median").text) if soup.select_one("p.ff-salaires-median") else 0.0,
        "salaire_bornes": {
            "min": clean_price(soup.select_one("div.ff-salaires-borne-1").text) if soup.select_one("div.ff-salaires-borne-1") else 0.0,
            "max": clean_price(soup.select_one("div.ff-salaires-borne-2").text) if soup.select_one("div.ff-salaires-borne-2") else 0.0,
        },
        "filieres_bac": list(set(filieres_bac)),
        "specialites_favorisees": list(set(specialites_favorisees)),
        "poursuite_etudes": poursuite_etudes,
        "taux_insertion": taux_insertion,
        "matieres_enseignees": "\n".join(clean_text(e.text) for e in soup.select("#tabpanel-1-panel, #tabpanel-2-panel, #tabpanel-3-panel")),
        "debouches": {
            "metiers": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:-soup-contains('métiers') + ul li")],
            "secteurs": [clean_text(li.text) for li in soup.select("#tabpanel-5-panel h4:-soup-contains('secteurs') + ul li")]
        },
        "lien_onisep": lien_onisep_url
    }

def run_agent_on_all_links(
    input_file="missing_links.json",
    output_file="formations_parcoursup.json"
):
    print("🤖 Démarrage de l'agent IA Parcoursup avec sauvegarde progressive...")

    # Charger tous les liens
    with open(input_file, "r", encoding="utf-8") as f:
        all_links = json.load(f)

    # Charger les formations déjà traitées
    existing_data = []
    processed_links = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
                processed_links = set(item["url"] for item in existing_data if "url" in item)
            except:
                existing_data = []

    # Filtrer les liens déjà traités
    to_process = [link for link in all_links if link not in processed_links]
    print(f"🔗 {len(to_process)} formations à traiter.")

    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    new_results = []
    save_every = 1000

    for i, link in enumerate(to_process):
        print(f"\n🔍 ({i+1}/{len(to_process)}) Scraping : {link}")
        try:
            data = extract_info_as_agent(driver, link)
            if data:
                new_results.append(data)
                print("✅ Formation ajoutée.")
            else:
                print("⚠️ Ignorée (aucune donnée)")
        except Exception as e:
            print(f"❌ Erreur sur {link} : {e}")

        time.sleep(1)

        # 💾 Sauvegarde toutes les 1000 formations
        if len(new_results) % save_every == 0:
            partial = existing_data + new_results
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(partial, f, ensure_ascii=False, indent=2)
            print(f"💾 Sauvegarde intermédiaire : {len(partial)} formations enregistrées.")

    driver.quit()

    # 📦 Sauvegarde finale
    final = existing_data + new_results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Fin de scraping. {len(final)} formations enregistrées dans : {output_file}")

# Exécution automatique
if __name__ == "__main__":
    run_agent_on_all_links()
