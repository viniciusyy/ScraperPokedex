import scrapy
from pokedex_scraper.items import AbilityItem

class AbilitySpider(scrapy.Spider):
    name = "abilities"
    allowed_domains = ["pokemondb.net"]
    start_urls = ["https://pokemondb.net/ability"]

    custom_settings = {
        "FEED_URI": "data/abilities_raw.jsonl",
        "FEED_FORMAT": "jsonlines",
    }

    def parse(self, response):
        # crawl all ability links from the listing
        for a in response.css('a[href^="/ability/"]'):
            href = a.attrib.get("href")
            # skip menu duplicates by ensuring it's in main content list
            if href and href.count("/") == 2:  # '/ability/overgrow'
                yield response.follow(href, callback=self.parse_ability)

    def parse_ability(self, response):
        name = response.css("h1::text").get().strip()
        # Effect paragraph under the 'Effect' section
        effect = response.xpath('//h2[normalize-space(.)="Effect"]/following-sibling::p[1]/text()').get()
        yield AbilityItem(name=name, url=response.url, effect=(effect or "").strip())
