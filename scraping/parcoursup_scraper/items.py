import scrapy

class FormationItem(scrapy.Item):
    nom_formation = scrapy.Field()
    etablissement = scrapy.Field()
    ville = scrapy.Field()
    attendus = scrapy.Field()
    specialites = scrapy.Field()
    taux_admission = scrapy.Field()
    debouches = scrapy.Field()
