import json, os, re
import pandas as pd

RAW_POK = "data/pokemons_raw.jsonl"
RAW_ABI = "data/abilities_raw.jsonl"
OUT_POK = "data/pokemons_clean.jsonl"
OUT_ABI = "data/abilities_clean.jsonl"

def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def main():
    pok = pd.DataFrame(load_jsonl(RAW_POK))
    abi = pd.DataFrame(load_jsonl(RAW_ABI))

    # --- basic cleaning ---
    # drop rows missing number or name
    pok = pok.dropna(subset=["number","name"])

    # normalize numeric fields
    for col in ["height_cm", "weight_kg"]:
        pok[col] = pd.to_numeric(pok[col], errors="coerce")

    # lowercase types and ensure list
    def norm_types(x):
        if isinstance(x, list):
            return [str(t).strip().lower() for t in x if str(t).strip()]
        if pd.isna(x):
            return []
        return [str(x).strip().lower()]
    pok["types"] = pok["types"].apply(norm_types)

    # Deduplicate by (number, form)
    pok["form"] = pok["form"].fillna("")
    pok = pok.sort_values(["number","form","name"]).drop_duplicates(subset=["number","form"], keep="first")

    # Remove obviously invalid heights/weights (<=0 or crazy values)
    pok.loc[(pok["height_cm"] <= 0) | (pok["height_cm"] > 2000), "height_cm"] = pd.NA
    pok.loc[(pok["weight_kg"] <= 0) | (pok["weight_kg"] > 10000), "weight_kg"] = pd.NA

    # Save cleaned
    with open(OUT_POK, "w", encoding="utf-8") as f:
        for _, row in pok.iterrows():
            f.write(json.dumps(row.dropna().to_dict(), ensure_ascii=False) + "\n")

    # Abilities cleaning
    if not abi.empty:
        abi = abi.dropna(subset=["name","url"]).drop_duplicates(subset=["url"], keep="first")
        with open(OUT_ABI, "w", encoding="utf-8") as f:
            for _, row in abi.iterrows():
                f.write(json.dumps(row.dropna().to_dict(), ensure_ascii=False) + "\n")

    print("Wrote:", OUT_POK, OUT_ABI)

if __name__ == "__main__":
    main()
