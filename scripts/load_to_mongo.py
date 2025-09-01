import json, os, sys
from pymongo import MongoClient

POK = "data/pokemons_clean.jsonl"
ABI = "data/abilities_clean.jsonl"

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            yield json.loads(line)

def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["pokedex"]

    # upsert pokemons
    db.pokemon.create_index("number")
    db.pokemon.create_index([("number", 1), ("form", 1)], unique=True)
    pok_count = 0
    for doc in load_jsonl(POK):
        db.pokemon.update_one({"number": doc.get("number"), "form": doc.get("form","")}, {"$set": doc}, upsert=True)
        pok_count += 1

    # abilities
    db.ability.create_index("url", unique=True)
    abi_count = 0
    if os.path.exists(ABI):
        for doc in load_jsonl(ABI):
            db.ability.update_one({"url": doc["url"]}, {"$set": doc}, upsert=True)
            abi_count += 1

    print(f"Loaded {pok_count} pokemons and {abi_count} abilities into MongoDB ({db.name}).")

if __name__ == "__main__":
    main()
