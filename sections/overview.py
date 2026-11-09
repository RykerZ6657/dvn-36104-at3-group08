"""Overview: which sectors develop notable AI models, 2015–2025."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "notable_ai_models.csv"
MIN_YEAR, MAX_YEAR = 2015, 2025
ORDER = ["Academia", "Industry - Academia Collaboration", "Industry", "Other", "Unknown"]
# Okabe-Ito colours, as in the other tabs; pairs stay distinguishable under protan, deutan and tritan simulation
COLORS = {
    "Academia": "#009E73",
    "Industry - Academia Collaboration": "#E69F00",
    "Industry": "#0072B2",
    "Other": "#555555",
    "Unknown": "#BBBBBB",
}
# Label colour inside each bar segment, chosen for contrast with the segment colour
TEXT_COLORS = {
    "Academia": "black",
    "Industry - Academia Collaboration": "black",
    "Industry": "white",
    "Other": "white",
    "Unknown": "black",
}
# Segments below this share (%) are too thin for a label, so they are listed under the chart
MIN_LABEL_SHARE = 4
# Lines labelled with their counts; Other and Unknown stay near zero, start hidden and are listed under the chart
LINE_LABELLED = ["Academia", "Industry - Academia Collaboration", "Industry"]


@st.cache_data
def _load_data():
    if not DATA_PATH.is_file():
        return None
    if DATA_PATH.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(DATA_PATH)
    return pd.read_csv(DATA_PATH)


def _sector(value):
    if pd.isna(value) or not str(value).strip():
        return "Unknown"

    # Split multiple categories and clean spaces/capitalisation
    categories = [
        item.strip().casefold()
        for item in str(value).split(",")
        if item.strip()
    ]

    categories = set(categories)  # Remove duplicates

    # Recognise the original Epoch AI collaboration category
    if "industry - academia collaboration" in categories:
        return "Industry - Academia Collaboration"

    # Classify combinations
    if "industry" in categories and "academia" in categories:
        return "Industry - Academia Collaboration"

    if categories == {"industry"}:
        return "Industry"

    if categories == {"academia"}:
        return "Academia"

    return "Other"


def _label_positions(counts):
    """Place each count label above or below its point so labels on nearby lines do not overlap."""
    positions = {}
    labelled = counts[counts["Sector"].isin(LINE_LABELLED)]
    for year, group in labelled.groupby("Year"):
        values = group.set_index("Sector")["Count"]
        ranked = values.sort_values(ascending=False, kind="stable").index.tolist()
        top, middle, bottom = ranked
        positions[(year, top)] = "top center"
        positions[(year, bottom)] = "bottom center"
        if values[top] - values[middle] >= 8:
            positions[(year, middle)] = "top center"
        elif values[middle] - values[bottom] >= 8:
            positions[(year, middle)] = "bottom center"
        else:
            positions[(year, middle)] = "middle right"
    return positions


def render(df=None):
    st.header("Overview: who develops notable AI models?")
    st.caption("Epoch AI · Notable AI Models · 2015–2025 | Model output by developing-organisation sector")
    if df is None:
        df = _load_data()
    if df is None:
        st.info("Place the Epoch AI CSV at data/raw/notable_ai_models.csv in the repository, or pass a DataFrame to render(df).")
        return

    required = {"Model", "Publication date", "Organization categorization"}
    missing = required.difference(df.columns)
    if missing:
        st.error("Missing required columns: " + ", ".join(sorted(missing)))
        return

    raw_rows = len(df)
    data = df.copy()
    data["Date"] = pd.to_datetime(data["Publication date"], errors="coerce")
    bad_dates = int(data["Date"].isna().sum())
    data = data[data["Date"].notna()].copy()
    data["Year"] = data["Date"].dt.year
    data = data[data["Year"].between(MIN_YEAR, MAX_YEAR)].copy()
    if data.empty:
        st.warning("No valid publication dates are available within the 2015–2025 scope.")
        return
    missing_ids = int(data["Model"].isna().sum() + data["Model"].astype("string").str.strip().eq("").sum())
    duplicates = int(data["Model"].dropna().duplicated().sum())
    if missing_ids or duplicates:
        st.error(f"Model-level audit needed before calculating: {missing_ids} missing/blank Model IDs and {duplicates} duplicate Model IDs. Records have not been silently deleted.")
        return
    data["Sector"] = data["Organization categorization"].map(_sector)

    years = sorted(data["Year"].unique().tolist())
    if len(years) > 1:
        first, last = st.slider("Year range", min_value=years[0], max_value=years[-1], value=(years[0], years[-1]), key="overview_range")
    else:
        first = last = years[0]
        st.caption(f"Year: {first}")
    selected = data[data["Year"].between(first, last)].copy()
    if selected.empty:
        st.warning("No model records in this selected interval.")
        return

    totals = selected.groupby("Year").size().rename("Total")
    actual = selected.groupby(["Year", "Sector"]).size().rename("Count")
    full_index = pd.MultiIndex.from_product([totals.index.tolist(), ORDER], names=["Year", "Sector"])
    counts = actual.reindex(full_index, fill_value=0).reset_index()
    counts["Total"] = counts["Year"].map(totals).astype(int)
    counts["Share"] = counts["Count"] / counts["Total"] * 100
    check_counts = counts.groupby("Year")["Count"].sum().reindex(totals.index)
    if not check_counts.equals(totals):
        st.error("Validation failed: sector counts don't sum to annual model totals.")
        return

    first_seen, last_seen = int(totals.index[0]), int(totals.index[-1])
    industry = counts[counts["Sector"].eq("Industry")].set_index("Year")
    industry_latest = float(industry.loc[last_seen, "Share"])
    industry_first = float(industry.loc[first_seen, "Share"])
    industry_delta = industry_latest - industry_first
    industry_count = int(industry.loc[last_seen, "Count"])
    latest_total = int(totals.loc[last_seen])

    k1, k2, k3 = st.columns(3)
    k1.metric("Notable models · selected period", f"{len(selected):,}")
    k2.metric(f"Industry share · {last_seen}", f"{industry_latest:.1f}%", help=f"{industry_count:,} industry models ÷ {latest_total:,} total models in {last_seen}.")
    k3.metric(f"Industry share shift · {first_seen}–{last_seen}", f"{industry_delta:+.1f} pp" if first_seen != last_seen else "N/A", help="Percentage-point change in Industry's annual share between selected endpoints; not a percentage growth rate.")

    finding = (
        f"Industry accounted for {industry_latest:.1f}% of notable models "
        f"published in {last_seen}"
    )
    if first_seen != last_seen:
        finding += f", compared with {industry_first:.1f}% in {first_seen}"
    st.markdown(f"**Main finding.** {finding}.")

    st.markdown("---")
    left = st.container()
    right = st.container()
    with left:
        st.subheader("Who accounts for model output?")
        st.caption("Composition by publication year · every column totals 100%")
        fig_share = go.Figure()
        for sector in ORDER:
            part = counts[counts["Sector"].eq(sector)].sort_values("Year")
            fig_share.add_bar(
                x=part["Year"], y=part["Share"], name=sector,
                marker_color=COLORS[sector],
                text=[f"{v:.1f}%" if v >= MIN_LABEL_SHARE else "" for v in part["Share"]],
                textposition="inside", insidetextanchor="middle", textangle=0,
                textfont=dict(color=TEXT_COLORS[sector], size=10),
                customdata=part[["Count", "Total"]].to_numpy(),
                hovertemplate=("<b>%{fullData.name}</b><br>Year: %{x}<br>Share: %{y:.1f}%"
                               "<br>Models: %{customdata[0]:,}<br>Annual total: %{customdata[1]:,}<extra></extra>"),
            )
        fig_share.update_layout(
            barmode="stack", height=480, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=dict(text="Sector")),
            uniformtext=dict(minsize=10, mode="show"),
            hovermode="closest", yaxis=dict(title="Share of annual models (%)", range=[0, 100], ticksuffix="%"),
            xaxis=dict(title="Publication year", dtick=1, type="linear"),
        )
        st.plotly_chart(fig_share, use_container_width=True, key="overview_share")
        small = counts[(counts["Share"] > 0) & (counts["Share"] < MIN_LABEL_SHARE)].sort_values(["Year", "Sector"])
        if not small.empty:
            st.caption(
                f"Segments under {MIN_LABEL_SHARE}% are too thin to label: "
                + "; ".join(f"{r.Year} {r.Sector} {r.Share:.1f}% ({r.Count} of {r.Total})" for r in small.itertuples())
            )
    with right:
        st.subheader("How has model output changed by sector?")
        st.caption("Annual model counts · click a sector in the legend to show or hide it")
        ymax = float(counts["Count"].max())
        growth = go.Figure()
        positions = _label_positions(counts)
        for sector in ORDER:
            part = counts[counts["Sector"].eq(sector)].sort_values("Year")
            labelled = sector in LINE_LABELLED
            growth.add_scatter(
                x=part["Year"],
                y=part["Count"],
                name=sector,
                mode="lines+markers+text" if labelled else "lines+markers",
                visible=True if labelled else "legendonly",
                text=part["Count"] if labelled else None,
                textposition=[positions[(y, sector)] for y in part["Year"]] if labelled else None,
                textfont=dict(size=10),
                line=dict(color=COLORS[sector], width=2.5),
                marker=dict(size=6),
                customdata=part[["Share"]].to_numpy(),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>Year: %{x}"
                    "<br>Models: %{y:,}<br>Share of annual models: %{customdata[0]:.1f}%"
                    "<extra></extra>"
                ),
            )
        growth.update_layout(
            height=440,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=dict(text="Sector")),
            xaxis=dict(
                title="Publication year",
                tickmode="linear",
                tick0=first_seen,
                dtick=1,
                type="linear",
                range=[first_seen - 0.5, last_seen + 0.5],
                automargin=True,
            ),
            yaxis=dict(title="Number of models", range=[-0.06 * ymax, ymax * 1.12]),
        )
        st.plotly_chart(growth, use_container_width=True, key="overview_growth")
        quiet = [sector for sector in ORDER if sector not in LINE_LABELLED]
        quiet_counts = counts[counts["Sector"].isin(quiet)]
        listed = []
        for sector in quiet:
            part = quiet_counts[quiet_counts["Sector"].eq(sector)].sort_values("Year")
            listed.append(f"{sector}: " + ", ".join(f"{y} {c}" for y, c in zip(part["Year"], part["Count"])))
        st.caption(
            f"{' and '.join(quiet)} stay at {int(quiet_counts['Count'].max())} models a year or fewer, "
            "so they are hidden here to keep the labels readable; click them in the legend to show them. " + " · ".join(listed)
        )

    st.caption("Interpretation: changes in sector share are not equivalent to changes in model counts. Sector-level output does not establish concentration among individual organisations.")

    with st.expander("Data checks, classification and calculation audit"):
        st.write(f"Source rows: **{raw_rows:,}** · Missing/unparseable dates: **{bad_dates:,}** · Records in {MIN_YEAR}–{MAX_YEAR}: **{len(data):,}** · Selected rows: **{len(selected):,}**")
        st.write("Each Organization categorization value is split on commas, trimmed, lower-cased and de-duplicated. Only Industry gives Industry, only Academia gives Academia, and Industry with Academia gives Industry - Academia Collaboration. Any other label or combination is Other, and a missing label is Unknown. All categories remain in the denominator.")
        st.write("Share = model count for sector and publication year ÷ all model records in that year × 100. Annual model counts are not adjusted for total AI activity outside this dataset.")
        st.write("Publication dates may include source-imputed month/day values, so visual comparisons use years only.")
        source_categories = (selected.groupby(["Organization categorization", "Sector"], dropna=False).size().reset_index(name="Models"))
        st.dataframe(source_categories, hide_index=True, use_container_width=True)
        st.dataframe(counts.rename(columns={"Count": "Models", "Share": "Share (%)"}), hide_index=True, use_container_width=True)
        st.download_button("Download annual sector calculations", counts.to_csv(index=False).encode("utf-8"), file_name="overview_sector_counts.csv", mime="text/csv")
