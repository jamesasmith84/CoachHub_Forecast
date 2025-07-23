
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.image("logo.png", width=200)

st.title("CoachHub Forecast Model")

# Currency selection
currency_symbol_map = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
currency = st.selectbox("Select Currency", options=list(currency_symbol_map.keys()))
currency_symbol = currency_symbol_map[currency]

# Load Excel data
@st.cache_data
def load_data(sheet_name):
    df = pd.read_excel("CoachHub_Case_Study_Forecast_Example.xlsx", sheet_name=sheet_name)
    return df

# Model toggle at top
model_option = st.radio("Select Forecast Model", ["Model A", "Model B"], horizontal=True)

if model_option == "Model A":
    data = load_data("Forecast Model A - Data")
else:
    data = load_data("Forecast Model B - Data")

# Model confidence threshold
confidence_threshold = st.slider("Minimum Model Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
filtered_data = data[data["Model Weighting"] >= confidence_threshold]

# KPI Summary
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Opportunities", len(filtered_data))
with col2:
    st.metric("Total Pipeline Value", f"{currency_symbol}{filtered_data['Potential Amount'].sum():,.0f}")
with col3:
    st.metric("Model Forecast", f"{currency_symbol}{filtered_data['Model Amount'].sum():,.0f}")

# Bar chart: Forecast by Category
st.subheader("Forecast Value by Category")
chart_data = filtered_data.groupby("Forecast Category")["Model Amount"].sum().reset_index()
st.bar_chart(chart_data.set_index("Forecast Category"))

# Chart: Potential vs. Model Amount
st.subheader("Potential vs. Forecast Value")
amounts_data = filtered_data[["Opportunity Name", "Potential Amount", "Model Amount"]].set_index("Opportunity Name")
st.bar_chart(amounts_data)

# Chart: Model Amount by Rep
st.subheader("Forecast by Sales Rep")
rep_chart = filtered_data.groupby("Opportunity Owner")["Model Amount"].sum().reset_index()
st.bar_chart(rep_chart.set_index("Opportunity Owner"))

# Format table
st.subheader("Opportunity Detail")
percent_cols = [
    "Sales Rep Forecast Accuracy", "Model Weighting", "Age Weighting", "Probability",
    "Probability Weighting", "Forecast Category Weighting", "Push Count Weighting",
    "Sales Rep Accuracy Weighting"
]
for col in percent_cols:
    if col in filtered_data.columns:
        filtered_data[col] = (filtered_data[col] * 100).round(1).astype(str) + "%"

# Add currency formatting
filtered_data["Potential Amount"] = filtered_data["Potential Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
filtered_data["Model Amount"] = filtered_data["Model Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")

st.dataframe(filtered_data)

# AI Insights
st.subheader("AI Insights")
insights = []

if filtered_data["Model Amount"].sum() < filtered_data["Potential Amount"].str.replace(currency_symbol, "").str.replace(",", "").astype(float).sum() * 0.5:
    insights.append("⚠️ Forecasted amount is significantly lower than the pipeline value — consider reviewing weighting factors.")
if filtered_data["Model Weighting"].astype(str).str.rstrip('%').astype(float).max() > 80:
    insights.append("✅ Some deals show high model confidence — these may be strong candidates for commit.")
if filtered_data["Forecast Category"].str.contains("Pipeline").sum() > len(filtered_data) / 2:
    insights.append("🔍 Majority of opportunities are still in pipeline — might be early in the sales cycle.")

if insights:
    for i in insights:
        st.write(i)
else:
    st.write("📈 No major anomalies detected. Forecast model looks balanced.")
