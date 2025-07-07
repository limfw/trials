import streamlit as st
import pandas as pd
import folium
import json
import requests
import altair as alt
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

# --- Prepare Monthly Rainfall by Region ---
month_cols = [f"Rain_{month}" for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
rain_long = filtered_df.melt(id_vars=["Region"], value_vars=month_cols,
                              var_name="Month", value_name="Rainfall")
rain_long['Month'] = rain_long['Month'].str.replace("Rain_", "")

# --- Line Chart ---
st.title("🌧️ Monthly Rainfall (Peninsular Malaysia) - Line Chart")
st.write(f"Rainfall across regions for year {selected_year} (synthetic data)")

chart = alt.Chart(rain_long).mark_line(point=True).encode(
    x=alt.X('Month', sort=month_cols, title='Month'),
    y=alt.Y('Rainfall', title='Rainfall (mm)'),
    color='Region'
).properties(width=800, height=400)

st.altair_chart(chart, use_container_width=True)
