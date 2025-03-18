import scrapy
from parcoursup_scraper.items import FormationItem


class FormationsSpider(scrapy.Spider):
    name = "formations"
    start_urls = ['https://dossier.parcoursup.fr/Candidat/carte']  # URL cible (JavaScript)

    def parse(self, response):
        # ⚠ INFO : Cette page est générée par JavaScript → Scrapy ne voit pas le contenu dynamiquement.
        # Tu peux garder ce bloc temporairement en test avec des données fictives :

        formations = [
            {
                "nom_formation": "Licence Informatique",
                "etablissement": "Université Paris",
                "ville": "Paris",
                "attendus": ["Mathématiques", "Logique", "Autonomie"],
                "specialites": ["NSI", "Maths", "Physique"],
                "taux_admission": "40%",
                "debouches": ["Développeur", "Ingénieur logiciel"]
            },
            {
                "nom_formation": "BUT Informatique",
                "etablissement": "IUT Nice",
                "ville": "Nice",
                "attendus": ["Esprit d’analyse", "Autonomie"],
                "specialites": ["NSI", "Maths"],
                "taux_admission": "35%",
                "debouches": ["Technicien systèmes", "Développeur Fullstack"]
            }
        ]

        for f in formations:
            item = FormationItem()
            item['nom_formation'] = f['nom_formation']
            item['etablissement'] = f['etablissement']
            item['ville'] = f['ville']
            item['attendus'] = f['attendus']
            item['specialites'] = f['specialites']
            item['taux_admission'] = f['taux_admission']
            item['debouches'] = f['debouches']
            yield item