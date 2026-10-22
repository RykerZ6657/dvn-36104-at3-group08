"""Section 4: Openness. How accessible are notable models, and does that differ by who builds them?

Reads the processed file made by scripts/prepare_openness.py.
Call render() from the main app.
"""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"

# Okabe-Ito colours (colour-blind safe); grey for missing data
RELEASE_ORDER = ["Open weights", "API or hosted access", "Unreleased", "Not recorded"]
RELEASE_COLOURS = ["#009E73", "#56B4E9", "#D55E00", "#BBBBBB"]
ORG_ORDER = ["Industry", "Industry–academia collaboration", "Academia", "Other (government, research collectives)"]


@st.cache_data
def load() -> pd.DataFrame:
    return pd.read_csv(DATA / "openness_models.csv")


def shares(models: pd.DataFrame, by: str) -> pd.DataFrame:
    counts = models.groupby([by, "release"]).size().rename("models").reset_index()
    counts["share"] = 100 * counts["models"] / counts.groupby(by)["models"].transform("sum")
    counts["order"] = counts["release"].map(RELEASE_ORDER.index)
    # Precompute where each segment's label sits, stacking in the same order as the bars
    counts = counts.sort_values([by, "order"])
    counts["frac"] = counts["share"] / 100
    counts["mid"] = counts.groupby(by)["frac"].cumsum() - counts["frac"] / 2
    return counts


def colour(releases: list[str]) -> alt.Color:
    domain = [r for r in RELEASE_ORDER if r in releases]
    return alt.Color(
        "release:N",
        scale=alt.Scale(domain=domain, range=[RELEASE_COLOURS[RELEASE_ORDER.index(r)] for r in domain]),
        legend=alt.Legend(title=None, orient="top"),
    )


def stacked_bars(data: pd.DataFrame, by: str, title: str, horizontal: bool) -> alt.Chart:
    if horizontal:
        category = alt.Y(f"{by}:N", title=None, sort=[o for o in ORG_ORDER if o in set(data[by])],
                         axis=alt.Axis(labelLimit=280))
        position, label_position = alt.X, alt.X
    else:
        category = alt.X(f"{by}:O", title=title, axis=alt.Axis(labelAngle=0))
        position, label_position = alt.Y, alt.Y
    axis = alt.Axis(format="%", title="Share of notable models (%)")
    tooltip = [
        alt.Tooltip(f"{by}:N", title=title or "Organisation type"),
        alt.Tooltip("release:N", title="Release"),
        alt.Tooltip("models:Q", title="Models"),
        alt.Tooltip("share:Q", title="Share (%)", format=".1f"),
    ]
    bars = alt.Chart(data).mark_bar().encode(
        category,
        position("frac:Q", stack="zero", scale=alt.Scale(domain=[0, 1]), axis=axis),
        color=colour(list(data["release"].unique())),
        order=alt.Order("order:Q"),
        tooltip=tooltip,
    )
    # Segment labels so the values are readable without hovering; tiny segments are left unlabelled
    labels = alt.Chart(data[data["share"] >= 7]).mark_text(color="black", fontSize=10).encode(
        category,
        label_position("mid:Q"),
        text=alt.Text("share:Q", format=".0f"),
    )
    return (bars + labels).properties(height=60 * data[by].nunique() + 40 if horizontal else 360)


