
import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="CoachHub Forecast Model", layout="wide")
st.image("logo.png", width=200)

st.title("CoachHub Forecast Model")

# Load Excel data
@st.cache_data
def load_data(sheet_name):
    df = pd.read_excel("CoachHub_Case_Study_Forecast_Example.xlsx", sheet_name=sheet_name)
    return df

# Sidebar options
model_option = st.sidebar.selectbox("Select Forecast Model", ["Model A", "Model B"])

if model_option == "Model A":
    data = load_data("Forecast Model A - Data")
elif model_option == "Model B":
    data = load_data("Forecast Model B - Data")

# Display data
st.subheader(f"Opportunities - {model_option}")
st.dataframe(data)

# KPI Summary
st.subheader("Summary Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Opportunities", len(data))
with col2:
    st.metric("Total Pipeline Value", f"${data['Potential Amount'].sum():,.0f}")
with col3:
    st.metric("Model Forecast", f"${data['Model Amount'].sum():,.0f}")

# Bar chart: Forecast by Category
st.subheader("Forecast Value by Category")
chart_data = data.groupby("Forecast Category")["Model Amount"].sum().reset_index()
st.bar_chart(chart_data.set_index("Forecast Category"))
