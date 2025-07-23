
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Page setup
st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.title("CoachHub Forecast Model")

# Sidebar filters
st.sidebar.header("Filters")
currency_symbol_map = {"USD ($)": "$", "EUR (€)": "€", "GBP (£)": "£"}
currency = st.sidebar.selectbox("Select Currency", options=list(currency_symbol_map.keys()))
currency_symbol = currency_symbol_map[currency]
model_option = st.radio(
    "Select Forecast Model",
    ["Model A - Balanced", "Model B - Probability/Forecast Category Weighted"],
    horizontal=True
)
confidence_threshold = st.sidebar.slider("Minimum Model Confidence", 0.0, 1.0, 0.0, 0.05)
forecast_categories = ["Pipeline", "Best Case", "Probable", "Commit"]
selected_categories = st.sidebar.multiselect("Forecast Categories", forecast_categories, default=forecast_categories)
model_strengths = ["Weak", "Moderate", "Strong"]
selected_strengths = st.sidebar.multiselect("Model Strength", model_strengths, default=model_strengths)

# Load data
@st.cache_data
def load_data(sheet_name):
    return pd.read_excel("CoachHub Case Study Forecast Example.xlsx", sheet_name=sheet_name)

sheet = "Forecast Model A - Data" if "Model A" in model_option else "Forecast Model B - Data"
data = load_data(sheet)

# Ensure 'Quarter' exists
if "Quarter" not in data.columns and "Close Date" in data.columns:
    data["Close Date"] = pd.to_datetime(data["Close Date"], errors="coerce")
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

# KPI Summary
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)
total_potential = data["Potential Amount"].sum()
total_model = data["Model Amount"].sum()
col1.metric("Total Opportunities", len(data))
col2.metric("Total Potential Amount", f"{currency_symbol}{total_potential:,.0f}")
col3.metric("Model Amount", f"{currency_symbol}{total_model:,.0f}")

# Chart 1: Model Amount By Category & Quarter
st.subheader("Model Amount By Category & Quarter")
cat_qtr = (
    data.groupby(["Forecast Category", "Quarter"])["Model Amount"]
    .sum()
    .unstack(fill_value=0)
    .reindex(["Pipeline", "Best Case", "Probable", "Commit"])
    .div(1000)
)
quarters = list(cat_qtr.columns)
categories = list(cat_qtr.index)
x = np.arange(len(quarters))
bar_width = 0.2

fig1, ax1 = plt.subplots(figsize=(10, 5))
for i, cat in enumerate(categories):
    ax1.bar(x + i * bar_width, cat_qtr.loc[cat].values, width=bar_width, label=cat)
# total model amount line
quarter_totals = data.groupby("Quarter")["Model Amount"].sum().reindex(quarters).fillna(0).div(1000)
ax2 = ax1.twinx()
ax2.plot(x + bar_width, quarter_totals.values, color="red", marker="o", label="Total Model Amount")
ax1.set_xticks(x + bar_width * (len(categories) - 1) / 2)
ax1.set_xticklabels(quarters, rotation=45)
ax1.set_ylabel("Model Amount (in thousands)")
ax2.set_ylabel("Total Model Amount (in thousands)")
ax1.legend(title="Forecast Category", loc="upper left")
ax2.legend(loc="upper right")
st.pyplot(fig1)

# Chart 2: Potential Amount vs Model Amount
st.subheader("Potential Amount vs Model Amount")
cat_comp = (
    data.groupby("Forecast Category")[["Potential Amount", "Model Amount"]]
    .sum()
    .reindex(["Pipeline", "Best Case", "Probable", "Commit"])
    .fillna(0)
    .div(1000)
)
x = np.arange(len(cat_comp))
width = 0.35
fig2, ax3 = plt.subplots(figsize=(8, 5))
ax3.bar(x - width / 2, cat_comp["Potential Amount"], width, label="Potential Amount")
ax3.bar(x + width / 2, cat_comp["Model Amount"], width, label="Model Amount")
# percentage line
percent = (cat_comp["Model Amount"] / cat_comp["Potential Amount"]).replace([np.inf, -np.inf], np.nan) * 100
ax4 = ax3.twinx()
ax4.plot(x, percent.values, color="black", marker="o", label="% Model vs Potential")
for i, v in enumerate(percent):
    ax4.text(i, v + 1, f"{v:.0f}%", ha="center", va="bottom")
ax3.set_xticks(x)
ax3.set_xticklabels(cat_comp.index)
ax3.set_ylabel("Amount (in thousands)")
ax4.set_ylabel("Model % vs Potential")
ax3.legend(loc="upper left")
ax4.legend(loc="upper right")
st.pyplot(fig2)

# Chart 3: Model Amount by Sales Rep and Category
st.subheader("Model Amount by Sales Rep and Category")
rep_cat = (
    data.pivot_table(
        index="Opportunity Owner",
        columns="Forecast Category",
        values="Model Amount",
        aggfunc="sum",
    )
    .reindex(columns=["Pipeline", "Best Case", "Probable", "Commit"], fill_value=0)
    .fillna(0)
    .div(1000)
)
fig3, ax5 = plt.subplots(figsize=(10, 5))
rep_cat.plot(kind="bar", stacked=True, ax=ax5)
ax5.set_ylabel("Model Amount (in thousands)")
ax5.set_xlabel("Opportunity Owner")
ax5.set_title("Model Amount by Sales Rep and Category")
st.pyplot(fig3)

# Data table
st.subheader("Opportunity Detail")
percent_cols = [c for c in data.columns if any(x in c for x in ["Weighting", "Accuracy", "Probability"])]
for col in percent_cols:
    if data[col].dtype != object:
        data[col] = (data[col] * 100).round(1).astype(str) + "%"
data["Potential Amount"] = data["Potential Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
data["Model Amount"] = data["Model Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
st.dataframe(data)
