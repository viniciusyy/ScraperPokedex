import re
import scrapy
from urllib.parse import urljoin
from pokedex_scraper.items import PokemonItem
from pokedex_scraper.utils import parse_float_from_text, absolutize, compute_type_effectiveness, detect_form_from_row_text, to_slug

BASE = "https://pokemondb.net"

class PokedexAllSpider(scrapy.Spider):
    name = "pokedex_all"
    allowed_domains = ["pokemondb.net"]
    start_urls = ["https://pokemondb.net/pokedex/all"]

    custom_settings = {
        "FEED_URI": "data/pokemons_raw.jsonl",
        "FEED_FORMAT": "jsonlines",
    }

    def parse(self, response):
        # Iterate table rows; try robust selectors
        rows = response.css("table#pokedex tbody tr")
        if not rows:
            rows = response.css("table.data-table tbody tr")
        self.logger.info("Found %d rows", len(rows))

        for tr in rows:
            # Skip header-ish or empty rows
            if not tr.css("td"):
                continue

            # Dex number
            number = None
            # common 'cell-num' class or first td text
            number = tr.css("td.cell-num::text").re_first(r"\d{1,4}")
            if not number:
                number = tr.css("td:nth-child(1)::text").re_first(r"\d{1,4}")
            if not number:
                # try data-sort on the first or second cell
                number = tr.css("td::attr(data-sort)").re_first(r"\d{1,4}")

            # Name + URL
            name_a = tr.css("td.cell-name a.ent-name")
            if not name_a:
                name_a = tr.css("td:nth-child(2) a")
            name = name_a.css("::text").get()
            href = name_a.css("::attr(href)").get()
            if not href:
                # skip malformed
                continue
            url = response.urljoin(href)

            # Types
            type_elems = tr.css("td:nth-child(3) a.type-icon::text")
            if not type_elems:
                type_elems = tr.css("td.cell-icon a::text")
            types = [t.strip().lower() for t in type_elems.getall() if t.strip()]

            # Form (if the row mentions Mega/Alolan/etc)
            raw_row_text = " ".join(tr.css("td").xpath("string()").getall())
            form = detect_form_from_row_text(raw_row_text)

            # Prepare request to details page
            base = {
                "number": number,
                "name": name,
                "form": form,
                "url": url,
                "types": types,
                "slug": url.rstrip("/").split("/")[-1],
            }
            yield response.follow(url, callback=self.parse_pokemon_page, cb_kwargs={"base": base})

    def parse_pokemon_page(self, response, base):
        # Height / Weight from Pokédex data table
        height_text = response.xpath('//th[contains(.,"Height")]/following-sibling::td[1]/text()').get()
        weight_text = response.xpath('//th[contains(.,"Weight")]/following-sibling::td[1]/text()').get()
        height_m = parse_float_from_text(height_text or "", "m")
        weight_kg = parse_float_from_text(weight_text or "", "kg")
        height_cm = round(height_m * 100, 1) if height_m is not None else None

        # Abilities: list of (name, url)
        ability_links = response.xpath('//th[contains(.,"Abilities")]/following-sibling::td[1]//a[contains(@href,"/ability/")]')
        abilities = []
        for a in ability_links:
            abilities.append({
                "name": a.xpath("normalize-space(.)").get(),
                "url": response.urljoin(a.xpath("@href").get())
            })

        # Evolution chart: parse immediate next evolutions (one hop)
        next_evolutions = self.parse_next_evolutions(response)

        # Type effectiveness: compute from types (fallback if we can't parse)
        type_effectiveness = { }
        try:
            type_effectiveness = self.compute_effectiveness_from_types(base.get("types") or [])
        except Exception:
            type_effectiveness = {}

        item = PokemonItem(
            number=base["number"],
            name=base["name"],
            form=base.get("form"),
            url=base["url"],
            types=base.get("types") or [],
            height_cm=height_cm,
            weight_kg=weight_kg,
            abilities=abilities,
            next_evolutions=next_evolutions,
            type_effectiveness=type_effectiveness,
            scraped_from=response.url,
            slug=base.get("slug"),
        )
        yield item

    # --- helpers ---
    def compute_effectiveness_from_types(self, types):
        return compute_type_effectiveness(types)

    def parse_next_evolutions(self, response):
        """Return list of dicts with immediate next evolutions, parsing the Evolution chart.
        Extremely defensive to support branching (Eevee) and items/levels.
        """
        evol = []
        # try to locate the evolution container
        container = response.xpath('//h2[normalize-space(.)="Evolution chart"]/following-sibling::*[1]')
        if not container:
            return evol

        # Find all cards in order
        cards = container.xpath('.//div[contains(@class,"infocard")]//a[contains(@href,"/pokedex/") and contains(@class,"ent-name")]')
        # if no cards found, fallback to any name links
        if not cards:
            cards = container.xpath('.//a[contains(@href,"/pokedex/")]')

        # Build list of (name, url, number) in order of appearance
        seq = []
        for a in cards:
            name = a.xpath('normalize-space(.)').get()
            href = a.xpath('@href').get()
            num = a.xpath('../../..//small[contains(.,"#")]/text()').re_first(r'#(\d{3,4})')
            seq.append({"name": name, "url": response.urljoin(href), "number": num})

        # Find current index by matching slug in URLs
        my_slug = response.url.rstrip("/").split("/")[-1]
        idxs = [i for i, c in enumerate(seq) if c["url"].rstrip("/").endswith("/" + my_slug)]
        if not idxs:
            # fallback: match by number & name
            num = response.xpath('//th[contains(.,"National")]/following-sibling::td[1]/text()').re_first(r'(\d{3,4})')
            name = response.xpath('//h1/text()').get() or ""
            idxs = [i for i, c in enumerate(seq) if (c["number"] == num) or (c["name"].lower() == (name or "").strip().lower())]

        if not idxs:
            return evol

        i = idxs[0]

        # Parse triggers between cards: inner text nodes often contain e.g. "(Level 16)", "(use Water Stone)"
        # We'll collect all texts from container and map nearest triggers.
        texts = [t.strip() for t in container.xpath('.//text()').getall() if t.strip()]
        def nearest_trigger(after_name):
            # find the first parenthesized token that appears after this name in texts
            try:
                pos = texts.index(after_name)
            except ValueError:
                return None
            # search next few tokens
            for t in texts[pos+1: pos+15]:
                if t.startswith("(") and t.endswith(")"):
                    return t
            return None

        # immediate next(s): look ahead until the next card that is not the same as current
        # Usually the next card(s) in seq correspond to next stage(s).
        for j in range(i+1, len(seq)):
            # stop if we hit a card of the same stage depth? We don't know stages; so break when we find a card that seems too far.
            # Heuristic: if there is a trigger text nearby for my name leading to that card, accept it; else stop after first batch.
            trig = nearest_trigger(seq[i]["name"])
            if trig is None and (j > i+1):
                break
            edge = {
                "to_number": seq[j]["number"],
                "to_name": seq[j]["name"],
                "to_url": seq[j]["url"],
                "level": None,
                "item": None,
            }
            if trig:
                # parse level and item keywords
                m = re.search(r'Level\s*(\d+)', trig, re.IGNORECASE)
                if m:
                    edge["level"] = int(m.group(1))
                m2 = re.search(r'use\s+([^\)]+)', trig, re.IGNORECASE)
                if m2:
                    edge["item"] = m2.group(1).strip()
            evol.append(edge)
            # If branching, loop may add multiple; then stop when we encounter another trigger for a different name.
            if not trig:
                break

        return evol
