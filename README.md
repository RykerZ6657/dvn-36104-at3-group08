# Is AI capability concentrating in fewer organisations?

36104 Data Visualisation and Narratives, Spring 2026. Assignment 3, Group 08.

An interactive Streamlit data narrative built on Epoch AI's *Notable AI Models* dataset.

## Question and persona

- **Question:** Is AI capability concentrating in fewer organisations?
- **Persona:** A university research director who wants to understand universities' position relative to industry, to inform research partnerships and compute planning.
- **User stories:** to be added (as a …, I want …, so that …).

## Sections

| Section | What it shows | Owner |
|---|---|---|
| Overview | Share of notable models developed by industry, academia and collaborations over time | TBC |
| Concentration | Top five organisations' shares of model counts and recorded training compute | Hao |
| Geography | Countries ranked by notable model counts, and which organisations contribute | TBC |
| Openness | Model release categories across organisation types over time | TBC |

## Data

- `data/raw/notable_ai_models.csv`: Epoch AI, *Notable AI Models*, https://epoch.ai/data/notable_ai_models.csv, licence CC BY 4.0, downloaded 21 Oct 2026. Everyone uses this same file.
- `data/processed/`: files the app reads, each produced by a script in `scripts/`.
- Data dictionary: to be added.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## How we work

1. Don't push to `main`. Create a branch for your section, e.g. `weiran/overview`.
2. Put your page in `sections/<your-section>.py` (keep the `render()` function) and any data processing in `scripts/`.
3. Open a pull request into `main` and ask someone to review it.
4. Record each substantive AI use in the AI provenance matrix (to be added); every member needs at least one row.
