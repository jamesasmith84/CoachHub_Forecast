
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.markdown("<div style='text-align: center'><img src='logo.png' width='300'></div>", unsafe_allow_html=True)

st.title("CoachHub Forecast Model")

# Sidebar filters
st.sidebar.header("Filters")
currency_symbol_map = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
currency = st.sidebar.selectbox("Select Currency", options=list(currency_symbol_map.keys()))
currency_symbol = currency_symbol_map[currency]
model_option = st.sidebar.radio("Select Forecast Model", ["Model A", "Model B"])
confidence_threshold = st.sidebar.slider("Minimum Model Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
forecast_categories = ["Pipeline", "Best Case", "Probable", "Commit"]
selected_categories = st.sidebar.multiselect("Forecast Categories", forecast_categories, default=forecast_categories)
model_strengths = ["Weak", "Moderate", "Strong"]
selected_strengths = st.sidebar.multiselect("Model Strength", model_strengths, default=model_strengths)

# Load Excel data
@st.cache_data
def load_data(sheet_name):
    return pd.read_excel("CoachHub_Case_Study_Forecast_Example.xlsx", sheet_name=sheet_name)

sheet = "Forecast Model A - Data" if model_option == "Model A" else "Forecast Model B - Data"
data = load_data(sheet)

# Filters
data = data[
    (data["Model Weighting"] >= confidence_threshold) &
    (data["Forecast Category"].isin(selected_categories)) &
    (data["Model Deal Strength"].str.strip().isin(selected_strengths))
]

# AI Insights
st.subheader("AI Insights")
insights = []
total_potential = data["Potential Amount"].sum()
total_model = data["Model Amount"].sum()
if total_model < total_potential * 0.5:
    insights.append("⚠️ Forecasted amount is significantly lower than the pipeline value — consider reviewing weighting factors.")
if data["Model Weighting"].max() > 0.8:
    insights.append("✅ Some deals show high model confidence — these may be strong candidates for commit.")
if data["Forecast Category"].str.contains("Pipeline").sum() > len(data) / 2:
    insights.append("🔍 Majority of opportunities are still in pipeline — might be early in the sales cycle.")
if data["Close Date"].max() > pd.Timestamp.now() + pd.DateOffset(months=6):
    insights.append("🗓️ Several deals appear to be closing far in the future — consider pipeline hygiene.")

if insights:
    for insight in insights:
        st.write(insight)
else:
    st.write("📈 No major anomalies detected. Forecast model looks balanced.")

# KPI Summary
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Opportunities", len(data))
with col2:
    st.metric("Total Pipeline Value", f"{currency_symbol}{total_potential:,.0f}")
with col3:
    st.metric("Model Forecast", f"{currency_symbol}{total_model:,.0f}")

# Forecast by Category and Quarter
st.subheader("Forecast Value by Category and Quarter")
data["Quarter"] = pd.to_datetime(data["Close Date"]).dt.to_period("Q").astype(str)
cat_qtr = data.groupby(["Forecast Category", "Quarter"])["Model Amount"].sum().unstack().fillna(0)
st.bar_chart(cat_qtr.T)

# Potential vs Forecast by Category - side-by-side bars
st.subheader("Potential vs Forecast by Category")
cat_comp = data.groupby("Forecast Category")[["Potential Amount", "Model Amount"]].sum()
st.bar_chart(cat_comp)

# Line chart for % of Model Amount vs Potential
st.subheader("Forecast Accuracy by Category")
pct_chart = (cat_comp["Model Amount"] / cat_comp["Potential Amount"] * 100).round(1).rename("% Forecast Accuracy")
st.line_chart(pct_chart)

# Forecast by Rep and Category (stacked)
st.subheader("Forecast by Sales Rep and Category")
rep_cat = data.pivot_table(index="Opportunity Owner", columns="Forecast Category", values="Model Amount", aggfunc="sum").fillna(0)
st.bar_chart(rep_cat)

# Format table
st.subheader("Opportunity Detail")
percent_cols = [
    "Sales Rep Forecast Accuracy", "Model Weighting", "Age Weighting", "Probability",
    "Probability Weighting", "Forecast Category Weighting", "Push Count Weighting",
    "Sales Rep Accuracy Weighting"
]
for col in percent_cols:
    if col in data.columns:
        data[col] = (data[col] * 100).round(1).astype(str) + "%"

data["Potential Amount"] = data["Potential Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
data["Model Amount"] = data["Model Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")

st.dataframe(data)
