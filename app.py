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
    geojson = response.json()

    # Keep only Peninsular Malaysia states
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

# --- Load Rainfall Data ---
@st.cache_data
def load_rainfall_data():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/output.csv"
    df = pd.read_csv(url)
    df["Region"] = df["Region"].astype(str).str.strip()
    return df

rain_df = load_rainfall_data()

# --- Select Year ---
years = sorted(rain_df['Year'].unique())
selected_year = st.sidebar.selectbox("Select Year", years)
filtered_df = rain_df[rain_df['Year'] == selected_year]

# --- Monthly Columns ---
month_cols = [f"Rain_{month}" for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]

# --- Display Map for Each Month ---
st.title("🌧️ Monthly Rainfall Map (Peninsular Malaysia)")
st.write(f"Drag the month slider below to view rainfall map for each month in {selected_year} (synthetic data)")

month_slider = st.slider("Select Month (1=Jan, ..., 12=Dec)", 1, 12, 1)
selected_month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month_slider - 1]
selected_column = f"Rain_{selected_month}"

region_month = filtered_df[['Region', selected_column]].rename(columns={selected_column: "Rainfall"})

# --- Create Folium Map ---
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

st_folium(m, width=800, height=500)
