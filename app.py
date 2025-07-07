import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import requests
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from io import BytesIO
import json

# --- Title ---
st.title("Rainfall and Wind Dashboard - Use Peninsular Malaysia and syntetics data as example")

# --- Load Data ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/output.csv"
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to load CSV from GitHub!")
        st.stop()
    df = pd.read_csv(BytesIO(response.content))
    return df

@st.cache_data
def load_geojson():
    with open("data/malaysia_Geojs.txt", "r", encoding="utf-8") as f:
        gj = json.load(f)
    return gj

# --- Data ---
df = load_data()
geojson_data = load_geojson()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
selected_year = st.sidebar.selectbox("Select Year", sorted(df['Year'].unique()))
selected_month = st.sidebar.selectbox("Select Month", ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
selected_metric = st.sidebar.radio("Metric", ["Rainfall", "Wind"])

# --- Aggregated Data by Region ---
rain_col = f"Rain_{selected_month}"
wind_col = f"Wind_{selected_month}"
agg_df = df[df['Year'] == selected_year].groupby("Region")[[rain_col, wind_col]].mean().reset_index()
agg_df.rename(columns={rain_col: "Rainfall (mm)", wind_col: "Wind Speed (km/h)"}, inplace=True)

# --- Region Mapping (state name to region id) ---
region_mapping = {
    "Perlis": 1, "Kedah": 1,
    "Terengganu": 2,
    "Kelantan": 3,
    "Perak": 4,
    "Selangor": 5,
    "Negeri Sembilan": 6,
    "Melaka": 7,
    "Johor": 8
}

# --- Build DataFrame for Map (state name to region with values) ---
map_df = pd.DataFrame(region_mapping.items(), columns=["name", "Region"])
map_df = map_df.merge(agg_df, on="Region", how="left")

# --- Folium Map ---
st.subheader(f"{selected_metric} Map - {selected_month} {selected_year}")
map_center = [4.5, 102.0]
m = folium.Map(location=map_center, zoom_start=6.2)

metric_col = "Rainfall (mm)" if selected_metric == "Rainfall" else "Wind Speed (km/h)"
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=map_df,
    columns=["name", metric_col],
    key_on="feature.properties.name",
    fill_color='BuPu' if selected_metric == "Rainfall" else 'OrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=metric_col,
    nan_fill_color='white'
).add_to(m)

# --- Add tooltip per state ---
for _, row in map_df.iterrows():
    tooltip = f"{row['name']}\n{metric_col}: {row[metric_col]:.2f}" if not pd.isna(row[metric_col]) else row['name']
    folium.GeoJson(
        geojson_data,
        name=row['name'],
        tooltip=folium.Tooltip(tooltip),
        style_function=lambda feature: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 0.3,
            'dashArray': '5, 5'
        }
    ).add_to(m)

folium.LayerControl().add_to(m)
folium_static(m)

# --- Charts ---
st.subheader(f"Average Rainfall and Wind Speed - {selected_month} {selected_year}")
col1, col2 = st.columns(2)

with col1:
    chart_rain = alt.Chart(agg_df).mark_bar().encode(
        x=alt.X('Region:O', sort='-y'),
        y='Rainfall (mm)',
        color=alt.Color('Rainfall (mm)', scale=alt.Scale(scheme='blues')),
        tooltip=['Region', 'Rainfall (mm)']
    ).properties(width=350, height=300, title="Rainfall Intensity")
    st.altair_chart(chart_rain)

with col2:
    chart_wind = alt.Chart(agg_df).mark_bar().encode(
        x=alt.X('Region:O', sort='-y'),
        y='Wind Speed (km/h)',
        color=alt.Color('Wind Speed (km/h)', scale=alt.Scale(scheme='oranges')),
        tooltip=['Region', 'Wind Speed (km/h)']
    ).properties(width=350, height=300, title="Wind Speed Intensity")
    st.altair_chart(chart_wind)
