BOT_NAME = "pokedex_scraper"

SPIDER_MODULES = ["pokedex_scraper.spiders"]
NEWSPIDER_MODULE = "pokedex_scraper.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5

# politeness
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5.0

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PokédexScraper/1.0; +https://example.local)"
}

FEEDS = {
    "data/pokemons_raw.jsonl": {"format": "jsonlines", "overwrite": True},
    "data/abilities_raw.jsonl": {"format": "jsonlines", "overwrite": True},
}
