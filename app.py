import streamlit as st
import pandas as pd
import folium
import json
import requests
import plotly.graph_objects as go
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# --- Load GeoJSON ---
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

# --- Load Data ---
@st.cache_data
def load_rainfall_data():
    url = "https://raw.githubusercontent.com/limfw/trials/main/data/output.csv"
    df = pd.read_csv(url)
    df["Region"] = df["Region"].astype(str).str.strip()
    return df

rain_df = load_rainfall_data()

# --- Region Mapping ---
region_mapping = {
    "Region 1": "Perlis",
    "Region 2": "Terengganu",
    "Region 3": "Kelantan",
    "Region 4": "Perak",
    "Region 5": "Selangor",
    "Region 6": "Negeri Sembilan",
    "Region 7": "Melaka",
    "Region 8": "Johor"
}
rain_df["Region"] = rain_df["Region"].map(region_mapping)

# --- Year and Month Selection ---
years = sorted(rain_df['Year'].unique())
selected_year = st.sidebar.selectbox("Select Year", years)
filtered_df = rain_df[rain_df['Year'] == selected_year]

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_slider = st.sidebar.slider("Select Month (1=Jan ... 12=Dec)", 1, 12, 1)
selected_month = months[month_slider - 1]
selected_column = f"Rain_{selected_month}"

region_month = filtered_df[['Region', selected_column]].rename(columns={selected_column: "Rainfall"})

# --- Title ---
st.title("🌧️ Rainfall and 🌬️ Wind Map with Operator Performance (Synthetic Data)")

# --- Side-by-side Maps ---
col1, col2 = st.columns(2)

# Left: Rain Map
with col1:
    st.subheader(f"Rainfall Map - {selected_month} {selected_year}")
    m1 = folium.Map(location=[4.5, 102], zoom_start=6)
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
    ).add_to(m1)
    st_folium(m1, width=600, height=500)

# Right: Wind Map (Fake Wind Index from 20 to 80)
with col2:
    st.subheader("Wind Intensity Map (Synthetic)")
    # Fake wind data just for placeholder visualization
    filtered_df["WindIndex"] = 20 + (filtered_df["Efficiency"] % 60)
    wind_data = filtered_df[['Region', 'WindIndex']]

    m2 = folium.Map(location=[4.5, 102], zoom_start=6)
    folium.Choropleth(
        geo_data=geojson_data,
        data=wind_data,
        columns=["Region", "WindIndex"],
        key_on="feature.properties.name",
        fill_color="YlGnBu",
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="Wind Intensity (0–100)",
        nan_fill_color="white",
        highlight=True
    ).add_to(m2)
    st_folium(m2, width=600, height=500)

# --- Operator Efficiency Gauges ---
st.markdown("---")
st.subheader("🛠️ Operator Performance Gauges (0–100 Efficiency)")

# Top 10 Companies by Efficiency
top10 = filtered_df.sort_values(by="Efficiency", ascending=False).head(10)
cols = st.columns(10)

for i, row in enumerate(top10.itertuples()):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=row.Efficiency,
        title={'text': row.Company},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 40], 'color': "red"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "green"}
            ]
        }
    ))
    fig.update_layout(height=250, margin=dict(t=20, b=20, l=5, r=5))
    cols[i].plotly_chart(fig, use_container_width=True)
