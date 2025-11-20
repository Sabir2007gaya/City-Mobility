import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utils import load_data, clean_data, add_features
from mongodb_connection import get_mongo_collection

st.set_page_config(page_title="City Mobility & Pollution Insights", layout="wide")
st.title("City Mobility & Pollution Insights Platform")
st.markdown("#### Explore city traffic, pollution, and weather patterns interactively.")

# Load data (local OR mongo)
option = st.sidebar.selectbox("Data Source", ["Local", "MongoDB"])
if option == "Local":
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = load_data(uploaded_file)
    else:
        st.warning("Please upload file.")
        st.stop()
else:
    collection = get_mongo_collection()
    data = list(collection.find())
    df = pd.DataFrame(data)

df = clean_data(df)
df = add_features(df)

st.header("Traffic & Pollution Overview")
st.write(df.describe())

# Visualization 1
st.subheader("Traffic Patterns vs Pollution")
fig, ax = plt.subplots()
ax.scatter(df['traffic_index'], df['pollution_index'])
ax.set_xlabel("Traffic Index")
ax.set_ylabel("Pollution Index")
st.pyplot(fig)

# Visualization 2
st.subheader("Rain Impact on Traffic & Pollution")
rain_impact = df.groupby("rain")["traffic_index", "pollution_index"].mean()
st.bar_chart(rain_impact)

# Time & Area Analysis
st.subheader("Worst Time/Area for Traffic & Pollution")
grouped = df.groupby(["hour", "area"])[["traffic_index", "pollution_index"]].mean().reset_index()
st.dataframe(grouped.sort_values("pollution_index", ascending=False).head(10))

st.sidebar.header("Explorer")
st.sidebar.write("Choose display options...")

# Transport Mode Insights
st.header("Mode Of Transport Insights")
transport_counts = df["transport_mode"].value_counts()
fig2, ax2 = plt.subplots()
ax2.pie(transport_counts, labels=transport_counts.index, autopct="%1.1f%%")
st.pyplot(fig2)

# Weather Impact Analysis
st.header("Weather Impact Analysis")
weather_impact = df.groupby("weather")["pollution_index"].mean()
st.bar_chart(weather_impact)

st.success("Thanks for using City Mobility & Pollution Insights Platform!")

# MongoDB Example
if st.sidebar.button("Save summary to MongoDB") and option == "MongoDB":
    summary = {"desc": "Summary of analysis", "shape": str(df.shape)}
    collection.insert_one(summary)
    st.sidebar.success("Saved to MongoDB!")
