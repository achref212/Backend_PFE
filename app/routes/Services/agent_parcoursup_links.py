from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time, json

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)

base_url = "https://dossier.parcoursup.fr/Candidat/carte"
formation_links = []

current_page = 1

def extract_links():
    try:
        wait.until(EC.presence_of_element_located((By.ID, "courses-cards")))
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#courses-cards a.fr-btn[href*='afficherFicheFormation']")))

        cards = driver.find_elements(By.CSS_SELECTOR, "#courses-cards a.fr-btn[href*='afficherFicheFormation']")
        links = [a.get_attribute("href") for a in cards if a.get_attribute("href")]

        if not links:
            print(f"⚠️ Aucune carte détectée à la page {current_page}.")
        else:
            print(f"📥 Liens collectés à la page {current_page} : {len(links)}")
            formation_links.extend(links)

    except Exception as e:
        print(f"⛔️ Erreur pendant l'extraction des liens (page {current_page}) : {e}")
        with open(f"debug_page_{current_page}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

try:
    driver.get(base_url)
    time.sleep(2)

    # ✅ Accept cookies
    try:
        cookie_button = wait.until(EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2")))
        driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
        time.sleep(1)
        cookie_button.click()
        print("✅ Cookies acceptés.")
    except Exception as e:
        print(f"⚠️ Cookies pas acceptés : {e}")

    print(f"\n📄 Analyse de la page {current_page} (première page)...")
    extract_links()

    # 🔁 Pagination
    while True:
        try:
            current_page += 1
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fr-pagination__link--next")))
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)

            try:
                next_button.click()
            except:
                ActionChains(driver).move_to_element(next_button).click().perform()

            time.sleep(3)
            print(f"\n➡️ Passage à la page {current_page}...")
            extract_links()

        except Exception as e:
            print(f"⛔️ Fin de pagination ou erreur à la page {current_page} : {e}")
            break

finally:
    driver.quit()

# 💾 Save
with open("parcoursup_links.json", "w", encoding="utf-8") as f:
    json.dump(formation_links, f, indent=2, ensure_ascii=False)

print(f"\n✅ Total de {len(formation_links)} liens collectés.")
print("📁 Fichier sauvegardé : parcoursup_formation_links.json")
