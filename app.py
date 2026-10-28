import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from io import BytesIO

st.set_page_config(page_title="NPA Banking Intelligence",page_icon="🏦",layout="wide")
NAVY="#102A43"; TEAL="#14B8A6"; BLUE="#3B82F6"; AMBER="#F4B942"; RED="#E05260"
st.markdown(f"""<style>
.stApp{{background:#F7F9FC;color:{NAVY}}}
[data-testid="stSidebar"]{{background:{NAVY}}}[data-testid="stSidebar"] *{{color:white!important}}
.block-container{{max-width:1500px;padding-top:1.5rem}}
div[data-testid="stMetric"]{{background:white;border:1px solid #DCE6F0;padding:15px;border-radius:14px}}
h1,h2,h3{{color:{NAVY}}}
.hero{{background:linear-gradient(120deg,{NAVY},#243B53);padding:24px 28px;border-radius:18px;color:white;margin-bottom:18px}}
.hero h1{{color:white}} .hero p{{color:#D9E6F2;margin-bottom:0}}
</style>""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🏦 NPA Banking Intelligence</h1><p>Historical asset quality + interactive five-applicant loan risk simulation</p></div>',unsafe_allow_html=True)

def emi(p,annual,months):
    r=annual/1200
    return p/months if r==0 else p*r*(1+r)**months/((1+r)**months-1)
def assess(c):
    income=float(c["Monthly income (₹)"]); debt=float(c["Existing monthly debt (₹)"])
    loan=float(c["Loan amount (₹)"]); rate=float(c["Interest rate (%)"]); months=int(c["Tenure (years)"])*12
    e=emi(loan,rate,months); foir=(debt+e)/income*100 if income else 100
    disposable=income-debt-e; asset=float(c["Asset value (₹)"]); ltv=loan/asset*100 if asset>0 else np.nan
    points=0; flags=[]
    if foir>60: points+=3; flags.append("FOIR exceeds 60%")
    elif foir>45: points+=2; flags.append("FOIR is 45–60%")
    elif foir>35: points+=1; flags.append("FOIR is 35–45%")
    if disposable<10000: points+=2; flags.append("Low disposable income")
    elif disposable<20000: points+=1; flags.append("Moderate disposable income")
    if int(c["Demo credit score"])<600: points+=3; flags.append("Demo credit score below 600")
    elif int(c["Demo credit score"])<700: points+=1; flags.append("Demo credit score below 700")
    if not np.isnan(ltv):
        if ltv>90: points+=2; flags.append("LTV exceeds 90%")
        elif ltv>80: points+=1; flags.append("LTV is 80–90%")
    risk="High" if points>=5 else "Moderate" if points>=2 else "Lower"
    return {**c,"Estimated EMI (₹)":e,"FOIR (%)":foir,"Existing-debt DTI (%)":debt/income*100 if income else 100,
            "Disposable income after EMI (₹)":disposable,"LTV (%)":ltv,"Demo risk category":risk,
            "Risk points":points,"Reason flags":"; ".join(flags) if flags else "No major flag under demo rules"}

if "applicants" not in st.session_state:
    st.session_state.applicants=[
    {"Applicant":"Applicant A","Monthly income (₹)":85000,"Existing monthly debt (₹)":8000,"Loan amount (₹)":1800000,"Interest rate (%)":9.0,"Tenure (years)":15,"Asset value (₹)":2400000,"Demo credit score":760},
    {"Applicant":"Applicant B","Monthly income (₹)":42000,"Existing monthly debt (₹)":12000,"Loan amount (₹)":1500000,"Interest rate (%)":10.5,"Tenure (years)":10,"Asset value (₹)":1700000,"Demo credit score":640},
    {"Applicant":"Applicant C","Monthly income (₹)":30000,"Existing monthly debt (₹)":9000,"Loan amount (₹)":900000,"Interest rate (%)":11.0,"Tenure (years)":7,"Asset value (₹)":1100000,"Demo credit score":590},
    {"Applicant":"Applicant D","Monthly income (₹)":125000,"Existing monthly debt (₹)":10000,"Loan amount (₹)":3000000,"Interest rate (%)":8.75,"Tenure (years)":20,"Asset value (₹)":4200000,"Demo credit score":810},
    {"Applicant":"Applicant E","Monthly income (₹)":55000,"Existing monthly debt (₹)":18000,"Loan amount (₹)":2200000,"Interest rate (%)":10.0,"Tenure (years)":12,"Asset value (₹)":2500000,"Demo credit score":690}]
with st.sidebar:
    st.markdown("## Navigation")
    page=st.radio("Workspace",["Executive Overview","Loan Risk Simulator","Applicant Comparison","Historical NPA Intelligence","Methodology"])
    st.markdown("---")
    st.markdown("### Historical data")
    uploaded=st.file_uploader("Upload original NPA workbook/CSV",type=["xlsx","xls","csv"])
cases=[assess(c) for c in st.session_state.applicants]; df=pd.DataFrame(cases)
def metrics():
    a,b,c,d,e=st.columns(5)
    a.metric("Applications",len(df)); b.metric("High-risk flags",int((df["Demo risk category"]=="High").sum()))
    c.metric("Moderate-risk flags",int((df["Demo risk category"]=="Moderate").sum()))
    d.metric("Average FOIR",f'{df["FOIR (%)"].mean():.1f}%')
    e.metric("Simulated exposure",f'₹{df["Loan amount (₹)"].sum():,.0f}')
if page=="Executive Overview":
    st.subheader("Portfolio snapshot"); metrics()
    a,b=st.columns(2)
    with a:
        counts=df["Demo risk category"].value_counts().reindex(["Lower","Moderate","High"],fill_value=0).rename_axis("Risk category").reset_index(name="Applicants")
        fig=px.pie(counts,names="Risk category",values="Applicants",hole=.58,color="Risk category",color_discrete_map={"Lower":TEAL,"Moderate":AMBER,"High":RED},title="Applicant risk mix")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.bar(df,x="Applicant",y="FOIR (%)",color="Demo risk category",text_auto=".1f",color_discrete_map={"Lower":TEAL,"Moderate":AMBER,"High":RED},title="Repayment pressure (FOIR)")
        fig.add_hline(y=45,line_dash="dash",line_color=AMBER,annotation_text="45% demo review threshold")
        st.plotly_chart(fig,use_container_width=True)
    st.subheader("Applicant review queue")
    st.dataframe(df[["Applicant","Loan amount (₹)","Estimated EMI (₹)","FOIR (%)","Disposable income after EMI (₹)","Demo risk category"]].round(2),use_container_width=True,hide_index=True)
    st.info("Fictional applicants and illustrative rules only. These flags do not establish that a loan is or will become an NPA.")
elif page=="Loan Risk Simulator":
    st.subheader("Edit a fictional applicant")
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
        tenure=z.selectbox("Tenure (years)",[1,2,3,5,7,10,12,15,20,25,30],[1,2,3,5,7,10,12,15,20,25,30].index(int(c["Tenure (years)"])))
        x,y=st.columns(2)
        asset=x.number_input("Asset value for LTV (₹)",0,100000000,int(c["Asset value (₹)"]),10000)
        credit=y.slider("Demo credit score",300,900,int(c["Demo credit score"]),10)
        submitted=st.form_submit_button("Recalculate assessment",type="primary")
    if submitted:
        st.session_state.applicants[ix]={"Applicant":name,"Monthly income (₹)":income,"Existing monthly debt (₹)":debt,"Loan amount (₹)":loan,"Interest rate (%)":rate,"Tenure (years)":tenure,"Asset value (₹)":asset,"Demo credit score":credit}
        st.rerun()
    current=assess({"Applicant":name,"Monthly income (₹)":income,"Existing monthly debt (₹)":debt,"Loan amount (₹)":loan,"Interest rate (%)":rate,"Tenure (years)":tenure,"Asset value (₹)":asset,"Demo credit score":credit})
    a,b,c,d=st.columns(4); a.metric("Estimated EMI",f'₹{current["Estimated EMI (₹)"]:,.0f}'); b.metric("FOIR",f'{current["FOIR (%)"]:.1f}%')
    c.metric("Disposable income",f'₹{current["Disposable income after EMI (₹)"]:,.0f}'); d.metric("LTV","N/A" if np.isnan(current["LTV (%)"]) else f'{current["LTV (%)"]:.1f}%')
    color={"Lower":TEAL,"Moderate":AMBER,"High":RED}[current["Demo risk category"]]
    st.markdown(f'<div style="background:white;padding:16px;border-left:6px solid {color};border-radius:10px"><b>Demo risk flag: {current["Demo risk category"]}</b><br>{current["Reason flags"]}</div>',unsafe_allow_html=True)
    st.caption("Illustrative classroom rules, not RBI rules or a validated credit-scoring model.")
elif page=="Applicant Comparison":
    st.subheader("Compare all five applications"); metrics()
    cats=st.multiselect("Risk categories",["Lower","Moderate","High"],default=["Lower","Moderate","High"])
    data=df[df["Demo risk category"].isin(cats)]
    metric=st.selectbox("Metric",["FOIR (%)","Estimated EMI (₹)","Disposable income after EMI (₹)","LTV (%)","Loan amount (₹)"])
    fig=px.bar(data,x="Applicant",y=metric,color="Demo risk category",text_auto=".1f",color_discrete_map={"Lower":TEAL,"Moderate":AMBER,"High":RED})
    st.plotly_chart(fig,use_container_width=True); st.dataframe(data,use_container_width=True,hide_index=True)
    st.download_button("Download CSV",data.to_csv(index=False).encode(), "loan_risk_assessment.csv","text/csv")
    bio=BytesIO()
    with pd.ExcelWriter(bio,engine="openpyxl") as writer:data.to_excel(writer,index=False)
    st.download_button("Download Excel",bio.getvalue(),"loan_risk_assessment.xlsx")
elif page=="Historical NPA Intelligence":
    st.subheader("Historical NPA intelligence")
    if uploaded is None:
        st.warning("Upload the original dataset in the sidebar to restore historical bank/year charts. The loan simulator works independently.")
        st.write("Keep your existing Excel workbook (covering FY 2018–19 to FY 2024–25) available for this section.")
    else:
        try: hist=pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
        except Exception as ex: st.error(f"Could not read workbook: {ex}"); hist=None
        if hist is not None:
            def col(candidates):
                norm={str(x).lower().replace(" ","_"):x for x in hist.columns}
                for v in candidates:
                    if v.lower().replace(" ","_") in norm:return norm[v.lower().replace(" ","_")]
                for x in hist.columns:
                    if any(v.lower().replace(" ","_") in str(x).lower().replace(" ","_") for v in candidates):return x
                return None
            bank=col(["Bank_Name","Bank Name","Bank"]); typ=col(["Bank_Type","Bank Type"]); year=col(["Financial_Year","Financial Year","Year"])
            gross=col(["Gross_NPA_Ratio","Gross NPA Ratio","Gross NPA"]); net=col(["Net_NPA_Ratio","Net NPA Ratio","Net NPA"])
            st.caption(f"Loaded {len(hist)} records from {uploaded.name}")
            if typ:
                opts=sorted(hist[typ].dropna().astype(str).unique()); sel=st.multiselect("Bank sector",opts,default=opts); hist=hist[hist[typ].astype(str).isin(sel)]
            if bank:
                opts=sorted(hist[bank].dropna().astype(str).unique()); sel=st.multiselect("Banks (optional)",opts,default=[]); hist=hist[hist[bank].astype(str).isin(sel)] if sel else hist
            if year:
                opts=sorted(hist[year].dropna().astype(str).unique()); sel=st.multiselect("Financial years",opts,default=opts); hist=hist[hist[year].astype(str).isin(sel)]
            a,b=st.columns(2)
            if gross: a.metric("Average Gross NPA",f'{pd.to_numeric(hist[gross],errors="coerce").mean():.2f}%')
            if net: b.metric("Average Net NPA",f'{pd.to_numeric(hist[net],errors="coerce").mean():.2f}%')
            if year and gross:
                hist[gross]=pd.to_numeric(hist[gross],errors="coerce")
                trend=hist.groupby([year]+([typ] if typ else []),as_index=False)[gross].mean()
                st.plotly_chart(px.line(trend,x=year,y=gross,color=typ if typ else None,markers=True,title="Average Gross NPA ratio over time",color_discrete_sequence=[BLUE,TEAL]),use_container_width=True)
            if bank and gross:
                comp=hist.groupby([bank]+([typ] if typ else []),as_index=False)[gross].mean().sort_values(gross)
                st.plotly_chart(px.bar(comp,x=gross,y=bank,color=typ if typ else None,orientation="h",title="Bank comparison — Gross NPA ratio",color_discrete_sequence=[BLUE,TEAL]),use_container_width=True)
            with st.expander("Preview filtered source data"):st.dataframe(hist,use_container_width=True,hide_index=True)
else:
    st.subheader("Methodology & interpretation")
    st.markdown("""**EMI** uses the standard fixed-rate amortising-loan formula. **FOIR** = (existing monthly debt + proposed EMI) / monthly net income × 100. **Existing-debt DTI** = existing debt / income × 100. **Disposable income** = income − existing debt − proposed EMI. **LTV** = loan amount / entered asset value × 100.

**Risk flags:** Lower / Moderate / High are rule-based demonstration labels using FOIR, disposable income, demo credit score and LTV. They are not official lending policy, a trained ML model, or a reliable default prediction. The five applicants are fictional. Applicant flags and historical bank NPA statistics are separate measures; five sample applicants cannot estimate a bank's real NPA rate.

**Presentation conclusion:** The simulator demonstrates how repayment burden, disposable income, collateral coverage and a sample credit score can help flag applications for additional review. Historical NPA analysis complements this by showing trends across banks and years. Neither view alone guarantees whether a specific loan will default.""")
st.markdown("---")
st.caption("NPA Banking Intelligence • Academic demo • Navy / white / teal palette • Not for real lending decisions")
