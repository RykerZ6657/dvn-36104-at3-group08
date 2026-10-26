"""Build the processed file for the Openness section.

Source: data/raw/notable_ai_models.csv
    Epoch AI, "Notable AI Models", https://epoch.ai/data/notable_ai_models.csv
    Licence: CC BY 4.0. Downloaded 21 Oct 2026 (latest publication date in file: 2026-09-30).

Output (data/processed/):
    openness_models.csv  one row per model: year, organisation type, release category

Run from the project root:  python scripts/prepare_openness.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "notable_ai_models.csv"
OUT = ROOT / "data" / "processed"

FIRST_YEAR, LAST_YEAR = 2015, 2025  # 2026 is a partial year, so it is left out

# Epoch's seven accessibility values grouped into the distinctions the persona cares about:
# can a university download and run the weights, only call them through a service, or not use them at all.
RELEASE = {
    "Open weights (unrestricted)": "Open weights",
    "Open weights (non-commercial)": "Open weights",
    "Open weights (restricted use)": "Open weights",
    "API access": "API or hosted access",
    "Hosted access (no API)": "API or hosted access",
    "Unreleased": "Unreleased",
}
NOT_RECORDED = "Not recorded"


def organisation_type(categories: str) -> str:
    """Collapse Epoch's per-organisation list (e.g. "Industry,Academia") to one label per model."""
    if pd.isna(categories):
        return "Not recorded"
    kinds = {c.strip() for c in categories.split(",")}
    if kinds == {"Industry"}:
        return "Industry"
    if kinds == {"Academia"}:
        return "Academia"
    if {"Industry", "Academia"} <= kinds:
        return "Industry–academia collaboration"
    return "Other (government, research collectives)"


def main() -> None:
    df = pd.read_csv(RAW)
    df["year"] = pd.to_datetime(df["Publication date"]).dt.year
    df = df[df["year"].between(FIRST_YEAR, LAST_YEAR)]

    models = pd.DataFrame({
        "Model": df["Model"],
        "Organization": df["Organization"],
        "year": df["year"],
        "accessibility_raw": df["Model accessibility"],
        "release": df["Model accessibility"].map(RELEASE).fillna(NOT_RECORDED),
        "org_type": df["Organization categorization"].map(organisation_type),
    })

    OUT.mkdir(parents=True, exist_ok=True)
    models.to_csv(OUT / "openness_models.csv", index=False)
    print(pd.crosstab(models["year"], models["release"]).to_string())
    print()
    print(pd.crosstab(models["org_type"], models["release"]).to_string())


if __name__ == "__main__":
    main()
