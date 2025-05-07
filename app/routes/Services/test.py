import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def clean_text(text):
    return ' '.join(text.split()).strip() if isinstance(text, str) else ""

def extract_range(text):
    match = re.search(r"entre (\d+[,.]?\d*) et (\d+[,.]?\d*)", text)
    return (match.group(1), match.group(2)) if match else ("", "")

def parse_intervalles_per_bac(li_elements, bac_label):
    low = mid = high = ""
    if len(li_elements) == 2:
        a1, a2 = extract_range(li_elements[0])
        b1, b2 = extract_range(li_elements[1])
        if all([a1, a2, b1, b2]):
            low = f"{a1} - {a2}"
            try:
                b2_float = float(b2.replace(",", "."))
                b2_minus1 = round(b2_float - 1, 2)
                high = f"{b2_minus1} - {b2}"
                a2_float = float(a2.replace(",", "."))
                mid = f"{a2} - {int(b2_float - 1)}"
            except:
                high = f"? - {b2}"
                mid = f"{a2} - ?"
    elif len(li_elements) == 3:
        low = " - ".join(extract_range(li_elements[0]))
        mid = " - ".join(extract_range(li_elements[1]))
        high = " - ".join(extract_range(li_elements[2]))

    return {
        "Intervalle des 10% admis les + bas": {bac_label: low},
        "Intervalle des 80% admis": {bac_label: mid},
        "Intervalle des 10% admis les + hauts": {bac_label: high}
    }

def scroll_and_extract_doublettes(driver):
    try:
        ul_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pca-liste-combinaisons-scrollable"))
        )

        # Scroll jusqu'en bas
        last_height = 0
        while True:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", ul_element)
            time.sleep(0.5)
            new_height = driver.execute_script("return arguments[0].scrollTop", ul_element)
            if new_height == last_height:
                break
            last_height = new_height

        # Parsing
        soup = BeautifulSoup(driver.page_source, "html.parser")
        ul = soup.find("ul", class_="pca-liste-combinaisons-scrollable")
        if not ul:
            print("❌ Aucun <ul> trouvé.")
            return {}

        doublettes = []
        for li in ul.find_all("li", recursive=False):
            d1 = d2 = None

            # 1️⃣ Cas <abbr>
            abbrs = li.select("div.fr-grid-row abbr")
            if len(abbrs) == 2:
                d1 = abbrs[0].text.strip()
                d2 = abbrs[1].text.strip()

            # 2️⃣ Cas fallback <div.pca-liste-combinaisons-item>
            elif len(li.select("div.pca-liste-combinaisons-item")) == 2:
                items = li.select("div.pca-liste-combinaisons-item")
                d1 = items[0].get_text(strip=True)
                d2 = items[1].get_text(strip=True)

            # 3️⃣ Cas unique dans <li class="pca-liste-combinaisons-item">
            elif "pca-liste-combinaisons-item" in li.get("class", []):
                doublette = li.get_text(strip=True)
                if doublette and doublette not in doublettes:
                    doublettes.append(doublette)
                continue

            if d1 and d2:
                doublette = f"{d1} & {d2}"
                if doublette not in doublettes:
                    doublettes.append(doublette)

        # Impression complète
        print("\n📋 Toutes les doublettes extraites :")
        for d in doublettes:
            print("-", d)

        if not doublettes:
            print("⚠️ Aucune doublette trouvée.")
            return {}

        # Les 3 premières
        result = {}
        for i, combo in enumerate(doublettes[:3]):
            result[f"{i+1})"] = combo
        if len(doublettes) > 3:
            result["autres"] = "Et d'autres élèves ont aussi été admis avec d'autres doublettes."

        return result

    except Exception as e:
        print(f"❌ Erreur lors de l'extraction des doublettes : {e}")
        return {}
def extract_all_doublettes_par_bac(driver):
    radio_ids = {
        "Pour Tle Générale": "rad-1",
        "Pour Tle Techno": "rad-2",
        "Pour Tle Pro": "rad-3"
    }

    doublettes_par_bac = {}

    try:
        tab_chiffres = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tabpanel-4")))
        driver.execute_script("arguments[0].click();", tab_chiffres)
        time.sleep(1)

        for bac_label, radio_id in radio_ids.items():
            try:
                # Sélectionner le bouton radio correspondant au Bac
                radio = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, radio_id)))
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(1)

                # Aller à l'onglet "admis"
                tab_admis = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tabpanel-admis")))
                driver.execute_script("arguments[0].click();", tab_admis)
                time.sleep(1.5)

                # Scroll et extraction
                doublettes = scroll_and_extract_doublettes(driver)

                doublettes_par_bac[bac_label] = doublettes

            except Exception as e:
                print(f"[⚠️] Erreur doublettes pour {bac_label} : {e}")
                doublettes_par_bac[bac_label] = {}

    except Exception as e:
        print(f"[❌] Erreur globale doublettes : {e}")

    return doublettes_par_bac
def extract_all_intervalles(driver):
    intervalles_final = {
        "Intervalle des 10% admis les + bas": {},
        "Intervalle des 80% admis": {},
        "Intervalle des 10% admis les + hauts": {}
    }
    radio_ids = {
        "Pour Tle Générale": "rad-1",
        "Pour Tle Techno": "rad-2",
        "Pour Tle Pro": "rad-3"
    }
    try:
        tab_chiffres = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tabpanel-4")))
        driver.execute_script("arguments[0].click();", tab_chiffres)
        time.sleep(1)

        for bac_label, radio_id in radio_ids.items():
            try:
                radio = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, radio_id)))
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(1)

                tab_admis = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tabpanel-admis")))
                driver.execute_script("arguments[0].click();", tab_admis)
                time.sleep(1)

                soup = BeautifulSoup(driver.page_source, "html.parser")
                bloc = soup.select_one("#tabpanel-admis-panel .fr-col-12.fr-col-lg-6 .fr-mt-7w")
                li_elements = [clean_text(li.text) for li in bloc.select("ul li")] if bloc else []

                parsed = parse_intervalles_per_bac(li_elements, bac_label)
                for section in intervalles_final:
                    intervalles_final[section][bac_label] = parsed[section][bac_label]

            except Exception as e:
                print(f"[⚠️] Erreur pour {bac_label} : {e}")

    except Exception as e:
        print(f"[❌] Erreur globale : {e}")

    return intervalles_final

if __name__ == "__main__":
    options = Options()
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)

    driver.get("https://dossier.parcoursup.fr/Candidats/public/fiches/afficherFicheFormation?g_ta_cod=9197&typeBac=0&originePc=0")
    time.sleep(2)

    intervalles = extract_all_intervalles(driver)
    print("\n📊 Intervalles par Bac :")
    for section, data in intervalles.items():
        print(f"\n🔹 {section}")
        for bac, val in data.items():
            print(f"  {bac}: {val}")

    print("\n📚 Doublettes de spécialités les plus favorables à la sélection :")
    doublettes_par_bac = extract_all_doublettes_par_bac(driver)

    for bac_label, result in doublettes_par_bac.items():
        print(f"\n🔸 {bac_label}")
        if result:
            for key, val in result.items():
                print(f"{key} {val}")
        else:
            print("⚠️ Aucune doublette trouvée.")

    driver.quit()