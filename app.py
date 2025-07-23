
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
col1.metric("Total Opportunities", len(data))
col2.metric("Total Potential Amount", f"{currency_symbol}{total_potential:,.0f}")
col3.metric("Model Amount", f"{currency_symbol}{total_model:,.0f}")

# Forecast by Category and Quarter
st.subheader("Model Amount By Category & Quarter")
data["Quarter"] = pd.to_datetime(data["Close Date"]).dt.to_period("Q").astype(str)
cat_qtr = data.groupby(["Forecast Category", "Quarter"])["Model Amount"].sum().unstack().fillna(0)
cat_qtr = cat_qtr.reindex(["Pipeline", "Best Case", "Probable", "Commit"]).div(1000)
quarters = cat_qtr.columns.tolist()
categories = cat_qtr.index.tolist()
bar_width = 0.15
x = np.arange(len(quarters))
fig1, ax = plt.subplots(figsize=(10, 5))
for i, cat in enumerate(categories):
    values = cat_qtr.loc[cat]
    ax.bar(x + i * bar_width, values, width=bar_width, label=cat)
ax.set_xticks(x + bar_width * (len(categories) - 1) / 2)
ax.set_xticklabels(quarters, rotation=45)
ax.set_ylabel("Model Amount (in thousands)")
ax.legend(title="Forecast Category")
st.pyplot(fig1)

# Potential vs Forecast by Category with % overlay
st.subheader("Potential Amount vs Model Amount")
cat_comp = data.groupby("Forecast Category")[["Potential Amount", "Model Amount"]].sum()
cat_comp = cat_comp.loc[["Pipeline", "Best Case", "Probable", "Commit"]]
cat_comp = cat_comp[cat_comp["Potential Amount"] > 0]
pct_line = (cat_comp["Model Amount"] / cat_comp["Potential Amount"] * 100).clip(upper=999).round(1)
cat_comp_div = cat_comp.div(1000)
fig2, ax1 = plt.subplots(figsize=(8, 4))
cat_comp_div.plot(kind='bar', ax=ax1, width=0.6)
for container in ax1.containers:
    ax1.bar_label(container, fmt='%.0f', label_type='edge', fontsize=8, padding=3)
ax1.set_ylabel("Amount (in thousands)")
ax2 = ax1.twinx()
ax2.plot(cat_comp.index, pct_line, color='red', marker='o', label="Model % vs Total")
for i, v in enumerate(pct_line):
    ax2.text(i, v + 2, f"{v:.1f}%", ha="center", va="bottom", color="red", fontsize=8)
ax2.set_ylabel("Model % of Potential")
ax2.set_ylim(0, 120)
ax2.legend(loc="upper left")
st.pyplot(fig2)

# Forecast by Rep and Category
st.subheader("Forecast by Sales Rep and Category")
rep_cat = data.pivot_table(index="Opportunity Owner", columns="Forecast Category", values="Model Amount", aggfunc="sum").fillna(0).div(1000)
fig3, ax3 = plt.subplots(figsize=(10, 4))
rep_cat.plot(kind='bar', stacked=True, ax=ax3)
ax3.set_ylabel("Model Amount (in thousands)")
ax3.set_xlabel("Opportunity Owner")
ax3.set_title("Model Amount by Sales Rep and Category")
st.pyplot(fig3)

# Format and display data table
st.subheader("Opportunity Detail")
percent_cols = [c for c in data.columns if "Weighting" in c or "Accuracy" in c or "Probability" in c]
for col in percent_cols:
    if col in data.columns and data[col].dtype != object:
        data[col] = (data[col] * 100).round(1).astype(str) + "%"

data["Potential Amount"] = data["Potential Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
data["Model Amount"] = data["Model Amount"].apply(lambda x: f"{currency_symbol}{x:,.0f}")
st.dataframe(data)
