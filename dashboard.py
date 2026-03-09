"""
Net Lease Intelligence Dashboard
Run: streamlit run dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import io

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Net Lease Intel",
    page_icon="NL",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom theme via CSS
st.markdown("""
<style>
    /* Dark header bar */
    .stApp > header { background-color: transparent; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 10px;
        padding: 15px 20px;
        color: white;
    }
    div[data-testid="stMetric"] label { color: #a8b2d1 !important; font-size: 0.85rem; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #64ffda !important; }

    /* Sidebar styling — dark theme */
    section[data-testid="stSidebar"] {
        background: #1a1a2e;
        border-right: 1px solid #233554;
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #e6f1ff; }
    section[data-testid="stSidebar"] .stRadio label { color: #ccd6f6 !important; font-weight: 500; }
    section[data-testid="stSidebar"] .stRadio label:hover { color: #64ffda !important; }
    section[data-testid="stSidebar"] .stCaption { color: #8892b0 !important; }
    section[data-testid="stSidebar"] small { color: #a8b2d1 !important; }

    /* Tables */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Section dividers */
    hr { border-color: #233554; margin: 1.5rem 0; }

    /* Reduce top padding */
    .block-container { padding-top: 2rem; }

    /* Tag-style badges for categories */
    .category-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-future { background: #064e3b; color: #6ee7b7; }
    .badge-active { background: #7c2d12; color: #fed7aa; }
    .badge-asset { background: #1e3a5f; color: #93c5fd; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOADING
# ============================================================
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "outputs")

PLOTLY_TEMPLATE = "plotly_dark"
CHART_COLORS = ["#64ffda", "#f78166", "#7ee8fa", "#eec643", "#a78bfa",
                "#f472b6", "#34d399", "#fb923c", "#60a5fa", "#c084fc"]


@st.cache_data(ttl=300)
def load_data(filename):
    path = os.path.join(OUT, filename)
    if os.path.exists(path):
        return pd.read_excel(path)
    return pd.DataFrame()


corp_df = load_data("corporate_re_targets.xlsx")
ercot_df = load_data("ercot_queue_scored.xlsx")
nyiso_df = load_data("nyiso_queue_scored.xlsx")
ferc_df = load_data("ferc_interconnection_filings.xlsx")
permit_df = load_data("commercial_permits.xlsx")


@st.cache_data(ttl=300)
def load_convergence():
    path = os.path.join(OUT, "convergence_signals.xlsx")
    if not os.path.exists(path):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    corp_conv = pd.read_excel(path, sheet_name="Corporate Convergence") if "Corporate Convergence" in pd.ExcelFile(path).sheet_names else pd.DataFrame()
    queue_ferc = pd.read_excel(path, sheet_name="Queue-FERC Matches") if "Queue-FERC Matches" in pd.ExcelFile(path).sheet_names else pd.DataFrame()
    permit_clusters = pd.read_excel(path, sheet_name="Permit Clusters") if "Permit Clusters" in pd.ExcelFile(path).sheet_names else pd.DataFrame()
    return corp_conv, queue_ferc, permit_clusters


conv_corp_df, conv_qf_df, conv_clusters_df = load_convergence()
transcript_df = load_data("earnings_transcript_signals.xlsx")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## Net Lease Intel")
    st.caption("Deal sourcing intelligence")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["Signal Feed", "Corporate Targets", "Earnings Transcripts",
         "Building Permits", "Interconnection Queues", "FERC Filings",
         "Convergence Signals"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Data freshness
    st.markdown("##### Data Sources")
    sources = {
        "Corporate": len(corp_df),
        "Permits": len(permit_df),
        "ERCOT": len(ercot_df),
        "NYISO": len(nyiso_df),
        "FERC": len(ferc_df),
        "Transcripts": len(transcript_df),
        "Convergence": len(conv_corp_df) + len(conv_qf_df),
    }
    for name, count in sources.items():
        st.markdown(f"<small>{name}: **{count:,}** records</small>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"Updated {datetime.now().strftime('%b %d, %Y %I:%M %p')}")


# ============================================================
# HELPERS
# ============================================================
def format_currency(val):
    if pd.isna(val) or val == 0:
        return "—"
    if val >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    if val >= 1_000:
        return f"${val/1_000:,.0f}K"
    return f"${val:,.0f}"


def make_chart(fig, height=350):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def csv_download(df, filename, label="Download CSV"):
    """Add a CSV download button for a dataframe."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, buf.getvalue(), file_name=filename, mime="text/csv")


# Portal URLs for each municipality (dataset-level, not record-level)
PERMIT_PORTALS = {
    "Chicago": "https://data.cityofchicago.org/d/ydr8-5enu",
    "Dallas": "https://www.dallasopendata.com/d/e7gq-4sah",
    "Austin": "https://datahub.austintexas.gov/d/3syk-w9eu",
    "Baton Rouge": "https://data.brla.gov/d/7fq7-8j7r",
    "Norfolk": "https://data.norfolk.gov/d/fahm-yuh4",
    "Mesa": "https://citydata.mesaaz.gov/d/dzpk-hxfb",
    "Los Angeles": "https://data.lacity.org/d/pi9x-tg5x",
    "Kansas City": "https://data.kcmo.org/d/ntw8-aacc",
    "Seattle": "https://cos-data.seattle.gov/d/76t5-zqzr",
    "Cincinnati": "https://data.cincinnati-oh.gov/d/uhjb-xac9",
    "Little Rock": "https://data.littlerock.gov/d/mkfu-qap3",
    "Reading": "https://data.readingpa.gov/d/t7j2-qwzz",
    "Cleveland": "https://services3.arcgis.com/dty2kHktVXHrqO8i/arcgis/rest/services/Building_Permits/FeatureServer",
    "Philadelphia": "https://www.opendataphilly.org/datasets/licenses-and-inspections-building-permits/",
    "Pittsburgh": "https://data.wprdc.org/dataset/pittsburgh-pli-permit-data",
    "Nashville": "https://data.nashville.gov/",
    "Greenville": "https://data-greenvillesc.opendata.arcgis.com/",
    "Columbus": "https://maps2.columbus.gov/arcgis/rest/services/Schemas/BuildingZoning/MapServer/5",
    "Louisville": "https://data.louisvilleky.gov/",
    "Minneapolis": "https://opendata.minneapolismn.gov/",
    "St. Paul": "https://information.stpaul.gov/",
    "Memphis": "https://data.opendatasoft.com/explore/dataset/shelby-county-building-and-demolition-permits@datamidsouth/",
    "Omaha": "https://www.civicdata.com/dataset/city-of-omaha-building-permits",
}

# Add Source Portal links to permit data
if not permit_df.empty and "Municipality" in permit_df.columns:
    permit_df["Source Portal"] = permit_df["Municipality"].map(PERMIT_PORTALS)


# ============================================================
# PAGE: SIGNAL FEED
# ============================================================
if page == "Signal Feed":
    st.markdown("# Signal Feed")
    st.markdown("*Top opportunities across all data sources*")

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Corporate Targets", f"{len(corp_df):,}")
    c2.metric("Permits Tracked", f"{len(permit_df):,}")
    c3.metric("ERCOT Projects", f"{len(ercot_df):,}")
    c4.metric("NYISO Projects", f"{len(nyiso_df):,}")
    c5.metric("FERC Filings", f"{len(ferc_df):,}")

    st.markdown("---")

    # Two-column layout: Corporate targets + High-value permits
    left, right = st.columns([1, 1])

    with left:
        st.markdown("### Top Corporate Targets")
        st.caption("Companies signaling future sale-leaseback or asset monetization")
        if not corp_df.empty and "Quote Category" in corp_df.columns:
            priority = ["FUTURE_INTENT", "ACTIVE_MONETIZATION", "ASSET_LIGHT_SHIFT", "BUILD_TO_SUIT"]
            top = corp_df[corp_df["Quote Category"].isin(priority)].copy()
            top["_p"] = top["Quote Category"].map({c: i for i, c in enumerate(priority)})
            top = top.sort_values(["_p", "Best Score"], ascending=[True, False]).head(12)
            cols = [c for c in ["Company", "Ticker", "Quote Category", "Best Score", "Sector"]
                    if c in top.columns]
            st.dataframe(top[cols], use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Highest-Value Permits")
        st.caption("Top permits per city (max 2 per city to show breadth)")
        if not permit_df.empty and "Estimated Value" in permit_df.columns:
            # Take top 2 per city to avoid Cleveland dominating
            top_p = permit_df.dropna(subset=["Estimated Value"])
            top_p = top_p.sort_values("Estimated Value", ascending=False)
            top_p = top_p.groupby("Municipality").head(2).sort_values("Estimated Value", ascending=False).head(14)
            top_p["Estimated Value"] = top_p["Estimated Value"].apply(format_currency)
            cols = [c for c in ["Municipality", "Address", "Description", "Estimated Value"]
                    if c in top_p.columns]
            st.dataframe(top_p[cols], use_container_width=True, hide_index=True)

    st.markdown("---")

    # Interconnection projects side by side
    left, right = st.columns(2)

    with left:
        st.markdown("### Top ERCOT Projects")
        if not ercot_df.empty:
            sc = "NL_Score" if "NL_Score" in ercot_df.columns else "score"
            top_e = ercot_df.sort_values(sc, ascending=False).head(8)
            ecols = [c for c in ["Project Name", "Fuel", "MW", "County", sc]
                     if c in top_e.columns]
            st.dataframe(top_e[ecols], use_container_width=True, hide_index=True)

    with right:
        st.markdown("### Top NYISO Projects")
        if not nyiso_df.empty:
            top_n = nyiso_df.sort_values("score", ascending=False).head(8)
            ncols = [c for c in ["Project Name", "Type/ Fuel", "SP (MW)", "County", "score"]
                     if c in top_n.columns]
            st.dataframe(top_n[ncols], use_container_width=True, hide_index=True)

    st.markdown("---")

    # Recent FERC filings
    st.markdown("### Latest FERC Filings")
    if not ferc_df.empty:
        recent = ferc_df.sort_values("filed_date", ascending=False).head(10)
        fcols = [c for c in ["filed_date", "docket", "company", "project_id", "description"]
                 if c in recent.columns]
        st.dataframe(recent[fcols], use_container_width=True, hide_index=True)


# ============================================================
# PAGE: CORPORATE TARGETS
# ============================================================
elif page == "Corporate Targets":
    st.markdown("# Corporate Real Estate Targets")
    st.caption("291 companies analyzed from SEC 10-K/8-K filings for sale-leaseback and asset monetization signals")

    if corp_df.empty:
        st.warning("No corporate target data found.")
    else:
        # Filters in a clean row
        f1, f2, f3 = st.columns(3)
        with f1:
            cats = ["All"] + sorted(corp_df.get("Quote Category", pd.Series()).dropna().unique().tolist())
            sel_cat = st.selectbox("Category", cats)
        with f2:
            secs = ["All"] + sorted(corp_df.get("Sector", pd.Series()).dropna().unique().tolist())
            sel_sec = st.selectbox("Sector", secs)
        with f3:
            search = st.text_input("Search company")

        filtered = corp_df.copy()
        if sel_cat != "All" and "Quote Category" in filtered.columns:
            filtered = filtered[filtered["Quote Category"] == sel_cat]
        if sel_sec != "All" and "Sector" in filtered.columns:
            filtered = filtered[filtered["Sector"] == sel_sec]
        if search:
            filtered = filtered[filtered["Company"].str.contains(search, case=False, na=False)]

        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Showing", f"{len(filtered)}")
        if "Quote Category" in corp_df.columns:
            m2.metric("Future Intent", len(corp_df[corp_df["Quote Category"] == "FUTURE_INTENT"]))
            m3.metric("Active Monetization", len(corp_df[corp_df["Quote Category"] == "ACTIVE_MONETIZATION"]))
            m4.metric("Asset-Light Shift", len(corp_df[corp_df["Quote Category"] == "ASSET_LIGHT_SHIFT"]))

        # Chart + Table side by side
        chart_col, table_col = st.columns([2, 5])

        with chart_col:
            if "Quote Category" in corp_df.columns:
                cat_counts = corp_df["Quote Category"].value_counts()
                fig = px.pie(values=cat_counts.values, names=cat_counts.index,
                             color_discrete_sequence=CHART_COLORS)
                fig = make_chart(fig, height=300)
                fig.update_traces(textposition='inside', textinfo='value')
                fig.update_layout(title="By Category", showlegend=True,
                                  legend=dict(orientation="h", yanchor="top", y=-0.1))
                st.plotly_chart(fig, use_container_width=True)

        with table_col:
            display_cols = [c for c in ["Company", "Ticker", "Quote Category", "Best Score",
                                         "Sector", "Industry", "Market Cap", "Filing Quote"]
                            if c in filtered.columns]
            st.dataframe(filtered[display_cols].sort_values("Best Score", ascending=False),
                         use_container_width=True, hide_index=True, height=450,
                         column_config={
                             "Market Cap": st.column_config.NumberColumn(format="$%,.0f"),
                         })

        csv_download(filtered, "corporate_targets.csv", "Export Corporate Targets CSV")


# ============================================================
# PAGE: EARNINGS TRANSCRIPTS
# ============================================================
elif page == "Earnings Transcripts":
    st.markdown("# Earnings Call Transcript Signals")
    st.caption("Keywords from earnings calls — sale-leaseback, asset-light, BTS, facility expansion")

    if transcript_df.empty:
        st.warning("No transcript data found. Run: `python scripts/scrape_transcripts.py --deep`")
    else:
        # Filter out REITs
        reit_kw = ['reit', 'realty', 'net lease', 'properties trust', 'prologis',
                    'broadstone', 'four corners', 'agree realty', 'essential properties',
                    'w. p. carey', 'w p carey', 'nnn reit', 'spirit realty', 'store capital',
                    'glpi', 'gaming and leisure', 'gladstone commercial', 'vici properties']
        tdf = transcript_df.copy()
        tdf["_company_lower"] = tdf["company"].astype(str).str.lower()
        tdf = tdf[~tdf["_company_lower"].apply(lambda c: any(k in c for k in reit_kw))].drop(columns=["_company_lower"])

        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            cats = ["All"] + sorted(tdf["category"].dropna().unique().tolist())
            sel_cat = st.selectbox("Signal Strength", cats)
        with f2:
            min_score = st.slider("Min Score", 0, int(tdf["score"].max()), 0)
        with f3:
            kw_filter = st.text_input("Keyword filter")

        filtered = tdf.copy()
        if sel_cat != "All":
            filtered = filtered[filtered["category"] == sel_cat]
        if min_score > 0:
            filtered = filtered[filtered["score"] >= min_score]
        if kw_filter:
            filtered = filtered[
                filtered["top_keywords"].astype(str).str.contains(kw_filter, case=False, na=False) |
                filtered["company"].astype(str).str.contains(kw_filter, case=False, na=False) |
                filtered["excerpt_text"].astype(str).str.contains(kw_filter, case=False, na=False)
            ]

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Signals", f"{len(filtered):,}")
        m2.metric("Strong", f"{len(filtered[filtered['category'] == 'STRONG_SIGNAL']):,}")
        m3.metric("Moderate", f"{len(filtered[filtered['category'] == 'MODERATE_SIGNAL']):,}")
        m4.metric("Companies", f"{filtered['company'].nunique():,}")

        st.markdown("---")

        # Charts row
        chart_col, table_col = st.columns([1, 2])
        with chart_col:
            # Category breakdown
            cat_counts = filtered["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            colors = {"STRONG_SIGNAL": "#f78166", "MODERATE_SIGNAL": "#64ffda", "WEAK_SIGNAL": "#a8b2d1"}
            fig = px.pie(cat_counts, values="Count", names="Category",
                         color="Category", color_discrete_map=colors)
            st.plotly_chart(make_chart(fig, height=300), use_container_width=True)

            # Top keywords
            if "top_keywords" in filtered.columns:
                all_kws = []
                for kws in filtered["top_keywords"].dropna():
                    all_kws.extend([k.strip() for k in str(kws).split(",")])
                if all_kws:
                    kw_counts = pd.Series(all_kws).value_counts().head(10).reset_index()
                    kw_counts.columns = ["Keyword", "Count"]
                    fig2 = px.bar(kw_counts, x="Count", y="Keyword", orientation="h",
                                  color="Count", color_continuous_scale=["#1a1a2e", "#64ffda"])
                    fig2.update_layout(title="Top Keywords", showlegend=False)
                    st.plotly_chart(make_chart(fig2, height=350), use_container_width=True)

        with table_col:
            display_cols = [c for c in ["company", "ticker", "date", "score", "category",
                                         "top_keywords", "excerpt_text"]
                           if c in filtered.columns]
            col_config = {
                "score": st.column_config.NumberColumn("Score"),
                "excerpt_text": st.column_config.TextColumn("Key Excerpts", width="large"),
                "url": st.column_config.LinkColumn("Link"),
            }
            st.dataframe(
                filtered[display_cols].sort_values("score", ascending=False),
                use_container_width=True, hide_index=True, height=600,
                column_config=col_config,
            )

            csv_download(filtered, "earnings_transcript_signals.csv", "Export Transcripts CSV")


# ============================================================
# PAGE: BUILDING PERMITS
# ============================================================
elif page == "Building Permits":
    st.markdown("# Commercial Building Permits")
    st.caption("Commercial permits across monitored cities — new construction, major renovations, demolitions")

    if permit_df.empty:
        st.warning("No permit data found.")
    else:
        # City coordinates for map
        CITY_COORDS = {
            "Cleveland": (41.4993, -81.6944), "Cincinnati": (39.1031, -84.5120),
            "Austin": (30.2672, -97.7431), "Dallas": (32.7767, -96.7970),
            "Chicago": (41.8781, -87.6298), "Baton Rouge": (30.4515, -91.1871),
            "Norfolk": (36.8508, -76.2859), "Mesa": (33.4152, -111.8315),
            "Los Angeles": (34.0522, -118.2437), "Kansas City": (39.0997, -94.5786),
            "Little Rock": (34.7465, -92.2896), "Seattle": (47.6062, -122.3321),
            "Columbus": (39.9612, -82.9988), "Nashville": (36.1627, -86.7816),
            "Philadelphia": (39.9526, -75.1652), "Pittsburgh": (40.4406, -79.9959),
            "Reading": (40.3357, -75.9269), "Louisville": (38.2527, -85.7585),
            "Minneapolis": (44.9778, -93.2650), "St. Paul": (44.9537, -93.0900),
            "Memphis": (35.1495, -90.0490), "Omaha": (41.2565, -95.9345),
            "Charlotte": (35.2271, -80.8431), "Raleigh": (35.7796, -78.6382),
            "Indianapolis": (39.7684, -86.1581), "Tulsa": (36.1540, -95.9928),
            "Chattanooga": (35.0456, -85.3097), "Knoxville": (35.9606, -83.9207),
            "Huntsville": (34.7304, -86.5861), "Boise": (43.6150, -116.2023),
            "Des Moines": (41.5868, -93.6250), "Grand Rapids": (42.9634, -85.6681),
            "Fort Wayne": (41.0793, -85.1394), "Greenville": (34.8526, -82.3940),
            "Savannah": (32.0809, -81.0912), "Spokane": (47.6588, -117.4260),
            "Toledo": (41.6528, -83.5379), "Dayton": (39.7589, -84.1916),
            "El Paso": (31.7619, -106.4850), "Corpus Christi": (27.8006, -97.3964),
            "Shreveport": (32.5252, -93.7502), "Syracuse": (43.0481, -76.1474),
            "Rochester": (43.1566, -77.6088), "Albany": (42.6526, -73.7562),
            "Harrisburg": (40.2732, -76.8867), "Allentown": (40.6084, -75.4902),
            "Sioux Falls": (43.5446, -96.7311), "Reno": (39.5296, -119.8138),
        }

        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            cities = ["All"] + sorted(permit_df["Municipality"].dropna().unique().tolist())
            sel_city = st.selectbox("City", cities)
        with f2:
            val_options = {"No minimum": 0, "$100K+": 100_000, "$500K+": 500_000,
                           "$1M+": 1_000_000, "$5M+": 5_000_000, "$10M+": 10_000_000}
            sel_val_label = st.selectbox("Min Value", list(val_options.keys()))
            min_val = val_options[sel_val_label]
        with f3:
            keyword = st.text_input("Keyword in description")

        filtered = permit_df.copy()
        if sel_city != "All":
            filtered = filtered[filtered["Municipality"] == sel_city]
        if min_val > 0:
            filtered = filtered[filtered["Estimated Value"] >= min_val]
        if keyword:
            filtered = filtered[filtered["Description"].str.contains(keyword, case=False, na=False)]

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        total_val = filtered["Estimated Value"].sum()
        m1.metric("Permits", f"{len(filtered):,}")
        m2.metric("Total Value", format_currency(total_val) if pd.notna(total_val) else "—")
        m3.metric(">$1M Permits", f"{len(filtered[filtered['Estimated Value'] >= 1_000_000]):,}")
        m4.metric("Cities", f"{filtered['Municipality'].nunique()}")

        # ---- INTERACTIVE MAP ----
        st.markdown("---")
        city_agg = filtered.groupby("Municipality").agg(
            count=("Municipality", "size"),
            total_value=("Estimated Value", "sum"),
            high_value=("Estimated Value", lambda x: (x >= 1_000_000).sum()),
            state=("State", "first"),
        ).reset_index()

        # Add coordinates
        city_agg["lat"] = city_agg["Municipality"].map(lambda c: CITY_COORDS.get(c, (None, None))[0])
        city_agg["lon"] = city_agg["Municipality"].map(lambda c: CITY_COORDS.get(c, (None, None))[1])
        map_data = city_agg.dropna(subset=["lat", "lon"])

        if len(map_data) > 0:
            map_data["display_value"] = map_data["total_value"].apply(
                lambda v: f"${v/1_000_000:,.1f}M" if v >= 1_000_000 else (f"${v/1_000:,.0f}K" if v >= 1_000 else f"${v:,.0f}")
            )
            map_data["hover_text"] = map_data.apply(
                lambda r: f"<b>{r['Municipality']}, {r['state']}</b><br>"
                          f"Permits: {r['count']:,}<br>"
                          f"Total Value: {r['display_value']}<br>"
                          f">$1M Permits: {r['high_value']}",
                axis=1
            )
            # Bubble size: log-scaled so Cleveland doesn't dominate
            import numpy as np
            map_data["bubble_size"] = np.log1p(map_data["total_value"] / 10_000).clip(lower=8)

            fig_map = go.Figure(go.Scattergeo(
                lat=map_data["lat"],
                lon=map_data["lon"],
                text=map_data["hover_text"],
                hoverinfo="text",
                marker=dict(
                    size=map_data["bubble_size"],
                    color=map_data["total_value"],
                    colorscale=[[0, "#1a1a2e"], [0.3, "#0f3460"], [0.6, "#64ffda"], [1, "#f78166"]],
                    showscale=True,
                    colorbar=dict(title="Value", tickprefix="$", tickformat=",.0s"),
                    line=dict(width=1, color="#64ffda"),
                    sizemode="area",
                    sizeref=0.5,
                ),
            ))
            fig_map.update_layout(
                template=PLOTLY_TEMPLATE,
                height=420,
                margin=dict(l=0, r=0, t=30, b=0),
                title="Permit Activity by City",
                geo=dict(
                    scope="usa",
                    bgcolor="rgba(0,0,0,0)",
                    landcolor="#1a1a2e",
                    lakecolor="#16213e",
                    showlakes=True,
                    showland=True,
                    subunitcolor="#233554",
                    countrycolor="#233554",
                ),
            )
            st.plotly_chart(fig_map, use_container_width=True)

        st.markdown("---")

        # Chart + Table
        chart_col, table_col = st.columns([2, 5])

        with chart_col:
            bar_agg = permit_df.groupby("Municipality").agg(
                count=("Municipality", "size"),
                total_value=("Estimated Value", "sum")
            ).sort_values("total_value", ascending=True).tail(10)

            fig = px.bar(bar_agg, x="total_value", y=bar_agg.index, orientation="h",
                         color_discrete_sequence=["#64ffda"],
                         labels={"total_value": "Total Value", "y": ""})
            fig = make_chart(fig, height=350)
            fig.update_layout(title="Value by City", xaxis_tickformat="$,.0s")
            st.plotly_chart(fig, use_container_width=True)

        with table_col:
            display_cols = [c for c in ["Municipality", "State", "Filing Date", "Address",
                                         "Description", "Estimated Value", "Sq Ft",
                                         "Contractor", "Source Portal"]
                            if c in filtered.columns]
            display = filtered[display_cols].sort_values("Estimated Value", ascending=False).copy()
            col_config = {
                "Estimated Value": st.column_config.NumberColumn(format="$%,.0f"),
                "Sq Ft": st.column_config.NumberColumn(format="%,.0f"),
            }
            if "Source Portal" in display.columns:
                col_config["Source Portal"] = st.column_config.LinkColumn("Source Portal", display_text="View Portal")
            st.dataframe(
                display,
                use_container_width=True, hide_index=True, height=450,
                column_config=col_config,
            )

            csv_download(filtered, "commercial_permits.csv", "Export Permits CSV")


# ============================================================
# PAGE: INTERCONNECTION QUEUES
# ============================================================
elif page == "Interconnection Queues":
    st.markdown("# Interconnection Queues")
    st.caption("Power generation projects seeking grid connection — data centers, battery storage, gas plants")

    tab_ercot, tab_nyiso = st.tabs(["ERCOT — Texas", "NYISO — New York"])

    with tab_ercot:
        if ercot_df.empty:
            st.warning("No ERCOT data.")
        else:
            sc = "NL_Score" if "NL_Score" in ercot_df.columns else "score"

            f1, f2, f3 = st.columns(3)
            with f1:
                fuels = ["All"] + sorted(ercot_df["Fuel"].dropna().unique().tolist())
                sel_fuel = st.selectbox("Fuel Type", fuels, key="ef")
            with f2:
                min_sc = st.slider("Min Score", 0, int(ercot_df[sc].max()), 15, key="es")
            with f3:
                ercot_search = st.text_input("Search project", key="esearch")

            filtered = ercot_df.copy()
            if sel_fuel != "All":
                filtered = filtered[filtered["Fuel"] == sel_fuel]
            filtered = filtered[filtered[sc] >= min_sc]
            if ercot_search:
                filtered = filtered[filtered["Project Name"].str.contains(ercot_search, case=False, na=False)]

            m1, m2, m3 = st.columns(3)
            m1.metric("Projects", f"{len(filtered):,}")
            total_mw = filtered["MW"].sum() if "MW" in filtered.columns else 0
            m2.metric("Total MW", f"{total_mw:,.0f}")
            m3.metric("Avg Score", f"{filtered[sc].mean():.1f}")

            chart_col, table_col = st.columns([2, 5])
            with chart_col:
                fuel_counts = ercot_df["Fuel"].value_counts().head(8)
                fig = px.pie(values=fuel_counts.values, names=fuel_counts.index,
                             color_discrete_sequence=CHART_COLORS)
                fig = make_chart(fig, height=300)
                fig.update_layout(title="By Fuel Type")
                st.plotly_chart(fig, use_container_width=True)

            with table_col:
                ecols = [c for c in ["Project Name", "Fuel", "Technology", "MW",
                                      "County", "Projected COD", "GIM Study Phase",
                                      "Interconnecting Entity", sc, "NL_Reasons"]
                         if c in filtered.columns]
                st.dataframe(filtered[ecols].sort_values(sc, ascending=False),
                             use_container_width=True, hide_index=True, height=450)

            csv_download(filtered, "ercot_queue.csv", "Export ERCOT CSV")

    with tab_nyiso:
        if nyiso_df.empty:
            st.warning("No NYISO data.")
        else:
            f1, f2 = st.columns(2)
            with f1:
                fuels = ["All"] + sorted(nyiso_df["Type/ Fuel"].dropna().unique().tolist())
                sel_fuel = st.selectbox("Fuel Type", fuels, key="nf")
            with f2:
                min_sc = st.slider("Min Score", 0, int(nyiso_df["score"].max()), 10, key="ns")

            filtered = nyiso_df.copy()
            if sel_fuel != "All":
                filtered = filtered[filtered["Type/ Fuel"] == sel_fuel]
            filtered = filtered[filtered["score"] >= min_sc]

            m1, m2, m3 = st.columns(3)
            m1.metric("Projects", f"{len(filtered):,}")
            mw = filtered["SP (MW)"].sum() if "SP (MW)" in filtered.columns else 0
            m2.metric("Total MW", f"{mw:,.0f}")
            m3.metric("Avg Score", f"{filtered['score'].mean():.1f}")

            ncols = [c for c in ["Project Name", "Developer/Interconnection Customer",
                                  "Type/ Fuel", "SP (MW)", "County", "State",
                                  "Proposed COD", "score"]
                     if c in filtered.columns]
            st.dataframe(filtered[ncols].sort_values("score", ascending=False),
                         use_container_width=True, hide_index=True, height=500)

            csv_download(filtered, "nyiso_queue.csv", "Export NYISO CSV")


# ============================================================
# PAGE: FERC FILINGS
# ============================================================
elif page == "FERC Filings":
    st.markdown("# FERC Interconnection Filings")
    st.caption("1,859 generator interconnection agreements — covers PJM, MISO, SPP, NYISO, ISO-NE")

    if ferc_df.empty:
        st.warning("No FERC data found.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            search = st.text_input("Search company or description", key="fs")
        with f2:
            top_filers = ferc_df["company"].value_counts().head(15).index.tolist()
            filer_opts = ["All"] + [f for f in top_filers if f and len(str(f)) > 3]
            sel_filer = st.selectbox("Filter by ISO/utility", filer_opts)

        filtered = ferc_df.copy()
        if search:
            mask = (
                filtered["company"].str.contains(search, case=False, na=False) |
                filtered["description"].str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        if sel_filer != "All":
            filtered = filtered[filtered["company"] == sel_filer]

        m1, m2, m3 = st.columns(3)
        m1.metric("Filings Shown", f"{len(filtered):,}")
        m2.metric("Unique Dockets", f"{filtered['docket'].nunique():,}")
        with_mw = filtered["capacity_mw"].notna().sum() if "capacity_mw" in filtered.columns else 0
        m3.metric("With MW Data", f"{with_mw:,}")

        # Chart + table
        chart_col, table_col = st.columns([2, 5])

        with chart_col:
            filer_counts = ferc_df["company"].value_counts().head(8)
            filer_counts = filer_counts[filer_counts.index.map(lambda x: len(str(x)) > 3)]
            fig = px.bar(x=filer_counts.values, y=filer_counts.index, orientation="h",
                         color_discrete_sequence=["#f78166"],
                         labels={"x": "Filings", "y": ""})
            fig = make_chart(fig, height=300)
            fig.update_layout(title="Top Filers")
            st.plotly_chart(fig, use_container_width=True)

        with table_col:
            fcols = [c for c in ["filed_date", "docket", "company", "project_id",
                                  "capacity_mw", "description"]
                     if c in filtered.columns]
            st.dataframe(filtered[fcols].sort_values("filed_date", ascending=False),
                         use_container_width=True, hide_index=True, height=450)

            csv_download(filtered, "ferc_filings.csv", "Export FERC CSV")

# ============================================================
# PAGE 6: CONVERGENCE SIGNALS
# ============================================================
elif page == "Convergence Signals":
    st.header("Convergence Signals")
    st.markdown("Entities appearing across multiple data sources — higher convergence = stronger signal.")

    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Corporate Cross-Matches", len(conv_corp_df))
    m2.metric("Queue-FERC Matches", len(conv_qf_df))
    m3.metric("Permit Clusters", len(conv_clusters_df))

    st.markdown("---")

    # Tab layout
    tab1, tab2, tab3 = st.tabs(["Corporate Convergence", "Queue-FERC Matches", "Permit Clusters"])

    with tab1:
        st.subheader("Corporate Targets in Multiple Sources")
        if len(conv_corp_df) > 0:
            chart_col, table_col = st.columns([1, 2])
            with chart_col:
                fig = px.bar(conv_corp_df.sort_values("sources_count"),
                             x="sources_count", y="entity", orientation="h",
                             color="sources_count",
                             color_continuous_scale=["#1a1a2e", "#64ffda"],
                             labels={"sources_count": "Sources", "entity": ""})
                fig = make_chart(fig, height=max(250, len(conv_corp_df) * 35))
                fig.update_layout(title="Sources per Entity", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with table_col:
                display_cols = [c for c in ["entity", "ticker", "sec_category", "sec_score",
                                            "sources_count", "sources", "match_summary"]
                                if c in conv_corp_df.columns]
                st.dataframe(conv_corp_df[display_cols].sort_values("sources_count", ascending=False),
                             use_container_width=True, hide_index=True, height=400)

                csv_download(conv_corp_df, "corporate_convergence.csv", "Export Corporate Convergence CSV")
        else:
            st.info("No corporate convergence signals found. Run build_convergence.py to generate.")

    with tab2:
        st.subheader("Interconnection Queue Developers Also in FERC")
        if len(conv_qf_df) > 0:
            # Filters
            f1, f2 = st.columns(2)
            with f1:
                qf_source = st.selectbox("Queue Source", ["All"] + sorted(conv_qf_df["queue_source"].dropna().unique().tolist()) if "queue_source" in conv_qf_df.columns else ["All"])
            with f2:
                qf_search = st.text_input("Search entity", key="qf_search")

            filtered_qf = conv_qf_df.copy()
            if qf_source != "All" and "queue_source" in filtered_qf.columns:
                filtered_qf = filtered_qf[filtered_qf["queue_source"] == qf_source]
            if qf_search:
                mask = filtered_qf.apply(lambda r: qf_search.lower() in str(r).lower(), axis=1)
                filtered_qf = filtered_qf[mask]

            chart_col, table_col = st.columns([1, 2])
            with chart_col:
                if "queue_source" in filtered_qf.columns:
                    src_counts = filtered_qf["queue_source"].value_counts()
                    fig = px.pie(values=src_counts.values, names=src_counts.index,
                                 color_discrete_sequence=CHART_COLORS)
                    fig = make_chart(fig, height=280)
                    fig.update_layout(title="By Queue Source")
                    st.plotly_chart(fig, use_container_width=True)

                if "mw" in filtered_qf.columns:
                    top_mw = filtered_qf.nlargest(10, "mw")
                    fig2 = px.bar(top_mw, x="mw", y="entity", orientation="h",
                                  color_discrete_sequence=["#64ffda"],
                                  labels={"mw": "MW", "entity": ""})
                    fig2 = make_chart(fig2, height=300)
                    fig2.update_layout(title="Top Projects by MW")
                    st.plotly_chart(fig2, use_container_width=True)

            with table_col:
                qf_cols = [c for c in ["entity", "queue_source", "project", "fuel", "mw",
                                        "queue_score", "ferc_docket", "ferc_description"]
                           if c in filtered_qf.columns]
                col_config = {}
                if "mw" in qf_cols:
                    col_config["mw"] = st.column_config.NumberColumn("MW", format="%,.0f")
                st.dataframe(filtered_qf[qf_cols], use_container_width=True,
                             hide_index=True, height=500, column_config=col_config)

                csv_download(filtered_qf, "queue_ferc_matches.csv", "Export Queue-FERC CSV")
        else:
            st.info("No queue-FERC matches found.")

    with tab3:
        st.subheader("Permit Activity Clusters (Same Address)")
        if len(conv_clusters_df) > 0:
            # Filter by city
            if "city" in conv_clusters_df.columns:
                cities = ["All"] + sorted(conv_clusters_df["city"].dropna().unique().tolist())
                cluster_city = st.selectbox("City", cities, key="cluster_city")
            else:
                cluster_city = "All"

            filtered_cl = conv_clusters_df.copy()
            if cluster_city != "All" and "city" in filtered_cl.columns:
                filtered_cl = filtered_cl[filtered_cl["city"] == cluster_city]

            chart_col, table_col = st.columns([1, 2])
            with chart_col:
                top_clusters = filtered_cl.nlargest(15, "total_value")
                fig = px.bar(top_clusters, x="total_value", y="address", orientation="h",
                             color_discrete_sequence=["#f78166"],
                             labels={"total_value": "Total Value", "address": ""})
                fig = make_chart(fig, height=400)
                fig.update_layout(title="Highest Value Clusters")
                fig.update_xaxes(tickprefix="$", tickformat=",")
                st.plotly_chart(fig, use_container_width=True)

            with table_col:
                cl_cols = [c for c in ["address", "city", "permit_count", "total_value",
                                        "descriptions", "contractors"]
                           if c in filtered_cl.columns]
                col_config = {}
                if "total_value" in cl_cols:
                    col_config["total_value"] = st.column_config.NumberColumn("Total Value", format="$%,.0f")
                st.dataframe(filtered_cl[cl_cols].sort_values("total_value", ascending=False),
                             use_container_width=True, hide_index=True, height=500,
                             column_config=col_config)

                csv_download(filtered_cl, "permit_clusters.csv", "Export Clusters CSV")
        else:
            st.info("No permit clusters found.")
