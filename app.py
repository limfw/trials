import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium

# --- Load your uploaded GeoJSON file ---
with open("my.json", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# --- Sample region-based data (must match your GeoJSON properties) ---
# Adjust the names here to match `feature.properties.name` in your file
# You may inspect one by printing geojson_data['features'][0]['properties']
data = {
    "Region": [
        "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
        "Pahang", "Pulau Pinang", "Perak", "Perlis", "Selangor",
        "Terengganu", "Sabah", "Sarawak", "Kuala Lumpur", "Putrajaya", "Labuan"
    ],
    "Value": [25, 30, 22, 15, 18, 35, 28, 40, 10, 55, 26, 50, 65, 60, 12, 8]
}
df = pd.DataFrame(data)
df["Region"] = df["Region"].str.strip().str.title()

# --- Create base map centered on Malaysia ---
m = folium.Map(location=[4.5, 109], zoom_start=5.3)

# --- Choropleth Map ---
folium.Choropleth(
    geo_data=geojson_data,
    data=df,
    columns=["Region", "Value"],
    key_on="feature.properties.name",  # Make sure this matches your GeoJSON's property name
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Sample Metric by State",
    highlight=True,
).add_to(m)

# --- Streamlit Display ---
st.title("🗺️ Malaysia Choropleth Map (Your GeoJSON)")
st.write("This map uses your uploaded `my.json` file.")
st_folium(m, width=800, height_
