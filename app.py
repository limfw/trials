import streamlit as st
import pandas as pd
import folium
import json
import requests
from streamlit_folium import st_folium

# --- Load GeoJSON from GitHub ---
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/my.json"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to load GeoJSON!")
        st.stop()
    return response.json()

geojson_data = load_geojson()

# --- Load CSV Rainfall Data ---
@st.cache_data
def load_rainfall_data():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/output.csv"
    df = pd.read_csv(url)
    df["Region"] = df["Region"].astype(str).str.strip()
    return df

rain_df = load_rainfall_data()

# --- Optional: Aggregate rainfall (pick month or average all months) ---
# Example here: take average of 12 months
rain_df["Rainfall"] = rain_df[[f"Rain_{m}" for m in 
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
].mean(axis=1)

region_avg = rain_df.groupby("Region")["Rainfall"].mean().reset_index()

# --- Create Map ---
m = folium.Map(location=[4.5, 109], zoom_start=6)

folium.Choropleth(
    geo_data=geojson_data,
    data=region_avg,
    columns=["Region", "Rainfall"],
    key_on="feature.properties.name",  # matches your GeoJSON name field
    fill_color="PuBu",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Avg Rainfall (mm)",
    nan_fill_color="white",
    highlight=True
).add_to(m)

# --- Streamlit UI ---
st.title("🌧️ Malaysia Rainfall Map (Synthetic Data)")
st.write("Average rainfall across Peninsular Malaysia regions (synthetic values).")
st_folium(m, width=800, height=500)
