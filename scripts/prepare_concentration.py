"""Build the processed files for the Concentration section.

Source: data/raw/notable_ai_models.csv
    Epoch AI, "Notable AI Models", https://epoch.ai/data/notable_ai_models.csv
    Licence: CC BY 4.0. Downloaded 21 Oct 2026 (latest publication date in file: 2026-09-30).

Outputs (data/processed/):
    concentration_org_credit.csv  one row per model x organisation, with fractional credit
    concentration_by_year.csv     one row per year: top-5 shares of models and of recorded compute

Run from the project root:  python scripts/prepare_concentration.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "notable_ai_models.csv"
OUT = ROOT / "data" / "processed"

FIRST_YEAR, LAST_YEAR = 2015, 2025  # 2026 is a partial year, so it is left out
TOP_N = 5

# Labs that belong to the same parent company are merged, otherwise one company
# (e.g. Alphabet) is split across five names and its share is understated.
# Listed explicitly rather than by substring, so "MetaMind Inc" or "MIT-IBM Watson AI Lab" are not swept in.
PARENT = {
    "Google": "Google (Alphabet)",
    "Google AI": "Google (Alphabet)",
    "Google Brain": "Google (Alphabet)",
    "Google Cloud": "Google (Alphabet)",
    "Google Research": "Google (Alphabet)",
    "Google DeepMind": "Google (Alphabet)",
    "DeepMind": "Google (Alphabet)",
    "Meta AI": "Meta",
    "Facebook": "Meta",
    "Facebook AI": "Meta",
    "Facebook AI Research": "Meta",
    "Microsoft": "Microsoft",
    "Microsoft Research": "Microsoft",
    "Microsoft Research Asia": "Microsoft",
    "Alibaba": "Alibaba",
    "Alibaba DAMO Academy": "Alibaba",
    "Huawei": "Huawei",
    "Huawei Noah's Ark Lab": "Huawei",
    "Samsung": "Samsung",
    "Samsung R&D Institute Russia": "Samsung",
}


def load_models() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    df["year"] = pd.to_datetime(df["Publication date"]).dt.year
    df = df[df["year"].between(FIRST_YEAR, LAST_YEAR)]
    df = df.dropna(subset=["Organization"])
    return df[["Model", "Organization", "year", "Training compute (FLOP)"]].rename(
        columns={"Training compute (FLOP)": "compute_flop"}
    )


def credit_per_org(models: pd.DataFrame) -> pd.DataFrame:
    """Split each model equally between the organisations that built it."""
    rows = models.assign(org_raw=models["Organization"].str.split(",")).explode("org_raw")
    rows["org_raw"] = rows["org_raw"].str.strip()
    rows["org"] = rows["org_raw"].map(PARENT).fillna(rows["org_raw"])
    # After merging, a Google Brain + DeepMind paper is one organisation, not two
    rows = rows.drop_duplicates(["Model", "year", "org"])
    n_orgs = rows.groupby(["Model", "year"])["org"].transform("size")
    rows["model_credit"] = 1 / n_orgs
    rows["compute_credit_flop"] = rows["compute_flop"] / n_orgs
    return rows[["Model", "year", "org_raw", "org", "model_credit", "compute_flop", "compute_credit_flop"]]


def top_share(credit: pd.DataFrame, column: str) -> pd.DataFrame:
    totals = credit.groupby(["year", "org"])[column].sum().reset_index()
    totals = totals[totals[column] > 0]
    totals["rank"] = totals.groupby("year")[column].rank(ascending=False, method="first")
    top = totals[totals["rank"] <= TOP_N]
    return pd.DataFrame({
        "top_sum": top.groupby("year")[column].sum(),
        "all_sum": totals.groupby("year")[column].sum(),
        "top_orgs": top.sort_values("rank").groupby("year")["org"].agg("; ".join),
        "n_orgs": totals.groupby("year")["org"].nunique(),
    })


def main() -> None:
    models = load_models()
    credit = credit_per_org(models)

    by_models = top_share(credit, "model_credit")
    by_compute = top_share(credit, "compute_credit_flop")
    coverage = models.groupby("year").agg(
        models=("Model", "size"),
        models_with_compute=("compute_flop", "count"),
    )

    by_year = pd.DataFrame({
        "models": coverage["models"],
        "models_with_compute": coverage["models_with_compute"],
        "compute_coverage_pct": 100 * coverage["models_with_compute"] / coverage["models"],
        "organisations": by_models["n_orgs"],
        "top5_model_share_pct": 100 * by_models["top_sum"] / by_models["all_sum"],
        "top5_compute_share_pct": 100 * by_compute["top_sum"] / by_compute["all_sum"],
        "top5_by_models": by_models["top_orgs"],
        "top5_by_compute": by_compute["top_orgs"],
    }).reset_index().rename(columns={"index": "year"})

    OUT.mkdir(parents=True, exist_ok=True)
    credit.to_csv(OUT / "concentration_org_credit.csv", index=False)
    by_year.round(1).to_csv(OUT / "concentration_by_year.csv", index=False)
    print(by_year.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
