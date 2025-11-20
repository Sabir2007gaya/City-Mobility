import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pymongo import MongoClient

# --------- MongoDB Connection ---------
def get_mongo_data():
    # Streamlit secrets se Mongo URI etc padho
    mongo_uri = st.secrets["mongo"]["uri"]
    db_name = st.secrets["mongo"]["db"]
    collection_name = st.secrets["mongo"]["collection"]
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    data = list(collection.find())
    df = pd.DataFrame(data)
    return df

# --------- Utility Functions ---------
def load_data(file):
    return pd.read_csv(file)

def clean_data(df):
    # Remove NAs, duplicates
    df = df.dropna()
    df = df.drop_duplicates()
    return df

def add_features(df):
    # Example: peak hour, random calculations (customize based on your columns!)
    if "hour" in df.columns:
        df["PeakHour"] = np.where((df["hour"] >= 7) & (df["hour"] <= 10), "Morning", "Other")
    if "rain" in df.columns and "traffic_index" in df.columns:
        df["RainImpact"] = np.where(df["rain"] == 1, df["traffic_index"] * 0.8, df["traffic_index"])
    return df

# --------- Streamlit UI ---------
st.set_page_config(page_title="City Mobility & Pollution Insights Platform", layout="wide")
st.title("City Mobility & Pollution Insights Platform")
st.write("#### Analyze city traffic, pollution, weather & transport patterns interactively.")

# --- Data Source Choice ---
source = st.sidebar.radio("Data Source", ["Local CSV", "MongoDB"])
if source == "Local CSV":
    uploaded_file = st.sidebar.file_uploader("Upload your dataset (CSV)", type="csv")
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        st.info("Please upload a CSV file to proceed.")
        st.stop()
else:
    try:
        df = get_mongo_data()
    except Exception as e:
        st.error("Database error! Check secrets and connection.")
        st.stop()

# --- Data Cleaning & Feature Engineering ---
df = clean_data(df)
df = add_features(df)

st.header("Traffic & Pollution Overview")
st.dataframe(df.describe())

# --- Visualization 1: Traffic vs Pollution ---
if "traffic_index" in df.columns and "pollution_index" in df.columns:
    st.subheader("Traffic Patterns vs Pollution")
    fig, ax = plt.subplots()
    ax.scatter(df["traffic_index"], df["pollution_index"], c=df.get("rain", pd.Series([0]*len(df))), cmap="coolwarm", alpha=0.7)
    ax.set_xlabel("Traffic Index")
    ax.set_ylabel("Pollution Index")
    st.pyplot(fig)
else:
    st.warning("traffic_index & pollution_index columns not found.")

# --- Visualization 2: Rain Impact ---
if "rain" in df.columns and "traffic_index" in df.columns and "pollution_index" in df.columns:
    st.subheader("Rain Impact on Traffic & Pollution")
    rain_impact = df.groupby("rain")[["traffic_index", "pollution_index"]].mean()
    st.bar_chart(rain_impact)
else:
    st.warning("'rain', 'traffic_index', 'pollution_index' columns required for rain impact.")

# --- Visualization 3: Worst Time/Area ---
if "hour" in df.columns and "area" in df.columns and "pollution_index" in df.columns:
    st.subheader("Worst Time/Area for Pollution")
    grouped = df.groupby(["hour", "area"])["pollution_index"].mean().reset_index()
    st.dataframe(grouped.sort_values("pollution_index", ascending=False).head(10))
else:
    st.warning("'hour', 'area', 'pollution_index' columns required for this analysis.")

# --- Mode Of Transport Insights ---
if "transport_mode" in df.columns:
    st.header("Mode Of Transport Insights")
    transport_counts = df["transport_mode"].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(transport_counts, labels=transport_counts.index, autopct="%1.1f%%")
    st.pyplot(fig2)
else:
    st.warning("'transport_mode' column not found.")

# --- Weather Impact Analysis ---
if "weather" in df.columns and "pollution_index" in df.columns:
    st.header("Weather Impact Analysis")
    weather_impact = df.groupby("weather")["pollution_index"].mean()
    st.bar_chart(weather_impact)
else:
    st.warning("'weather' and 'pollution_index' columns required for weather impact analysis.")

st.success("Thanks for using City Mobility & Pollution Insights Platform!")

# MongoDB: Save summary
if st.sidebar.button("Save summary to MongoDB") and source == "MongoDB":
    mongo_uri = st.secrets["mongo"]["uri"]
    db_name = st.secrets["mongo"]["db"]
    collection_name = st.secrets["mongo"]["collection"]
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    summary = {"desc": "App run summary", "shape": str(df.shape)}
    collection.insert_one(summary)
    st.sidebar.success("Saved summary to MongoDB!")

