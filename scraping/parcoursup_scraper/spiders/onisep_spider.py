import scrapy
from parcoursup_scraper.items import FormationItem

class OnisepSpider(scrapy.Spider):
    name = "onisep"
    start_urls = [
        "https://dossierappel.parcoursup.fr/Candidats/public/fiches/afficherFicheFormation?g_ta_cod=48658&typeBac=0&originePc=0"
    ]

    def parse(self, response):
        # Scraping d'une seule fiche test (BUT Informatique)
        item = FormationItem()
        item['nom_formation'] = response.css("h1.titre-page::text").get(default="").strip()
        item['etablissement'] = "À compléter"
        item['ville'] = "À compléter"
        item['attendus'] = response.css(".blc-attendus ul li::text").getall()
        item['specialites'] = []
        item['taux_admission'] = ""
        item['debouches'] = response.css(".blc-debouches ul li::text").getall()

        yield item
