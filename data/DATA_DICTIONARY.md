# Data dictionary

Every dataset the app reads, where it comes from, what each column means and how it was produced.
All processed files are rebuilt from the raw file by the scripts in `scripts/`; running them again reproduces the committed files exactly.

| Dataset | File | Rows | Primary key | Built by | Used by |
|---|---|---|---|---|---|
| Notable AI Models (source) | `data/raw/notable_ai_models.csv` | 1,078 | `Model` | Downloaded from Epoch AI | All sections |
| Organisation credit | `data/processed/concentration_org_credit.csv` | 1,202 | `Model`, `org` | `scripts/prepare_concentration.py` | Concentration |
| Concentration by year | `data/processed/concentration_by_year.csv` | 11 | `year` | `scripts/prepare_concentration.py` | Concentration |
| Openness by model | `data/processed/openness_models.csv` | 782 | `Model` | `scripts/prepare_openness.py` | Openness |
| Country and organisation attributions | built in memory, not saved | 962 / 1,134 | see below | `scripts/geography_processing.py` | Geography |

---

## 1. Notable AI Models (source)

- **File:** `data/raw/notable_ai_models.csv`
- **Publisher:** Epoch AI
- **Title:** Notable AI Models
- **URL:** https://epoch.ai/data/notable_ai_models.csv (documentation: https://epoch.ai/data/notable-ai-models)
- **Licence:** Creative Commons Attribution 4.0 (CC BY 4.0)
- **Retrieved:** 21 Oct 2026. The full file is committed; it is small enough to serve as its own source sample.
- **Primary key:** `Model` (no duplicates in the file)
- **Time coverage of the file:** 1950-07-02 to 2026-09-30 (`Publication date`)
- **Time coverage used in the app:** 2015-01-01 to 2025-12-31 (782 models). 2026 is excluded as a partial year.
- **Latest observation used:** 2025-12-31

The file has 47 columns. The app uses the seven below; the others are kept unchanged so the file matches the source.

| Column | Type | Unit / values | Missing in 2015–2025 | Meaning |
|---|---|---|---|---|
| `Model` | text | name | 0 | Model name, unique per row |
| `Organization` | text | comma-separated list | 1 | Organisations credited with the model |
| `Publication date` | date | YYYY-MM-DD | 0 | Date the model or paper was published |
| `Training compute (FLOP)` | number | floating-point operations | 367 | Total compute used to train the model, as estimated by Epoch AI |
| `Organization categorization` | text | comma-separated list of Industry, Academia, Government, Research collective | 2 | Type of each credited organisation |
| `Country (of organization)` | text | comma-separated list of countries | 1 | Country of each credited organisation, in the same order as `Organization` where both are complete |
| `Model accessibility` | text | Open weights (unrestricted / non-commercial / restricted use), API access, Hosted access (no API), Unreleased, Limited access | 69 | How the model was released |

---

## 2. Organisation credit

- **File:** `data/processed/concentration_org_credit.csv`
- **Primary key:** `Model`, `org`
- **Time coverage:** 2015–2025 (781 models; the one model with no organisation is dropped)
- **Latest observation:** 2025

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `Model` | text | | Model name, from the source |
| `year` | integer | calendar year | Year of `Publication date` |
| `org_raw` | text | | One organisation name exactly as listed in the source |
| `org` | text | | Organisation after merging labs into their parent company (e.g. DeepMind → Google (Alphabet)) |
| `model_credit` | number | models (0–1) | Share of the model credited to this organisation: 1 ÷ number of distinct organisations on the model |
| `compute_flop` | number | FLOP | The model's total training compute, from the source; empty if not recorded |
| `compute_credit_flop` | number | FLOP | `compute_flop` × `model_credit` |

**Transform (`scripts/prepare_concentration.py`):**
1. Keep models published 2015–2025 with an organisation listed.
2. Split `Organization` on commas, one row per organisation.
3. Map labs to parent companies with the explicit `PARENT` table in the script (Google, Meta, Microsoft, Alibaba, Huawei and Samsung labs). Names are matched exactly, not by substring.
4. Drop duplicate parent organisations on the same model, then split credit equally between the remaining organisations.

