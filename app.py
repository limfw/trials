import streamlit as st
import pandas as pd
import folium
import json
import requests
from streamlit_folium import st_folium

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/my.json"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to load GeoJSON!")
        st.stop()
    geojson = response.json()

    peninsular_states = [
        "Kedah", "Perlis", "Perak", "Selangor", "Terengganu", 
        "Kelantan", "Negeri Sembilan", "Melaka", "Johor"
    ]
    geojson["features"] = [
        f for f in geojson["features"]
        if f["properties"]["name"] in peninsular_states
    ]
    return geojson

geojson_data = load_geojson()

@st.cache_data
def load_rainfall_data():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/output.csv"
    df = pd.read_csv(url)
    df["Region"] = df["Region"].astype(str).str.strip()
    return df

rain_df = load_rainfall_data()

month_options = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
selected_month = st.sidebar.selectbox("Select Month", month_options)
selected_column = f"Rain_{selected_month}"

region_month = rain_df.groupby("Region")[selected_column].mean().reset_index()
region_month.rename(columns={selected_column: "Rainfall"}, inplace=True)

m = folium.Map(location=[4.5, 102], zoom_start=6)

folium.Choropleth(
    geo_data=geojson_data,
    data=region_month,
    columns=["Region", "Rainfall"],
    key_on="feature.properties.name",
    fill_color="PuBu",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name=f"Rainfall in {selected_month} (mm)",
    nan_fill_color="white",
    highlight=True
).add_to(m)

st.title("🌧️ Rainfall Dashboard (Peninsular Malaysia Only)")
st.write(f"Rainfall for {selected_month} across selected states (synthetic data)")
st_folium(m, width=800, height=500)
