
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.title("CoachHub Forecast Model")

# Sidebar filters
st.sidebar.header("Filters")
currency_symbol_map = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
currency = st.sidebar.selectbox("Select Currency", options=list(currency_symbol_map.keys()))
currency_symbol = currency_symbol_map[currency]

# Model selection in main view
model_option = st.radio("Select Forecast Model", ["Model A - Balanced", "Model B - Probability/Forecast Category Weighted"], horizontal=True)
confidence_threshold = st.sidebar.slider("Minimum Model Confidence", 0.0, 1.0, 0.0, 0.05)
forecast_categories = ["Pipeline", "Best Case", "Probable", "Commit"]
selected_categories = st.sidebar.multiselect("Forecast Categories", forecast_categories, default=forecast_categories)
model_strengths = ["Weak", "Moderate", "Strong"]
selected_strengths = st.sidebar.multiselect("Model Strength", model_strengths, default=model_strengths)

@st.cache_data
def load_data(sheet_name):
    return pd.read_excel("CoachHub Case Study Forecast Example.xlsx", sheet_name=sheet_name)

sheet = "Forecast Model A - Data" if "Model A" in model_option else "Forecast Model B - Data"
data = load_data(sheet)

# Ensure 'Quarter' column exists
if "Quarter" not in data.columns and "Close Date" in data.columns:
    data["Close Date"] = pd.to_datetime(data["Close Date"], errors='coerce')
    data["Quarter"] = data["Close Date"].dt.to_period("Q").astype(str)


# Apply filters
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
    st.write("📈 No major anomalies detected. Model Amount looks balanced.")

st.subheader("Opportunity Detail")
percent_cols = [c for c in data.columns if "Weighting" in c or "Accuracy" in c or "Probability" in c]
for col in percent_cols:
    if col in data.columns and data[col].dtype != object:
        data[col] = (data[col] * 100).round(1).astype(str) + "%"

data["Potential Amount"] = data["Potential Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
data["Model Amount"] = data["Model Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
st.dataframe(data)

# Line chart: Opportunity Count per Quarter
st.subheader("Opportunity Count by Quarter")
quarter_counts = data["Quarter"].value_counts().sort_index()
fig_line, ax_line = plt.subplots(figsize=(8, 3))
ax_line.plot(quarter_counts.index, quarter_counts.values, marker='o')
ax_line.set_ylabel("Opportunity Count")
ax_line.set_xlabel("Quarter")
ax_line.set_title("Total Opportunities per Quarter")
st.pyplot(fig_line)
