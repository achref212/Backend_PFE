from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import json

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(), options=options)
wait = WebDriverWait(driver, 20)

base_url = "https://dossier.parcoursup.fr/Candidat/carte"
formation_links = []

try:
    driver.get(base_url)

    # ✅ Accepter les cookies
    try:
        cookie_button = wait.until(EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2")))
        driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
        time.sleep(1)
        cookie_button.click()
        print("✅ Cookies acceptés.")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'acceptation des cookies : {e}")


    def extract_links():
        try:
            # Attendre que les cartes de formation soient présentes
            wait.until(EC.presence_of_element_located((By.ID, "courses-cards")))
            cards = driver.find_elements(By.CSS_SELECTOR, "#courses-cards a.fr-btn[href*='afficherFicheFormation']")
            links = [a.get_attribute("href") for a in cards if a.get_attribute("href")]
            print(f"📄 Liens extraits sur cette page : {len(links)}")
            formation_links.extend(links)
        except Exception as e:
            print(f"⛔️ Erreur pendant l'extraction des liens : {e}")


    # Extraire les liens de la première page
    extract_links()

    while True:
        try:
            # Attendre que le bouton 'Page suivante' soit cliquable
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fr-pagination__link--next")))

            # Faire défiler jusqu'au bouton pour s'assurer qu'il est visible
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)

            # Essayer de cliquer sur le bouton 'Suivant' en le forçant si nécessaire
            try:
                next_button.click()
            except Exception:
                # Si le clic échoue, utiliser ActionChains pour forcer le clic
                ActionChains(driver).move_to_element(next_button).click().perform()

            time.sleep(2)  # Attendre que la page se charge
            print("✅ Passage à la page suivante.")

            # Attendre que les nouvelles cartes soient présentes avant d'extraire
            extract_links()
        except Exception as e:
            print(f"⛔️ Fin de pagination ou erreur : {e}")
            break

finally:
    driver.quit()

# Sauvegarder dans un fichier JSON
with open("parcoursup_formation_links.json", "w", encoding="utf-8") as f:
    json.dump(formation_links, f, indent=2, ensure_ascii=False)

print("✅ Fichier sauvegardé : parcoursup_formation_links.json")