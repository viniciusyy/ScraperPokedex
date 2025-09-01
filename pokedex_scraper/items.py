import scrapy

class PokemonItem(scrapy.Item):
    number = scrapy.Field()              # e.g., "0001"
    name = scrapy.Field()                # e.g., "Bulbasaur"
    form = scrapy.Field()                # e.g., "Alolan", "Mega X", or None
    url = scrapy.Field()
    types = scrapy.Field()               # list[str] (lowercase)
    height_cm = scrapy.Field()           # float
    weight_kg = scrapy.Field()           # float
    abilities = scrapy.Field()           # list[{"name": str, "url": str}]
    next_evolutions = scrapy.Field()     # list[{"to_number": str, "to_name": str, "to_url": str, "level": int|None, "item": str|None}]
    type_effectiveness = scrapy.Field()  # dict[str, float]  (attacking type -> multiplier)
    scraped_from = scrapy.Field()        # for provenance
    slug = scrapy.Field()                # e.g., "bulbasaur"
    

class AbilityItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    effect = scrapy.Field()              # one-paragraph effect description text
