# AI provenance matrix

One row per substantive use of AI in this project. Every member owns at least one row.
The verification column names a check that could have failed: if the AI output had been wrong, the check would have shown it.

| # | Artefact | Who | Tool | What was asked | What came back | How it was verified | Outcome |
|---|---|---|---|---|---|---|---|
| 1 | `scripts/prepare_concentration.py`, `sections/concentration.py` | Hao | Claude Code (Anthropic) | Build the Concentration section: the top five organisations' yearly share of notable models and of recorded training compute, with labs merged into parent companies | Processing script, Streamlit section with a line chart, a top-5 ranking chart and a trace panel | Recomputed the 2025 compute share of xAI directly from the raw CSV (Grok 4 and Grok 3 compute ÷ all recorded 2025 compute = 56.8%) and compared it with the app; checked the parent-company table lists names exactly so "MetaMind Inc" is not merged into Meta | Kept. Chart labels changed from whole numbers to one decimal place after 99.9% displayed as 100% |
| 2 | `scripts/prepare_openness.py`, `sections/openness.py` | Hao | Claude Code (Anthropic) | Build the Openness section: release type of notable models by year and by organisation type | Processing script, Streamlit section with two 100% stacked bar charts and a trace panel | Filtered the raw CSV for 2025 by hand: 55 of 107 models are API or hosted access (51.4%), matching the app. Checked the release-type coverage per year and found 2015 was mostly "not recorded" | Modified. The summary sentence was changed to compare only years with at least 90% of release types recorded, so 2015 is no longer the baseline |
| 3 | Review of pull request #3 (Geography) | Hao | Claude Code (Anthropic) | Review the Geography pull request against the Concentration method | Review noting that Geography counted Google, DeepMind and other Alphabet labs separately | After Weiran's fix, checked the US organisation ranking shows one "Google (Alphabet)" entry (149 models) and no separate DeepMind or Google Brain entries | Change requested, fixed by Weiran, then merged |
| 4 | `README.md` user stories, `data/DATA_DICTIONARY.md`, this file, `DISCLOSURE.md` | Hao | Claude Code (Anthropic) | Draft the user stories, data dictionary, provenance matrix and disclosure statement from the repository | Draft documents | Re-ran both processing scripts and confirmed `git status` showed no change to the committed processed files; checked each stated primary key for duplicates (none); recomputed row counts and missing-value counts from the CSVs | Kept after review by Hao |
| 5 | *Geography section* | Weiran | | | | | *To be completed by Weiran* |
| 6 | *Overview section* | Kylie | | | | | *To be completed by Kylie* |

Add more rows as needed, for example for the recording script or any other AI-assisted writing or code.
