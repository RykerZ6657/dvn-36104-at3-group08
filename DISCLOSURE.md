# Data and AI disclosure statement

## Data

All data in this app comes from one public source: Epoch AI, *Notable AI Models*, https://epoch.ai/data/notable_ai_models.csv, downloaded on 21 October 2026 and released under a Creative Commons Attribution 4.0 licence. The unmodified file is committed in `data/raw/`, and every processed file the app reads is produced from it by the scripts in `scripts/`, as documented in `data/DATA_DICTIONARY.md`.

The app shows models published from 2015 to 2025. It covers only models that meet Epoch AI's notability criteria, so it describes notable models, not all AI development. Some fields are incomplete, most importantly training compute (recorded for 415 of 782 models) and release type (missing for 69 models, mostly from 2015–2017). Each section states how it handles these gaps.

The dataset lists paper authors, but the app does not use or display any personal information.

## AI

Group members used generative AI tools during this project. Each substantive use is recorded in `AI_PROVENANCE.md`, with what was asked, what came back, how it was checked and what was kept.

AI tools were used to help write data processing and Streamlit code, review pull requests and draft documentation. AI was not used as a source of data: every number shown in the app is computed from the Epoch AI file by the committed scripts, and the numbers quoted in the provenance matrix were checked against that file.

The group takes responsibility for all submitted work, including any part produced with AI help.
