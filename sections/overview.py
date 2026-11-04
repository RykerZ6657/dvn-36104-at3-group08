"""Alternative Overview design: composition first, growth second.
Drop into sections/overview.py. Existing app.py remains unchanged.
Requires streamlit, pandas, plotly; openpyxl if reading XLSX.
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path("/Users/hienlai/Desktop/Data visualization/AT3/data/raw/notable_ai_models.csv")  # EDIT to match your actual file
MIN_YEAR, MAX_YEAR = 2015, 2025
ORDER = ["Academia", "Industry - Academia Collaboration", "Industry", "Other", "Unknown"]
COLORS = {
    "Academia": "#28A58B",
    "Industry - Academia Collaboration": "#E9AD49",
    "Industry": "#5475D8",
    "Other": "#8490A4",
    "Unknown": "#CBD0DA",
}


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


def render(df=None):
    st.markdown("### Who is developing notable AI models?")
    st.caption("Epoch AI · Notable AI Models · 2015–2025 | Model output by developing-organisation sector")
    if df is None:
        df = _load_data()
    if df is None:
        st.info("Set DATA_PATH in sections/overview.py to your existing Epoch AI CSV or Excel file, or pass a DataFrame to render(df).")
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
    st.markdown("#### Explore the overview")
    if len(years) > 1:
        first, last = st.slider("Year range", min_value=years[0], max_value=years[-1], value=(years[0], years[-1]), key="overview_alt_range")
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
    industry_delta = industry_latest - float(industry.loc[first_seen, "Share"])
    industry_count = int(industry.loc[last_seen, "Count"])
    latest_total = int(totals.loc[last_seen])

    k1, k2, k3 = st.columns(3)
    k1.metric("Notable models · selected period", f"{len(selected):,}")
    k2.metric(f"Industry share · {last_seen}", f"{industry_latest:.1f}%", help=f"{industry_count:,} industry models ÷ {latest_total:,} total models in {last_seen}.")
    k3.metric(f"Industry share shift · {first_seen}–{last_seen}", f"{industry_delta:+.1f} pp" if first_seen != last_seen else "N/A", help="Percentage-point change in Industry's annual share between selected endpoints; not a percentage growth rate.")

    st.markdown("---")
    left, right = st.columns([1.8, 1], gap="large")
    with left:
        st.markdown("#### 01 · Who accounts for model output?")
        st.caption("Composition by publication year · every column totals 100%")
        fig_share = go.Figure()
        for sector in ORDER:
            part = counts[counts["Sector"].eq(sector)].sort_values("Year")
            fig_share.add_bar(
                x=part["Year"], y=part["Share"], name=sector,
                marker_color=COLORS[sector],
                customdata=part[["Count", "Total"]].to_numpy(),
                hovertemplate=("<b>%{fullData.name}</b><br>Year: %{x}<br>Share: %{y:.1f}%"
                               "<br>Models: %{customdata[0]:,}<br>Annual total: %{customdata[1]:,}<extra></extra>"),
            )
        fig_share.update_layout(
            barmode="stack", height=440, margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", y=-0.2, x=0, title=None),
            hovermode="closest", yaxis=dict(title="Share of annual models (%)", range=[0, 100], ticksuffix="%"),
            xaxis=dict(title=None, dtick=1, type="linear"),
        )
        st.plotly_chart(fig_share, use_container_width=True, key="overview_alt_share")
    with right:
        st.markdown("#### 02 · Is total output growing?")
        st.caption("All notable models published per year · absolute counts")
        growth = go.Figure()
        growth.add_trace(go.Scatter(
            x=totals.index.astype(int), y=totals.to_numpy(), mode="lines+markers",
            line=dict(color="#5475D8", width=3), marker=dict(size=8),
            fill="tozeroy", fillcolor="rgba(84,117,216,.12)", name="All sectors",
            hovertemplate="Year: %{x}<br>Models: %{y:,}<extra></extra>",
        ))
        growth.update_layout(
            height=440, margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
            xaxis=dict(title=None, dtick=1, type="linear"),
            yaxis=dict(title="Number of models", rangemode="tozero"),
        )
        st.plotly_chart(growth, use_container_width=True, key="overview_alt_growth")

    st.caption("Interpretation: changes in sector share are not equivalent to changes in model counts. Sector-level output does not establish concentration among individual organisations.")

    with st.expander("Data checks, classification and calculation audit"):
        st.write(f"Source rows: **{raw_rows:,}** · Missing/unparseable dates: **{bad_dates:,}** · Records in {MIN_YEAR}–{MAX_YEAR}: **{len(data):,}** · Selected rows: **{len(selected):,}**")
        st.write("Source categories Industry, Academia, and Industry - Academia Collaboration are mapped only from exact standardised values. Every other recorded label is Other; missing sector labels are Unknown. All categories remain in the denominator.")
        st.write("Share = model count for sector and publication year ÷ all model records in that year × 100. Annual model counts are not adjusted for total AI activity outside this dataset.")
        st.write("Publication dates may include source-imputed month/day values, so visual comparisons use years only.")
        source_categories = (selected.groupby(["Organization categorization", "Sector"], dropna=False).size().reset_index(name="Models"))
        st.dataframe(source_categories, hide_index=True, use_container_width=True)
        st.dataframe(counts.rename(columns={"Count": "Models", "Share": "Share (%)"}), hide_index=True, use_container_width=True)
        st.download_button("Download annual sector calculations", counts.to_csv(index=False).encode("utf-8"), file_name="overview_alternative_audit.csv", mime="text/csv")
