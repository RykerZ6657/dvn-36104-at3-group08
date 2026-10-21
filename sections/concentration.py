"""Section 2: Concentration. Are fewer organisations dominating?

Reads the processed files made by scripts/prepare_concentration.py.
Call render() from the main app.
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"

# Okabe-Ito colours: distinguishable with the common colour vision deficiencies
MODELS_COLOUR = "#0072B2"
COMPUTE_COLOUR = "#E69F00"

METRICS = {
    "Recorded training compute": ("compute_credit_flop", COMPUTE_COLOUR),
    "Number of notable models": ("model_credit", MODELS_COLOUR),
}


@st.cache_data
def load():
    by_year = pd.read_csv(DATA / "concentration_by_year.csv")
    credit = pd.read_csv(DATA / "concentration_org_credit.csv")
    return by_year, credit


def trend_chart(by_year: pd.DataFrame) -> alt.Chart:
    long = by_year.melt(
        id_vars="year",
        value_vars=["top5_model_share_pct", "top5_compute_share_pct"],
        var_name="measure",
        value_name="share",
    )
    long["measure"] = long["measure"].map({
        "top5_model_share_pct": "Share of notable models",
        "top5_compute_share_pct": "Share of recorded training compute",
    })
    colour = alt.Color(
        "measure:N",
        scale=alt.Scale(
            domain=["Share of recorded training compute", "Share of notable models"],
            range=[COMPUTE_COLOUR, MODELS_COLOUR],
        ),
        legend=alt.Legend(title=None, orient="top", labelLimit=300),
    )
    base = alt.Chart(long).encode(
        x=alt.X("year:O", title="Publication year", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("share:Q", title="Top 5 organisations' share (%)", scale=alt.Scale(domain=[0, 100])),
        color=colour,
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("measure:N", title="Measure"),
            alt.Tooltip("share:Q", title="Share (%)", format=".1f"),
        ],
    )
    lines = base.mark_line(point=True, strokeWidth=3)
    # Values printed on the chart so nothing depends on hovering
    # One decimal, so 99.9% is not shown as a misleading 100%
    labels = base.mark_text(dy=-10, fontSize=10).encode(text=alt.Text("share:Q", format=".1f"))
    return (lines + labels).properties(height=360)


def ranking_chart(top: pd.DataFrame, colour: str) -> alt.Chart:
    bars = alt.Chart(top).mark_bar(color=colour).encode(
        x=alt.X("share:Q", title="Share of the year's total (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("org:N", sort="-x", title=None, axis=alt.Axis(labelLimit=260)),
        tooltip=[alt.Tooltip("org:N", title="Organisation"), alt.Tooltip("share:Q", title="Share (%)", format=".1f")],
    )
    labels = bars.mark_text(align="left", dx=4, color="currentColor").encode(text=alt.Text("share:Q", format=".1f"))
    return (bars + labels).properties(height=40 * len(top) + 20)


def render() -> None:
    by_year, credit = load()

    st.header("Concentration: are fewer organisations dominating?")
    st.markdown(
        "Each year, how much of the field do the five biggest organisations account for? "
        "We measure it two ways: their share of **notable models released**, and their share of "
        "**recorded training compute** (the total computation used to train those models)."
    )

    first, last = int(by_year["year"].min()), int(by_year["year"].max())
    start, end = st.slider("Years shown", first, last, (first, last), key="conc_years")
    shown = by_year[by_year["year"].between(start, end)]
    if shown.empty:
        st.info("No years in this range. Widen the year range to see the trend.")
        return

    st.subheader("Top 5 share over time")
    st.altair_chart(trend_chart(shown), use_container_width=True)

    model_avg = shown["top5_model_share_pct"].mean()
    compute_avg = shown["top5_compute_share_pct"].mean()
    st.markdown(
        f"**What this shows:** from {start} to {end}, the top five organisations released on average "
        f"**{model_avg:.0f}%** of notable models but accounted for **{compute_avg:.0f}%** of recorded training compute. "
        "Model output is spread across many organisations; the compute behind the largest models is not. "
        "Neither line rises steadily, so the data supports *persistently high* concentration of compute "
        "rather than a clear trend towards *more* concentration."
    )

    st.subheader("Who are the top five?")
    left, right = st.columns([1, 2])
    with left:
        year = st.selectbox("Year", list(range(end, start - 1, -1)), key="conc_year")
        metric = st.radio("Measure", list(METRICS), key="conc_metric")
    column, colour = METRICS[metric]

    year_credit = credit[credit["year"] == year]
    totals = year_credit.groupby("org")[column].sum()
    totals = totals[totals > 0]
    with right:
        if totals.empty:
            st.info(f"No {metric.lower()} recorded for {year}. Try another year or measure.")
        else:
            top = (100 * totals / totals.sum()).sort_values(ascending=False).head(5)
            top = top.rename("share").rename_axis("org").reset_index()
            st.altair_chart(ranking_chart(top, colour), use_container_width=True)

    row = by_year[by_year["year"] == year].iloc[0]
    st.caption(
        f"{year}: {int(row['models'])} notable models from {int(row['organisations'])} organisations; "
        f"training compute is recorded for {int(row['models_with_compute'])} of them ({row['compute_coverage_pct']:.0f}%)."
    )

    with st.expander("Trace a number back to the data"):
        orgs = sorted(year_credit["org"].unique())
        if not orgs:
            st.info(f"No models recorded for {year}.")
        else:
            default = orgs.index(top["org"].iloc[0]) if not totals.empty else 0
            org = st.selectbox("Organisation", orgs, index=default, key="conc_trace_org")
            rows = year_credit[year_credit["org"] == org][
                ["Model", "org_raw", "model_credit", "compute_flop", "compute_credit_flop"]
            ]
            st.dataframe(
                rows.rename(columns={
                    "org_raw": "Organisation as listed",
                    "model_credit": "Model credit",
                    "compute_flop": "Training compute (FLOP)",
                    "compute_credit_flop": "Compute credited (FLOP)",
                }),
                hide_index=True,
                use_container_width=True,
            )
            st.markdown(
                f"Share = this organisation's credited total ÷ the {year} total across all organisations. "
                "Rows come from `data/processed/concentration_org_credit.csv`, built from the Epoch AI CSV by "
                "`scripts/prepare_concentration.py`."
            )

    with st.expander("How this is calculated, and what the data cannot show"):
        st.markdown(
            "- **Parent companies are merged.** Google, Google Brain, Google Research, DeepMind and Google DeepMind "
            "count as *Google (Alphabet)*; Facebook AI Research and Meta AI count as *Meta*; and so on.\n"
            "- **Shared models are split equally.** A model built by two organisations gives each half a model "
            "and half its compute.\n"
            "- **Compute share uses only models with recorded compute.** Coverage ranges from "
            f"{by_year['compute_coverage_pct'].min():.0f}% to {by_year['compute_coverage_pct'].max():.0f}% of models per year "
            "and is lowest in recent years, when frontier labs disclose less.\n"
            "- **Compute and model counts are not capability.** They show who builds and who spends, not whose "
            "models perform best.\n"
            "- **Notable models only.** Epoch AI includes models that meet its notability criteria, so smaller "
            "organisations' work is under-represented.\n"
            "- Source: Epoch AI, *Notable AI Models* (CC BY 4.0), downloaded 21 Oct 2026; 2026 is excluded as a partial year."
        )