## 3. Concentration by year

- **File:** `data/processed/concentration_by_year.csv`
- **Primary key:** `year`
- **Time coverage:** 2015–2025 (11 rows)
- **Latest observation:** 2025

| Column | Type | Unit | Meaning |
|---|---|---|---|
| `year` | integer | calendar year | Publication year |
| `models` | integer | models | Notable models published that year (with an organisation listed) |
| `models_with_compute` | integer | models | Of those, models with a recorded training compute |
| `compute_coverage_pct` | number | % | `models_with_compute` ÷ `models` × 100 |
| `organisations` | integer | organisations | Distinct organisations (after parent merging) credited that year |
| `top5_model_share_pct` | number | % of model credit | Share of the year's model credit held by the five organisations with the most credit |
| `top5_compute_share_pct` | number | % of recorded compute | Share of the year's recorded training compute held by the five organisations with the most compute |
| `top5_by_models` | text | `; `-separated list | The five organisations behind `top5_model_share_pct`, largest first |
| `top5_by_compute` | text | `; `-separated list | The five organisations behind `top5_compute_share_pct`, largest first |

**Transform:** sum `model_credit` and `compute_credit_flop` from the organisation credit file by year and organisation, rank organisations within each year, and divide the top five's total by the year's total. Percentages are rounded to one decimal place. Compute shares cover only models with recorded compute (415 of 782 models in 2015–2025).

## 4. Openness by model

- **File:** `data/processed/openness_models.csv`
- **Primary key:** `Model`
- **Time coverage:** 2015–2025 (782 models)
- **Latest observation:** 2025

| Column | Type | Unit / values | Meaning |
|---|---|---|---|
| `Model` | text | | Model name, from the source |
| `Organization` | text | | Organisations, unchanged from the source |
| `year` | integer | calendar year | Year of `Publication date` |
| `accessibility_raw` | text | | `Model accessibility` unchanged from the source |
| `release` | text | Open weights, API or hosted access, Unreleased, Not recorded | Grouped release type (see transform) |
| `org_type` | text | Industry, Academia, Industry–academia collaboration, Other (government, research collectives), Not recorded | One organisation type per model (see transform) |

**Transform (`scripts/prepare_openness.py`):**
- `release`: the three *Open weights* values → Open weights; *API access* and *Hosted access (no API)* → API or hosted access; *Unreleased* → Unreleased; empty → Not recorded. *Limited access* does not occur in 2015–2025.
- `org_type`: only Industry → Industry; only Academia → Academia; both Industry and Academia → Industry–academia collaboration; any other mix → Other; empty → Not recorded.

Counts, 2015–2025: Open weights 310, Unreleased 255, API or hosted access 148, Not recorded 69.

## 5. Country and organisation attributions (Geography)

These tables are built in memory each time the Geography tab loads, by `flatten_attributions()` in `scripts/geography_processing.py`, and are not saved to `data/processed/`. They are rebuilt from the raw file every time, so they always match it.

**Country table** (962 rows, 33 countries). Primary key: `CSV row`, `Country`.

| Column | Type | Meaning |
|---|---|---|
| `Model` | text | Model name, from the source |
| `Year` | integer | Year of `Publication date` (2015–2025) |
| `CSV row` | integer | Row number of the model in the raw CSV, counting the header as row 1, so any number can be traced back |
| `Country` | text | One country from `Country (of organization)`; a model with several countries appears once per country |

**Organisation table** (1,134 rows). Primary key: `CSV row`, `Country`, `Organisation`. Same columns plus:

| Column | Type | Meaning |
|---|---|---|
| `Organisation` | text | Organisation paired with `Country`, after the same parent-company merging as Concentration |

**Transform:** split `Country (of organization)` and `Organization` on commas. Countries are de-duplicated within each model. Organisations are paired with countries by position only when both lists have the same length; models where the lengths differ are left out of the organisation table rather than guessed.
