import os
from io import BytesIO
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="NPA Banking Intelligence", page_icon="🏦", layout="wide")
NAVY="#102A43"; TEAL="#14B8A6"; BLUE="#3B82F6"; AMBER="#F4B942"; RED="#E05260"; PALE="#F7F9FC"
st.markdown(f"""<style>
.stApp{{background:{PALE};color:{NAVY}}}
[data-testid="stSidebar"]{{background:{NAVY}}}[data-testid="stSidebar"] *{{color:white!important}}
.block-container{{max-width:1550px;padding-top:1.2rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #DCE6F0;padding:14px;border-radius:13px}}
h1,h2,h3{{color:{NAVY}}}
.hero{{background:linear-gradient(120deg,{NAVY},#243B53);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}}
.hero h1{{color:white}} .hero p{{color:#D9E6F2;margin-bottom:0}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🏦 NPA Banking Intelligence</h1><p>Historical Indian banking asset-quality analytics + interactive fictional loan-risk assessment</p></div>', unsafe_allow_html=True)

DATA_FILE = "NPA_Banking_Sector_India_Dataset (1).xlsx"
def load_history():
    if not os.path.exists(DATA_FILE):
        return None, f"Dataset file not found: {DATA_FILE}"
    try:
        return pd.read_excel(DATA_FILE, sheet_name="Master_Merged_Panel_Data"), None
    except Exception as exc:
        return None, str(exc)

def money(v):
    return "—" if pd.isna(v) else f"₹{v:,.0f}"
def pct(v):
    return "—" if pd.isna(v) else f"{v:.2f}%"
def emi(p, annual, months):
    r=annual/1200
    return p/months if r==0 else p*r*(1+r)**months/((1+r)**months-1)
def assess(c):
    income=float(c["Monthly income (₹)"]); debt=float(c["Existing monthly debt (₹)"])
    loan=float(c["Loan amount (₹)"]); rate=float(c["Interest rate (%)"]); months=int(c["Tenure (years)"])*12
    payment=emi(loan,rate,months); foir=(debt+payment)/income*100 if income else 100
    disposable=income-debt-payment; asset=float(c["Asset value (₹)"]); ltv=loan/asset*100 if asset>0 else np.nan
    points=0; flags=[]
    if foir>60: points+=3; flags.append("FOIR exceeds 60%")
    elif foir>45: points+=2; flags.append("FOIR is 45–60%")
    elif foir>35: points+=1; flags.append("FOIR is 35–45%")
    if disposable<10000: points+=2; flags.append("Low disposable income")
    elif disposable<20000: points+=1; flags.append("Moderate disposable income")
    score=int(c["Demo credit score"])
    if score<600: points+=3; flags.append("Demo credit score below 600")
    elif score<700: points+=1; flags.append("Demo credit score below 700")
    if not np.isnan(ltv):
        if ltv>90: points+=2; flags.append("LTV exceeds 90%")
        elif ltv>80: points+=1; flags.append("LTV is 80–90%")
    risk="High" if points>=5 else "Moderate" if points>=2 else "Lower"
    return {**c,"Estimated EMI (₹)":payment,"FOIR (%)":foir,
            "Existing-debt DTI (%)":debt/income*100 if income else 100,
            "Disposable income after EMI (₹)":disposable,"LTV (%)":ltv,
            "Demo risk category":risk,"Risk points":points,
            "Reason flags":"; ".join(flags) if flags else "No major flag under demo rules"}

if "applicants" not in st.session_state:
    st.session_state.applicants=[
    {"Applicant":"Applicant A","Monthly income (₹)":85000,"Existing monthly debt (₹)":8000,"Loan amount (₹)":1800000,"Interest rate (%)":9.0,"Tenure (years)":15,"Asset value (₹)":2400000,"Demo credit score":760},
    {"Applicant":"Applicant B","Monthly income (₹)":42000,"Existing monthly debt (₹)":12000,"Loan amount (₹)":1500000,"Interest rate (%)":10.5,"Tenure (years)":10,"Asset value (₹)":1700000,"Demo credit score":640},
    {"Applicant":"Applicant C","Monthly income (₹)":30000,"Existing monthly debt (₹)":9000,"Loan amount (₹)":900000,"Interest rate (%)":11.0,"Tenure (years)":7,"Asset value (₹)":1100000,"Demo credit score":590},
    {"Applicant":"Applicant D","Monthly income (₹)":125000,"Existing monthly debt (₹)":10000,"Loan amount (₹)":3000000,"Interest rate (%)":8.75,"Tenure (years)":20,"Asset value (₹)":4200000,"Demo credit score":810},
    {"Applicant":"Applicant E","Monthly income (₹)":55000,"Existing monthly debt (₹)":18000,"Loan amount (₹)":2200000,"Interest rate (%)":10.0,"Tenure (years)":12,"Asset value (₹)":2500000,"Demo credit score":690}]
applicants_df=pd.DataFrame([assess(c) for c in st.session_state.applicants])
hist, hist_error=load_history()
with st.sidebar:
    st.markdown("## Navigation")
    page=st.radio("Workspace",["Executive Overview","Asset Quality Overview","Bank Comparison","Financial Performance","Sector Risk","Loan Risk Simulator","Applicant Comparison","Methodology"])
    st.markdown("---")
    st.caption("Historical workbook loads automatically from the app folder.")
    if hist is not None: st.success(f"Historical records loaded: {len(hist):,}")
    else: st.warning(hist_error)

def applicant_metrics(df):
    a,b,c,d,e=st.columns(5)
    a.metric("Applications",len(df)); b.metric("High-risk flags",int((df["Demo risk category"]=="High").sum()))
    c.metric("Moderate-risk flags",int((df["Demo risk category"]=="Moderate").sum()))
    d.metric("Average FOIR",f'{df["FOIR (%)"].mean():.1f}%')
    e.metric("Simulated exposure",f'₹{df["Loan amount (₹)"].sum():,.0f}')

def risk_chart(df, metric):
    fig=px.bar(df,x="Applicant",y=metric,color="Demo risk category",text_auto=".1f",
       color_discrete_map={"Lower":TEAL,"Moderate":AMBER,"High":RED},title=metric)
    fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY,legend_title_text="Demo risk")
    return fig

if page=="Executive Overview":
    st.subheader("Executive overview")
    st.markdown("### Historical banking portfolio")
    if hist is None:
        st.error(f"Historical data could not load. {hist_error}")
    else:
        gross=pd.to_numeric(hist["Gross_NPA_Ratio"],errors="coerce").mean()
        net=pd.to_numeric(hist["Net_NPA_Ratio"],errors="coerce").mean()
        pcr=pd.to_numeric(hist["Provision_Coverage_Ratio"],errors="coerce").mean()
        a,b,c,d=st.columns(4)
        a.metric("Average Gross NPA ratio",pct(gross)); b.metric("Average Net NPA ratio",pct(net))
        c.metric("Average Provision Coverage",pct(pcr)); d.metric("Bank-year records",f"{len(hist):,}")
        trend=hist.groupby("Financial_Year",as_index=False)[["Gross_NPA_Ratio","Net_NPA_Ratio"]].mean()
        fig=px.line(trend,x="Financial_Year",y=["Gross_NPA_Ratio","Net_NPA_Ratio"],markers=True,title="Historical Gross and Net NPA trend",color_discrete_sequence=[BLUE,TEAL])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY)
        st.plotly_chart(fig,use_container_width=True)
    st.divider()
    st.markdown("### Fictional applicant portfolio"); applicant_metrics(applicants_df)
    a,b=st.columns(2)
    with a:
        counts=applicants_df["Demo risk category"].value_counts().reindex(["Lower","Moderate","High"],fill_value=0).rename_axis("Risk category").reset_index(name="Applicants")
        fig=px.pie(counts,names="Risk category",values="Applicants",hole=.58,color="Risk category",color_discrete_map={"Lower":TEAL,"Moderate":AMBER,"High":RED},title="Applicant risk mix")
        fig.update_layout(paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
    with b: st.plotly_chart(risk_chart(applicants_df,"FOIR (%)"),use_container_width=True)
    st.dataframe(applicants_df[["Applicant","Loan amount (₹)","Estimated EMI (₹)","FOIR (%)","Disposable income after EMI (₹)","Demo risk category"]].round(2),use_container_width=True,hide_index=True)
    st.info("Historical bank NPA measures and the five fictional applicant assessments are separate analyses. Demo applicant flags are not actual NPAs or a bank default-rate estimate.")

elif page=="Asset Quality Overview":
    st.subheader("Asset Quality Overview")
    if hist is None: st.error(hist_error)
    else:
        typ_opts=sorted(hist["Bank_Type"].dropna().astype(str).unique())
        years=sorted(hist["Financial_Year"].dropna().astype(str).unique())
        banks=sorted(hist["Bank_Name"].dropna().astype(str).unique())
        c1,c2,c3=st.columns(3)
        sel_types=c1.multiselect("Bank type",typ_opts,default=typ_opts)
        sel_years=c2.multiselect("Financial years",years,default=years)
        sel_banks=c3.multiselect("Banks (optional)",banks,default=[])
        d=hist[hist["Bank_Type"].astype(str).isin(sel_types)&hist["Financial_Year"].astype(str).isin(sel_years)]
        if sel_banks: d=d[d["Bank_Name"].astype(str).isin(sel_banks)]
        a,b,c,dcol=st.columns(4)
        a.metric("Average Gross NPA",pct(pd.to_numeric(d["Gross_NPA_Ratio"],errors="coerce").mean()))
        b.metric("Average Net NPA",pct(pd.to_numeric(d["Net_NPA_Ratio"],errors="coerce").mean()))
        c.metric("Average PCR",pct(pd.to_numeric(d["Provision_Coverage_Ratio"],errors="coerce").mean()))
        dcol.metric("Records",len(d))
        trend=d.groupby(["Financial_Year","Bank_Type"],as_index=False)[["Gross_NPA_Ratio","Net_NPA_Ratio"]].mean()
        a,b=st.columns(2)
        with a:
            fig=px.line(trend,x="Financial_Year",y="Gross_NPA_Ratio",color="Bank_Type",markers=True,title="Gross NPA ratio trend",color_discrete_sequence=[BLUE,TEAL,AMBER])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.line(trend,x="Financial_Year",y="Net_NPA_Ratio",color="Bank_Type",markers=True,title="Net NPA ratio trend",color_discrete_sequence=[TEAL,BLUE,AMBER])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        st.subheader("NPA stock and asset quality components")
        c1,c2=st.columns(2)
        stock=d.groupby("Financial_Year",as_index=False)[["Gross_NPA","Net_NPA","Fresh_Slippages","Write_Offs"]].sum()
        with c1:
            fig=px.bar(stock,x="Financial_Year",y=["Gross_NPA","Net_NPA"],barmode="group",title="Gross and net NPA amount",color_discrete_sequence=[BLUE,TEAL])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        with c2:
            fig=px.line(stock,x="Financial_Year",y=["Fresh_Slippages","Write_Offs"],markers=True,title="Fresh slippages and write-offs",color_discrete_sequence=[AMBER,RED])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(d,use_container_width=True,hide_index=True)

elif page=="Bank Comparison":
    st.subheader("Bank Comparison")
    if hist is None: st.error(hist_error)
    else:
        years=sorted(hist["Financial_Year"].dropna().astype(str).unique())
        types=sorted(hist["Bank_Type"].dropna().astype(str).unique())
        a,b=st.columns(2); year=a.selectbox("Financial year",years,index=len(years)-1); typ=b.multiselect("Bank type",types,default=types)
        d=hist[(hist["Financial_Year"].astype(str)==year)&hist["Bank_Type"].astype(str).isin(typ)].copy()
        d["Gross_NPA_Ratio"]=pd.to_numeric(d["Gross_NPA_Ratio"],errors="coerce")
        d=d.sort_values("Gross_NPA_Ratio",ascending=True)
        fig=px.bar(d,x="Gross_NPA_Ratio",y="Bank_Name",color="Bank_Type",orientation="h",title=f"Gross NPA ratio by bank — {year}",color_discrete_sequence=[BLUE,TEAL,AMBER])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        fig=px.scatter(d,x="Gross_NPA_Ratio",y="Net_NPA_Ratio",size="Total_Advances",color="Bank_Type",hover_name="Bank_Name",title="Gross vs net NPA ratio (bubble size = total advances)",color_discrete_sequence=[BLUE,TEAL,AMBER])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(d[["Bank_Name","Bank_Type","Gross_NPA_Ratio","Net_NPA_Ratio","Provision_Coverage_Ratio","Total_Advances"]],use_container_width=True,hide_index=True)

elif page=="Financial Performance":
    st.subheader("Financial Performance")
    if hist is None: st.error(hist_error)
    else:
        types=sorted(hist["Bank_Type"].dropna().astype(str).unique()); years=sorted(hist["Financial_Year"].dropna().astype(str).unique())
        a,b=st.columns(2); sel_types=a.multiselect("Bank type",types,default=types); sel_years=b.multiselect("Financial years",years,default=years)
        d=hist[hist["Bank_Type"].astype(str).isin(sel_types)&hist["Financial_Year"].astype(str).isin(sel_years)]
        trend=d.groupby("Financial_Year",as_index=False)[["Net_Profit","Operating_Profit","Net_Interest_Income"]].sum()
        a,b=st.columns(2)
        with a:
            fig=px.line(trend,x="Financial_Year",y=["Net_Profit","Operating_Profit"],markers=True,title="Net profit and operating profit",color_discrete_sequence=[TEAL,BLUE])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.line(trend,x="Financial_Year",y="Net_Interest_Income",markers=True,title="Net interest income trend",color_discrete_sequence=[BLUE])
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        ratios=d.groupby("Financial_Year",as_index=False)[["Return_on_Assets","Return_on_Equity","Capital_Adequacy_Ratio","Cost_to_Income_Ratio"]].mean()
        fig=px.line(ratios,x="Financial_Year",y=["Return_on_Assets","Return_on_Equity","Capital_Adequacy_Ratio","Cost_to_Income_Ratio"],markers=True,title="Profitability, capital and efficiency ratios",color_discrete_sequence=[TEAL,BLUE,AMBER,RED])
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(d,use_container_width=True,hide_index=True)

elif page=="Sector Risk":
    st.subheader("Sector Risk")
    if hist is None: st.error(hist_error)
    else:
        sector_pairs=[("Agriculture","Agriculture_Loans","Agriculture_NPA"),("MSME","MSME_Loans","MSME_NPA"),("Retail","Retail_Loans","Retail_NPA"),("Personal loans","Personal_Loans","Personal_Loan_NPA"),("Corporate","Corporate_Loans","Corporate_NPA"),("Industrial","Industrial_Loans","Industrial_NPA"),("Housing","Housing_Loans","Housing_Loan_NPA"),("Education","Education_Loans","Education_Loan_NPA"),("Vehicle","Vehicle_Loans","Vehicle_Loan_NPA"),("Credit cards","Credit_Card_Outstanding","Credit_Card_NPA")]
        years=sorted(hist["Financial_Year"].dropna().astype(str).unique()); sel_year=st.selectbox("Financial year for sector ranking",years,index=len(years)-1)
        d=hist[hist["Financial_Year"].astype(str)==sel_year]
        rows=[]
        for name,loans,npa in sector_pairs:
            exposure=pd.to_numeric(d[loans],errors="coerce").sum(min_count=1)
            bad=pd.to_numeric(d[npa],errors="coerce").sum(min_count=1)
            rows.append({"Sector":name,"Loan exposure":exposure,"NPA amount":bad,"Sector NPA ratio (%)":bad/exposure*100 if pd.notna(exposure) and exposure else np.nan})
        sec=pd.DataFrame(rows).dropna(subset=["Sector NPA ratio (%)"]).sort_values("Sector NPA ratio (%)")
        a,b=st.columns(2)
        with a:
            fig=px.bar(sec,x="Sector NPA ratio (%)",y="Sector",orientation="h",color="Sector NPA ratio (%)",color_continuous_scale=["#B7F7E8",TEAL,RED],title=f"Sector NPA ratio ranking — {sel_year}")
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        with b:
            trendrows=[]
            for yr in years:
                sub=hist[hist["Financial_Year"].astype(str)==yr]
                for name,loans,npa in sector_pairs:
                    exposure=pd.to_numeric(sub[loans],errors="coerce").sum(min_count=1)
                    bad=pd.to_numeric(sub[npa],errors="coerce").sum(min_count=1)
                    if pd.notna(exposure) and exposure:
                        trendrows.append({"Financial_Year":yr,"Sector":name,"Sector NPA ratio (%)":bad/exposure*100})
            trend=pd.DataFrame(trendrows)
            chosen=st.multiselect("Sectors for trend",sec["Sector"].tolist(),default=sec["Sector"].head(4).tolist())
            fig=px.line(trend[trend["Sector"].isin(chosen)],x="Financial_Year",y="Sector NPA ratio (%)",color="Sector",markers=True,title="Sector NPA ratio trend",color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",font_color=NAVY); st.plotly_chart(fig,use_container_width=True)
        st.dataframe(sec,use_container_width=True,hide_index=True)
        st.caption("Sector NPA ratio is calculated as aggregate sector NPA divided by aggregate sector loan exposure × 100.")

elif page=="Loan Risk Simulator":
    st.subheader("Loan Risk Simulator — fictional applicants")
    names=[c["Applicant"] for c in st.session_state.applicants]; selected=st.selectbox("Applicant",names)
    ix=names.index(selected); c=st.session_state.applicants[ix]
    with st.form("loan_form"):
        x,y,z=st.columns(3)
        name=x.text_input("Applicant label",c["Applicant"])
        income=y.number_input("Monthly net income (₹)",5000,10000000,int(c["Monthly income (₹)"]),1000)
        debt=z.number_input("Existing monthly EMI/debt (₹)",0,10000000,int(c["Existing monthly debt (₹)"]),500)
        x,y,z=st.columns(3)
        loan=x.number_input("Proposed loan amount (₹)",10000,100000000,int(c["Loan amount (₹)"]),10000)
        rate=y.number_input("Annual interest rate (%)",0.0,40.0,float(c["Interest rate (%)"]),0.25)
        tenure_opts=[1,2,3,5,7,10,12,15,20,25,30]
        tenure=z.selectbox("Tenure (years)",tenure_opts,index=tenure_opts.index(int(c["Tenure (years)"])))
        x,y=st.columns(2)
        asset=x.number_input("Asset value for LTV (₹)",0,100000000,int(c["Asset value (₹)"]),10000)
        credit=y.slider("Demo credit score",300,900,int(c["Demo credit score"]),10)
        submitted=st.form_submit_button("Save and recalculate",type="primary")
    if submitted:
        st.session_state.applicants[ix]={"Applicant":name,"Monthly income (₹)":income,"Existing monthly debt (₹)":debt,"Loan amount (₹)":loan,"Interest rate (%)":rate,"Tenure (years)":tenure,"Asset value (₹)":asset,"Demo credit score":credit}
        st.rerun()
    current=assess({"Applicant":name,"Monthly income (₹)":income,"Existing monthly debt (₹)":debt,"Loan amount (₹)":loan,"Interest rate (%)":rate,"Tenure (years)":tenure,"Asset value (₹)":asset,"Demo credit score":credit})
    a,b,c,d=st.columns(4); a.metric("Estimated EMI",money(current["Estimated EMI (₹)"])); b.metric("FOIR",pct(current["FOIR (%)"]))
    c.metric("Disposable income",money(current["Disposable income after EMI (₹)"])); d.metric("LTV","N/A" if np.isnan(current["LTV (%)"]) else pct(current["LTV (%)"]))
    color={"Lower":TEAL,"Moderate":AMBER,"High":RED}[current["Demo risk category"]]
    st.markdown(f'<div style="background:white;padding:16px;border-left:6px solid {color};border-radius:10px"><b>Demo risk flag: {current["Demo risk category"]}</b><br>{current["Reason flags"]}</div>',unsafe_allow_html=True)
    st.caption("Illustrative classroom rules, not RBI rules or a validated credit-scoring model.")

elif page=="Applicant Comparison":
    st.subheader("Applicant Comparison & Reports"); applicant_metrics(applicants_df)
    cats=st.multiselect("Risk categories",["Lower","Moderate","High"],default=["Lower","Moderate","High"])
    data=applicants_df[applicants_df["Demo risk category"].isin(cats)]
    metric=st.selectbox("Metric to compare",["FOIR (%)","Estimated EMI (₹)","Disposable income after EMI (₹)","LTV (%)","Loan amount (₹)","Demo credit score"])
    st.plotly_chart(risk_chart(data,metric),use_container_width=True)
    st.dataframe(data,use_container_width=True,hide_index=True)
    st.download_button("Download CSV",data.to_csv(index=False).encode("utf-8"),"loan_risk_assessment.csv","text/csv")
    bio=BytesIO()
    with pd.ExcelWriter(bio,engine="openpyxl") as writer: data.to_excel(writer,index=False)
    st.download_button("Download Excel",bio.getvalue(),"loan_risk_assessment.xlsx")

else:
    st.subheader("Methodology & interpretation")
    st.markdown("""**Historical NPA analysis:** the workbook is loaded automatically from the repository. Filters and visualizations operate on the bank-year records. Sector ratios are computed as aggregated sector NPA divided by aggregated sector loan exposure, multiplied by 100.

**EMI** uses the standard fixed-rate amortising-loan formula. **FOIR** = (existing monthly debt + proposed EMI) / monthly net income × 100. **Existing-debt DTI** = existing debt / income × 100. **Disposable income** = income − existing debt − proposed EMI. **LTV** = proposed loan amount / entered asset value × 100.

**Risk flags:** Lower / Moderate / High are rule-based demonstration labels using FOIR, disposable income, demo credit score and LTV. They are not official lending policy, a trained ML model, or a reliable default prediction. All five applicants are fictional. Applicant flags and historical bank NPA statistics are separate measures; five sample applicants cannot estimate a bank's real NPA rate.

**Interpretation:** the simulator demonstrates how repayment burden, disposable income, collateral coverage and a sample credit score can help flag applications for additional review. Historical NPA analysis complements this by showing trends across banks, years, financial performance and lending sectors. Neither view alone guarantees whether a specific loan will default.""")
st.divider()
st.caption("NPA Banking Intelligence • Academic demonstration • Navy / white / teal palette • Not for real lending decisions")
