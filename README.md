# Pokédex Scraper (Scrapy + Pandas + MongoDB)

Este projeto coleta dados do Pokédex do site **pokemondb.net** e produz JSONs limpos com:
- Número, URL, nome, tipos
- Tamanho (cm) e peso (kg)
- Habilidades (nome + URL; descrição via spider separado)
- Próximas evoluções (número, nome, URL, level se houver e item se houver)
- Efetividade de cada tipo **sobre** o Pokémon (tabela de multiplicadores por tipo atacante)


## Estrutura

```
pokedex_scraper/
  pokedex_scraper/
    __init__.py
    items.py
    settings.py
    utils.py
    spiders/
      pokedex_all.py
      ability_spider.py
  scripts/
    process_data.py
    load_to_mongo.py
    run_queries.py
  data/
    (saídas .jsonl)
  scrapy.cfg
  requirements.txt
```

## Configurar ambiente

Crie e ative um venv, depois instale dependências:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

> Se tiver erro de instalação do Scrapy no macOS, instale antes:
> `pip install wheel` e `xcode-select --install` (caso falte build tools).

## Rodar spiders

1) **Pokémons (detalhes):**
```bash
scrapy runspider pokedex_scraper/spiders/pokedex_all.py -s LOG_LEVEL=INFO
```
Gera: `data/pokemons_raw.jsonl`

2) **Habilidades (efeitos):**
```bash
scrapy runspider pokedex_scraper/spiders/ability_spider.py -s LOG_LEVEL=INFO
```
Gera: `data/abilities_raw.jsonl`

> Você pode rodar em momentos distintos; os JSONs são independentes.

## Limpeza/Transformação (Pandas)

```bash
python pokedex_scraper/scripts/process_data.py
```
Gera `data/pokemons_clean.jsonl` (e `abilities_clean.jsonl` se existir input).  
- Remove nulos/ inválidos
- Normaliza tipos para minúsculo
- Deduplica por `(number, form)`

## Carregar no MongoDB

Defina `MONGO_URI` (ou use o padrão `mongodb://localhost:27017`):

```bash
export MONGO_URI="mongodb://localhost:27017"
python pokedex_scraper/scripts/load_to_mongo.py
```

## Consultas pedidas

```bash
python pokedex_scraper/scripts/run_queries.py
```

- **Quantos Pokémons são de 2 tipos ou mais?**  
  Conta `types.1` existente em `pokemon`.

- **Quais Pokémons do tipo água são evoluções que ocorrem depois do Level 30?**  
  O script varre as arestas `next_evolutions` com `level > 30` e lista os Pokémons alvo (água).

## Observações sobre casos complexos (Eevee, regionais, Mega etc.)

- O spider tenta inferir `form` a partir do texto da linha da listagem (ex.: *Alolan*, *Mega*, *Hisuian*).  
- As evoluções são extraídas da seção **Evolution chart** na página do Pokémon com heurísticas robustas:
  - Suporta ramificações (como Eevee) buscando os cartões da cadeia e os gatilhos em parênteses (ex. `(Level 36)`, `(use Water Stone)`).
  - Para cada Pokémon, salva **apenas as evoluções imediatas (um passo)** com `level` (int) quando tiver e `item` (str) quando aplicável.
- A efetividade por tipo é calculada via uma matriz estática (dual-type multiplicando fatores), o que evita depender do HTML dessa seção — o resultado é o mesmo em condições base (sem habilidades/itens).

## Requisitos

```
Scrapy>=2.11
pandas>=2.0
pymongo>=4.6
python-dotenv>=1.0
```