def render() -> None:
    models = load()

    st.header("Openness: how accessible are these models?")
    st.markdown(
        "Can a university download a model and run it, only call it through a company's service, or not use it at all? "
        "Each notable model is grouped by how it was released: **open weights** (downloadable, under any licence), "
        "**API or hosted access** (usable only through the developer's service), or **unreleased**."
    )

    first, last = int(models["year"].min()), int(models["year"].max())
    left, right = st.columns([3, 2])
    with left:
        start, end = st.slider("Years shown", first, last, (first, last), key="open_years")
    with right:
        show_missing = st.checkbox(
            "Include models with no recorded release type", value=True, key="open_missing",
            help="Mostly 2015–2017 models. Untick to compare only models whose release type is known.",
        )

    shown = models[models["year"].between(start, end)]
    if not show_missing:
        shown = shown[shown["release"] != "Not recorded"]
    if shown.empty:
        st.info("No models match these settings. Widen the year range or include models with no recorded release type.")
        return

    st.subheader("How notable models were released, by year")
    st.altair_chart(stacked_bars(shares(shown, "year"), "year", "Publication year", horizontal=False), use_container_width=True)

    # Compare only years where release type is recorded for at least 90% of models,
    # so a year with a big grey band (2015–2017) is never the baseline
    in_range = models[models["year"].between(start, end)]
    coverage = in_range.groupby("year")["release"].apply(lambda r: (r != "Not recorded").mean())
    well_covered = coverage[coverage >= 0.9].index
    known = in_range[in_range["year"].isin(well_covered) & (in_range["release"] != "Not recorded")]
    by_year = known.groupby("year")["release"].value_counts(normalize=True).unstack(fill_value=0) * 100
    if len(by_year) >= 2:
        y0, y1 = int(by_year.index.min()), int(by_year.index.max())
        st.markdown(
            f"**What this shows:** comparing years where release type is recorded for at least 90% of models, the unreleased share went from "
            f"**{by_year.loc[y0].get('Unreleased', 0):.0f}%** in {y0} to **{by_year.loc[y1].get('Unreleased', 0):.0f}%** in {y1}, "
            f"while API or hosted access went from **{by_year.loc[y0].get('API or hosted access', 0):.0f}%** to "
            f"**{by_year.loc[y1].get('API or hosted access', 0):.0f}%**. Fewer models are kept in-house, but more are offered "
            "only as a service: usable, yet controlled by the company that built them."
        )

    st.subheader("Who releases open weights?")
    by_org = shown[shown["org_type"] != "Not recorded"]
    if by_org.empty:
        st.info("No models with a recorded organisation type in this range.")
    else:
        org_shares = shares(by_org, "org_type")
        st.altair_chart(stacked_bars(org_shares, "org_type", "", horizontal=True), use_container_width=True)
        pivot = org_shares.pivot(index="org_type", columns="release", values="share").fillna(0)
        if {"Industry", "Academia"} <= set(pivot.index):
            st.markdown(
                f"**What this shows:** {pivot.loc['Industry'].get('API or hosted access', 0):.0f}% of industry models are "
                f"offered only through an API or hosted service, against {pivot.loc['Academia'].get('API or hosted access', 0):.0f}% "
                f"for academia. Academia releases open weights more often "
                f"({pivot.loc['Academia'].get('Open weights', 0):.0f}% vs {pivot.loc['Industry'].get('Open weights', 0):.0f}%), "
                "so the service-only route to access is almost entirely an industry choice."
            )
        counts = by_org.groupby("org_type").size()
        st.caption(
            f"{start}–{end}. Models per group: "
            + "; ".join(f"{org} {counts[org]}" for org in ORG_ORDER if org in counts)
            + ". Organisation types come from Epoch AI; a model is a collaboration if both industry and academic organisations built it."
        )

    with st.expander("Trace a number back to the data"):
        c1, c2 = st.columns(2)
        with c1:
            year = st.selectbox("Year", list(range(end, start - 1, -1)), key="open_trace_year")
        with c2:
            release = st.selectbox("Release type", RELEASE_ORDER, key="open_trace_release")
        year_models = shown[shown["year"] == year]
        rows = year_models[year_models["release"] == release]
        if rows.empty:
            st.info(f"No {release.lower()} models in {year} with the current settings.")
        else:
            st.markdown(
                f"{len(rows)} of {len(year_models)} models in {year} are **{release.lower()}** "
                f"({100 * len(rows) / len(year_models):.1f}%)."
            )
            st.dataframe(
                rows[["Model", "Organization", "org_type", "accessibility_raw"]].rename(columns={
                    "org_type": "Organisation type",
                    "accessibility_raw": "Model accessibility (as listed by Epoch AI)",
                }),
                hide_index=True,
                use_container_width=True,
            )
            st.markdown(
                "Rows come from `data/processed/openness_models.csv`, built from the Epoch AI CSV by "
                "`scripts/prepare_openness.py`."
            )

    with st.expander("How this is calculated, and what the data cannot show"):
        st.markdown(
            "- **Release types are grouped.** Epoch AI's three open-weights licences (unrestricted, non-commercial, "
            "restricted use) count as *open weights*; *API access* and *hosted access (no API)* count as *API or hosted access*.\n"
            "- **Shares are of models, not of capability or usage.** One open-weights model counts the same as one frontier API model.\n"
            "- **Release type is missing for 69 models**, almost all from 2015–2017, which is why those years have a large grey band.\n"
            "- **Open weights is not the same as open source.** Training data and code may still be closed, and licences can restrict use.\n"
            "- **Notable models only.** Epoch AI includes models that meet its notability criteria.\n"
            "- Source: Epoch AI, *Notable AI Models* (CC BY 4.0), downloaded 21 Oct 2026; 2026 is excluded as a partial year."
        )
