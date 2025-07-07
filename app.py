import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium

# --- Load your GeoJSON file ---
with open("my.json", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# --- Example: load your rainfall data ---
# Replace this with your real source (e.g., uploaded CSV)
# Example:
# Region,Rainfall
# Johor,120
# Kedah,85
rain_df = pd.read_csv("rain_df.csv")  # Your actual data here
rain_df["Region"] = rain_df["Region"].str.strip()

# Optional: inspect GeoJSON property key
# print(geojson_data["features"][0]["properties"])  # e.g., might be "name" or "Region"

# --- Create map ---
m = folium.Map(location=[4.5, 109], zoom_start=5.3)

# --- Plot choropleth map using your rainfall data ---
folium.Choropleth(
    geo_data=geojson_data,
    data=rain_df,
    columns=["Region", "Rainfall"],
    key_on="feature.properties.name",  # Replace "name" if your GeoJSON uses something else
    fill_color="PuBu",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Rainfall (mm)",
    highlight=True
).add_to(m)

# --- Streamlit display ---
st.title("🌧️ Malaysia Rainfall Map")
st.write("Rainfall visualization using your own GeoJSON and rain data")
st_folium(m, width=800, height=500)
