import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium

with open("my.json", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)


rain_df = pd.read_csv("https://github.com/limfw/trials/main/data/output.csv")  
rain_df["Region"] = rain_df["Region"].str.strip()

m = folium.Map(location=[4.5, 109], zoom_start=5.3)

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

st.title("🌧️ Malaysia Rainfall Map on synthetic data ")
st.write("Rainfall visualization on synthetic data")
st_folium(m, width=800, height=500)
