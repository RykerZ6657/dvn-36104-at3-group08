# Is AI capability concentrating in fewer organisations?

36104 Data Visualisation and Narratives, Spring 2026. Assignment 3, Group 08.

An interactive Streamlit data narrative built on Epoch AI's *Notable AI Models* dataset.

## Question and persona

- **Question:** Is AI capability concentrating in fewer organisations?
- **Persona:** A university research director who wants to understand universities' position relative to industry, to inform research partnerships and compute planning.

### User stories

1. **As a** university research director, **I want** to see what share of notable models and of recorded training compute the five leading organisations hold each year, **so that** I can judge whether frontier-scale training is something our university could match or would need partners for.
   *In the app:* Concentration tab. Read the top-5 share line chart, then pick a year and measure to see who the top five are.
2. **As a** university research director, **I want** to see which countries produce the most notable models and which organisations lead in each, **so that** I can identify where potential international research partners are based.
   *In the app:* Geography tab. Set the year range and ranking size, then select a country to see its leading organisations.
3. **As a** university research director, **I want** to see whether notable models are released as open weights, through an API only, or not at all, by year and by type of organisation, **so that** I can plan whether our researchers can rely on downloadable models or need budget for paid access.
   *In the app:* Openness tab. Read the release-type chart by year, then the comparison by organisation type.

## Sections

| Section | What it shows | Owner |
|---|---|---|
| Overview | Share of notable models developed by industry, academia and collaborations over time | Kylie |
| Concentration | Top five organisations' shares of model counts and recorded training compute | Hao |
| Geography | Countries ranked by notable model counts, and which organisations contribute | Weiran |
| Openness | Model release categories across organisation types over time | Hao |

## Data

- `data/raw/notable_ai_models.csv`: Epoch AI, *Notable AI Models*, https://epoch.ai/data/notable_ai_models.csv, licence CC BY 4.0, downloaded 21 Oct 2026. Everyone uses this same file.
- `data/processed/`: files the app reads, each produced by a script in `scripts/`.
- Data dictionary: [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md) (source, licence, columns and units, keys, coverage and transform for every dataset).

To regenerate the processed files from the raw file:

```bash
python scripts/prepare_concentration.py
python scripts/prepare_openness.py
```

## AI use and disclosure

- AI provenance matrix: [`AI_PROVENANCE.md`](AI_PROVENANCE.md). Every member owns at least one row.
- Data and AI disclosure statement: [`DISCLOSURE.md`](DISCLOSURE.md).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How we work

1. Don't push to `main`. Create a branch for your section, e.g. `weiran/overview`.
2. Put your page in `sections/<your-section>.py` (keep the `render()` function) and any data processing in `scripts/`.
3. Open a pull request into `main` and ask someone to review it.
4. Record each substantive AI use in [`AI_PROVENANCE.md`](AI_PROVENANCE.md); every member needs at least one row.
