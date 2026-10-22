import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="NPA Banking Intelligence Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "NPA_Banking_Sector_India_Dataset (1).xlsx")

st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {background: #f5f7fb; border: 1px solid #e2e8f0;
        padding: 14px 16px; border-radius: 12px;}
    h1, h2, h3 {letter-spacing: -0.02em;}
    .small-note {color: #64748b; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_path):
    book = pd.ExcelFile(file_path)
    preferred = "Master_Merged_Panel_Data"
    sheet = preferred if preferred in book.sheet_names else book.sheet_names[0]
    data = pd.read_excel(file_path, sheet_name=sheet)
    data.columns = data.columns.astype(str).str.strip()
    for col in ["Bank_Name", "Bank_Type", "Financial_Year"]:
        if col in data.columns:
            data[col] = data[col].astype("string").str.strip()
    numeric_candidates = [
        "Gross_NPA_Ratio", "Net_NPA_Ratio", "Provision_Coverage_Ratio",
        "Net_Profit", "Return_on_Assets", "Return_on_Equity",
        "Capital_Adequacy_Ratio", "Credit_Growth_Rate", "Total_Assets"
    ]
    for col in numeric_candidates:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    data = data.replace([np.inf, -np.inf], np.nan)
    data["Year_Start"] = pd.to_numeric(
        data["Financial_Year"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce"
    )
    return data

if not os.path.exists(DATA_FILE):
    st.error("Dataset file not found. Place the Excel workbook beside app.py and name it exactly: " + os.path.basename(DATA_FILE))
    st.stop()

df = load_data(DATA_FILE)
required = ["Bank_Name", "Bank_Type", "Financial_Year"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Required columns are missing from the workbook: {missing}")
    st.stop()

st.title("🏦 NPA Banking Intelligence Dashboard")
st.caption("Analysis of Non-Performing Assets in Indian Public and Private Sector Banks")
st.markdown(
    "Explore asset quality, compare public and private sector banks, track financial-year trends, "
    "and examine sector-level lending risk using the supplied academic dataset."
)

with st.sidebar:
    st.header("Dashboard filters")
    types = sorted(df["Bank_Type"].dropna().astype(str).unique().tolist())
    selected_types = st.multiselect("Bank sector", types, default=types)
    bank_pool = df[df["Bank_Type"].isin(selected_types)]
    banks = sorted(bank_pool["Bank_Name"].dropna().astype(str).unique().tolist())
    selected_banks = st.multiselect("Banks (optional)", banks, default=[])
    years = sorted(df["Financial_Year"].dropna().astype(str).unique().tolist(), key=lambda x: int(''.join(filter(str.isdigit, x))[:4] or 0))
    selected_years = st.multiselect("Financial years", years, default=years)
    st.divider()
    st.caption("Source: supplied Excel workbook. Values are shown as recorded in the workbook; verify source figures before making financial decisions.")

filtered = df[df["Bank_Type"].isin(selected_types)].copy()
if selected_banks:
    filtered = filtered[filtered["Bank_Name"].isin(selected_banks)]
if selected_years:
    filtered = filtered[filtered["Financial_Year"].isin(selected_years)]

if filtered.empty:
    st.warning("No records match the current filters. Select at least one bank sector and financial year.")
    st.stop()

# KPI row uses the filtered bank-year records.
def mean_col(frame, col):
    return frame[col].mean() if col in frame.columns and frame[col].notna().any() else np.nan

latest_year = filtered["Year_Start"].max()
latest = filtered[filtered["Year_Start"] == latest_year] if pd.notna(latest_year) else filtered
k1, k2, k3, k4 = st.columns(4)
g = mean_col(latest, "Gross_NPA_Ratio")
n = mean_col(latest, "Net_NPA_Ratio")
pcr = mean_col(latest, "Provision_Coverage_Ratio")
k1.metric("Average Gross NPA", f"{g:.2f}%" if pd.notna(g) else "N/A")
k2.metric("Average Net NPA", f"{n:.2f}%" if pd.notna(n) else "N/A")
k3.metric("Average Provision Coverage", f"{pcr:.2f}%" if pd.notna(pcr) else "N/A")
k4.metric("Bank-year records", f"{len(filtered):,}")

st.caption(f"Latest financial year within the selected filters: {latest['Financial_Year'].iloc[0] if not latest.empty else 'Not available'}. KPI values are simple averages of selected bank-year records, not weighted sector totals.")

tab1, tab2, tab3, tab4 = st.tabs([
    "Asset Quality Overview", "Bank Comparison", "Financial Performance", "Sector Risk"
])

with tab1:
    left, right = st.columns(2)
    if {"Financial_Year", "Bank_Type", "Gross_NPA_Ratio"}.issubset(filtered.columns):
        trend = filtered.groupby(["Year_Start", "Financial_Year", "Bank_Type"], as_index=False)["Gross_NPA_Ratio"].mean()
        trend = trend.sort_values("Year_Start")
        fig = px.line(trend, x="Financial_Year", y="Gross_NPA_Ratio", color="Bank_Type",
                      markers=True, title="Average Gross NPA Ratio over Time",
                      labels={"Financial_Year":"Financial year", "Gross_NPA_Ratio":"Gross NPA ratio (%)", "Bank_Type":"Bank sector"})
        fig.update_layout(legend_title_text="Bank sector")
        left.plotly_chart(fig, use_container_width=True)
    if {"Financial_Year", "Bank_Type", "Net_NPA_Ratio"}.issubset(filtered.columns):
        trend = filtered.groupby(["Year_Start", "Financial_Year", "Bank_Type"], as_index=False)["Net_NPA_Ratio"].mean().sort_values("Year_Start")
        fig = px.line(trend, x="Financial_Year", y="Net_NPA_Ratio", color="Bank_Type",
                      markers=True, title="Average Net NPA Ratio over Time",
                      labels={"Financial_Year":"Financial year", "Net_NPA_Ratio":"Net NPA ratio (%)", "Bank_Type":"Bank sector"})
        right.plotly_chart(fig, use_container_width=True)

    if "Provision_Coverage_Ratio" in filtered.columns:
        pcr_year = filtered.groupby(["Year_Start", "Financial_Year", "Bank_Type"], as_index=False)["Provision_Coverage_Ratio"].mean().sort_values("Year_Start")
        fig = px.line(pcr_year, x="Financial_Year", y="Provision_Coverage_Ratio", color="Bank_Type", markers=True,
                      title="Provision Coverage Ratio over Time",
                      labels={"Financial_Year":"Financial year", "Provision_Coverage_Ratio":"Provision coverage ratio", "Bank_Type":"Bank sector"})
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    metric_options = [("Gross NPA ratio", "Gross_NPA_Ratio"), ("Net NPA ratio", "Net_NPA_Ratio"),
                      ("Provision coverage ratio", "Provision_Coverage_Ratio"), ("Net profit", "Net_Profit")]
    available_options = [(label, col) for label, col in metric_options if col in filtered.columns]
    if available_options:
        selected_label = st.selectbox("Metric to compare", [x[0] for x in available_options])
        metric = dict(available_options)[selected_label]
        bank_avg = filtered.groupby(["Bank_Name", "Bank_Type"], as_index=False)[metric].mean().dropna(subset=[metric])
        bank_avg = bank_avg.sort_values(metric, ascending=False)
        fig = px.bar(bank_avg, x=metric, y="Bank_Name", color="Bank_Type", orientation="h",
                     title=f"Bank comparison — {selected_label}",
                     labels={metric:selected_label, "Bank_Name":"Bank"})
        fig.update_layout(yaxis={"categoryorder":"total ascending"}, height=max(450, 28*len(bank_avg)))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(bank_avg.rename(columns={metric:selected_label}), use_container_width=True, hide_index=True)
    else:
        st.info("No supported bank-comparison metrics were found in the workbook.")

with tab3:
    possible = [("Net profit", "Net_Profit"), ("Return on Assets (ROA)", "Return_on_Assets"),
                ("Return on Equity (ROE)", "Return_on_Equity"), ("Capital adequacy ratio", "Capital_Adequacy_Ratio")]
    available = [(label, col) for label, col in possible if col in filtered.columns]
    if available:
        label = st.selectbox("Financial indicator", [x[0] for x in available])
        col = dict(available)[label]
        trend = filtered.groupby(["Year_Start", "Financial_Year", "Bank_Type"], as_index=False)[col].mean().sort_values("Year_Start")
        fig = px.line(trend, x="Financial_Year", y=col, color="Bank_Type", markers=True,
                      title=f"{label} over Time",
                      labels={"Financial_Year":"Financial year", col:label, "Bank_Type":"Bank sector"})
        st.plotly_chart(fig, use_container_width=True)
    if {"Gross_NPA_Ratio", "Net_Profit"}.issubset(filtered.columns):
        scatter = filtered.dropna(subset=["Gross_NPA_Ratio", "Net_Profit"])
        if not scatter.empty:
            fig = px.scatter(scatter, x="Gross_NPA_Ratio", y="Net_Profit", color="Bank_Type",
                             hover_name="Bank_Name", hover_data=["Financial_Year"],
                             title="Gross NPA Ratio vs Net Profit",
                             labels={"Gross_NPA_Ratio":"Gross NPA ratio (%)", "Net_Profit":"Net profit"})
            st.plotly_chart(fig, use_container_width=True)
    corr_cols = [c for c in ["Gross_NPA_Ratio","Net_NPA_Ratio","Return_on_Assets","Return_on_Equity","Net_Profit","Capital_Adequacy_Ratio","Provision_Coverage_Ratio"] if c in filtered.columns and filtered[c].nunique(dropna=True)>1]
    if len(corr_cols) >= 2:
        corr = filtered[corr_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                        title="Correlation between NPA and financial indicators")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    sector_map = {
        "Agriculture": ("Agriculture_Loans", "Agriculture_NPA"),
        "MSME": ("MSME_Loans", "MSME_NPA"),
        "Retail": ("Retail_Loans", "Retail_NPA"),
        "Personal Loans": ("Personal_Loans", "Personal_Loan_NPA"),
        "Corporate": ("Corporate_Loans", "Corporate_NPA"),
        "Industrial": ("Industrial_Loans", "Industrial_NPA"),
        "Priority Sector": ("Priority_Sector_Lending", "Priority_Sector_NPA"),
        "Housing": ("Housing_Loans", "Housing_Loan_NPA"),
        "Education": ("Education_Loans", "Education_Loan_NPA"),
        "Vehicle": ("Vehicle_Loans", "Vehicle_Loan_NPA"),
        "Credit Cards": ("Credit_Card_Outstanding", "Credit_Card_NPA"),
    }
    present = {name: pair for name, pair in sector_map.items() if pair[0] in filtered.columns and pair[1] in filtered.columns}
    if present:
        long_parts = []
        for sector, (loan_col, npa_col) in present.items():
            temp = filtered[["Bank_Name", "Bank_Type", "Financial_Year", "Year_Start", loan_col, npa_col]].copy()
            temp = temp.rename(columns={loan_col:"Exposure", npa_col:"Sector_NPA"})
            temp["Sector"] = sector
            temp["Exposure"] = pd.to_numeric(temp["Exposure"], errors="coerce")
            temp["Sector_NPA"] = pd.to_numeric(temp["Sector_NPA"], errors="coerce")
            long_parts.append(temp)
        sector_long = pd.concat(long_parts, ignore_index=True)
        sector_long = sector_long.dropna(subset=["Exposure", "Sector_NPA"])
        sector_long = sector_long[sector_long["Exposure"] > 0]
        sector_long["Sector_NPA_Ratio"] = sector_long["Sector_NPA"] / sector_long["Exposure"] * 100
        if not sector_long.empty:
            sector_year = sector_long.groupby(["Year_Start","Financial_Year","Bank_Type","Sector"], as_index=False).agg(
                Exposure=("Exposure","sum"), Sector_NPA=("Sector_NPA","sum"))
            sector_year["Sector_NPA_Ratio"] = sector_year["Sector_NPA"] / sector_year["Exposure"] * 100
            sector_year = sector_year.sort_values("Year_Start")
            c1, c2 = st.columns(2)
            sector_latest_year = sector_year["Year_Start"].max()
            latest_sector = sector_year[sector_year["Year_Start"] == sector_latest_year]
            latest_rank = latest_sector.groupby("Sector", as_index=False).agg(
                Exposure=("Exposure","sum"), Sector_NPA=("Sector_NPA","sum"))
            latest_rank["Sector_NPA_Ratio"] = latest_rank["Sector_NPA"] / latest_rank["Exposure"] * 100
            latest_rank = latest_rank.sort_values("Sector_NPA_Ratio", ascending=False)
            fig = px.bar(latest_rank, x="Sector_NPA_Ratio", y="Sector", orientation="h",
                         title=f"Sector NPA risk ranking — {latest_sector['Financial_Year'].iloc[0]}",
                         labels={"Sector_NPA_Ratio":"Sector NPA ratio (%)", "Sector":"Lending sector"})
            fig.update_layout(yaxis={"categoryorder":"total descending"})
            c1.plotly_chart(fig, use_container_width=True)
            sector_trend = sector_year.groupby(["Year_Start","Financial_Year","Sector"], as_index=False).agg(
                Exposure=("Exposure","sum"), Sector_NPA=("Sector_NPA","sum"))
            sector_trend["Sector_NPA_Ratio"] = sector_trend["Sector_NPA"] / sector_trend["Exposure"] * 100
            fig = px.line(sector_trend, x="Financial_Year", y="Sector_NPA_Ratio", color="Sector", markers=True,
                          title="Sector NPA trends",
                          labels={"Financial_Year":"Financial year","Sector_NPA_Ratio":"Sector NPA ratio (%)"})
            c2.plotly_chart(fig, use_container_width=True)
            pivot = sector_year.pivot_table(index="Sector", columns="Financial_Year", values="Sector_NPA_Ratio", aggfunc="mean")
            fig = px.imshow(pivot, text_auto=".2f", aspect="auto", color_continuous_scale="YlOrRd",
                            title="Sector risk heatmap", labels={"color":"NPA ratio (%)"})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(latest_rank.sort_values("Sector_NPA_Ratio", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Sector loan and NPA columns exist, but no valid positive exposure values were available after filtering.")
    else:
        st.info("The expected sector-level loan/NPA column pairs were not found in this workbook.")

with st.expander("View filtered data"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data as CSV", data=csv, file_name="npa_filtered_data.csv", mime="text/csv")

st.divider()
st.markdown(
    '<p class="small-note">Academic analysis dashboard. The figures reflect the supplied workbook and selected filters; '
    'they are descriptive, not investment or lending advice. Verify underlying data with authoritative sources before relying on it.</p>',
    unsafe_allow_html=True
)
