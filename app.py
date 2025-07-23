
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.image("logo.png", width=200)

st.title("CoachHub Forecast Model")

# Sidebar filters
st.sidebar.header("Filters")

# Currency selection
currency_symbol_map = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
currency = st.sidebar.selectbox("Select Currency", options=list(currency_symbol_map.keys()))
currency_symbol = currency_symbol_map[currency]

# Forecast model selection
model_option = st.sidebar.radio("Select Forecast Model", ["Model A", "Model B"])

# Confidence threshold
confidence_threshold = st.sidebar.slider("Minimum Model Confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.05)

# Forecast Category filter
forecast_categories = ["Pipeline", "Best Case", "Probable", "Commit"]
selected_categories = st.sidebar.multiselect("Forecast Categories", forecast_categories, default=forecast_categories)

# Model Strength filter
model_strengths = ["Weak", "Moderate", "Strong"]
selected_strengths = st.sidebar.multiselect("Model Strength", model_strengths, default=model_strengths)

# Load Excel data
@st.cache_data
def load_data(sheet_name):
    return pd.read_excel("CoachHub_Case_Study_Forecast_Example.xlsx", sheet_name=sheet_name)

if model_option == "Model A":
    data = load_data("Forecast Model A - Data")
else:
    data = load_data("Forecast Model B - Data")

# Apply filters
data = data[
    (data["Model Weighting"] >= confidence_threshold) &
    (data["Forecast Category"].isin(selected_categories)) &
    (data["Model Deal Strength"].str.strip().isin(selected_strengths))
]

# KPI Summary
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Opportunities", len(data))
with col2:
    st.metric("Total Pipeline Value", f"{currency_symbol}{data['Potential Amount'].sum():,.0f}")
with col3:
    st.metric("Model Forecast", f"{currency_symbol}{data['Model Amount'].sum():,.0f}")

# Bar chart: Forecast by Category
st.subheader("Forecast Value by Category")
category_chart = data.groupby("Forecast Category")["Model Amount"].sum().reset_index()
st.bar_chart(category_chart.set_index("Forecast Category"))

# Stacked bar chart: Rep by Forecast Category
st.subheader("Forecast by Sales Rep and Category")
rep_cat_data = data.pivot_table(index="Opportunity Owner", columns="Forecast Category", values="Model Amount", aggfunc="sum").fillna(0)
st.bar_chart(rep_cat_data)

# Bar chart: Potential vs Model by Category
st.subheader("Potential vs Forecast by Category")
comp_data = data.groupby("Forecast Category")[["Potential Amount", "Model Amount"]].sum().reset_index()
comp_data = comp_data.set_index("Forecast Category")
st.bar_chart(comp_data)

# Table Formatting
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

# AI Insights
st.subheader("AI Insights")
insights = []
numeric_data = pd.read_excel("CoachHub_Case_Study_Forecast_Example.xlsx", sheet_name="Forecast Model A - Data" if model_option == "Model A" else "Forecast Model B - Data")

# Reapply same filters on numeric values for insights
numeric_data = numeric_data[
    (numeric_data["Model Weighting"] >= confidence_threshold) &
    (numeric_data["Forecast Category"].isin(selected_categories)) &
    (numeric_data["Model Deal Strength"].str.strip().isin(selected_strengths))
]

if numeric_data["Model Amount"].sum() < numeric_data["Potential Amount"].sum() * 0.5:
    insights.append("⚠️ Forecasted amount is significantly lower than the pipeline value — consider reviewing weighting factors.")
if numeric_data["Model Weighting"].max() > 0.8:
    insights.append("✅ Some deals show high model confidence — these may be strong candidates for commit.")
if numeric_data["Forecast Category"].str.contains("Pipeline").sum() > len(numeric_data) / 2:
    insights.append("🔍 Majority of opportunities are still in pipeline — might be early in the sales cycle.")

if insights:
    for i in insights:
        st.write(i)
else:
    st.write("📈 No major anomalies detected. Forecast model looks balanced.")
