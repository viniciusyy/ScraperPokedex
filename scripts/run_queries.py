from pymongo import MongoClient
import os

def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["pokedex"]

    # 1) Quantos Pokemons são de 2 tipos ou mais?
    count_dual = db.pokemon.count_documents({"types.1": {"$exists": True}})
    print(f"Pokémons com 2 tipos ou mais: {count_dual}")

    # 2) Quais Pokemons do tipo água são evoluções que ocorrem depois do Level 30?
    # Construir um conjunto com todos os 'to_number' onde a evolução tem level > 30
    evolved_after_30 = set()
    cursor = db.pokemon.find({}, {"next_evolutions": 1})
    for doc in cursor:
        for e in (doc.get("next_evolutions") or []):
            lvl = e.get("level")
            if isinstance(lvl, int) and lvl > 30:
                if e.get("to_number"):
                    evolved_after_30.add(e["to_number"])

    # Buscar pokémons de água cujo 'number' está nesse conjunto
    results = list(db.pokemon.find({"number": {"$in": list(evolved_after_30)}, "types": "water"}, {"_id":0, "number":1, "name":1, "types":1}))
    print("Pokémons do tipo água que são evoluções com Level > 30:")
    for r in results:
        print(f" - #{r['number']} {r['name']} ({', '.join(r.get('types', []))})")

if __name__ == "__main__":
    main()
