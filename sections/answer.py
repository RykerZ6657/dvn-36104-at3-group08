"""The app's overall answer to the question, shown above the tabs.

Every number is read from the processed files, so the text cannot drift from the charts.
Call render() from the main app.
"""

import streamlit as st

from sections import concentration, openness


def render() -> None:
    by_year = concentration.load()[0].set_index("year")
    models = openness.load()
    first, last = int(by_year.index.min()), int(by_year.index.max())
    industry = (models["org_type"] == "Industry").groupby(models["year"]).mean() * 100
    first_models = int((models["year"] == first).sum())
    recent = last - 2

    st.markdown(
        f"**Short answer: concentrated throughout, with no clear long-run rise, but the last two years point towards "
        f"more concentration.** From {first} to {last}, the top five organisations held on average "
        f"**{by_year['top5_model_share_pct'].mean():.0f}%** of notable models and "
        f"**{by_year['top5_compute_share_pct'].mean():.0f}%** of recorded training compute, and neither share rises steadily. "
        f"Since {recent}, however, the number of organisations credited has fallen from "
        f"{by_year.loc[recent, 'organisations']} to {by_year.loc[last, 'organisations']}, while the top five's share of models "
        f"has risen from {by_year.loc[recent, 'top5_model_share_pct']:.0f}% to {by_year.loc[last, 'top5_model_share_pct']:.0f}%. "
        f"Two years is too short to call a trend, and recent years may be less complete. The clearer shift is between "
        f"sectors: industry built {industry.loc[first]:.0f}% of notable models in {first} and {industry.loc[last]:.0f}% in {last}, "
        f"though {first} has only {first_models} models."
    )
    st.markdown(
        "**What the data cannot show:** these are shares of notable models and of recorded compute, not of capability. "
        f"Training compute is recorded for only {by_year.loc[last, 'compute_coverage_pct']:.0f}% of {last} models."
    )
