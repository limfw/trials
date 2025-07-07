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

debug_geojson_names = sorted([f["properties"]["name"] for f in load_geojson()["features"]])
geojson_data = load_geojson()

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

# --- Select Year ---
years = sorted(rain_df['Year'].unique())
selected_year = st.sidebar.selectbox("Select Year", years)
filtered_df = rain_df[rain_df['Year'] == selected_year]

month_cols = [f"Rain_{month}" for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]

st.title("Monthly Rainfall Map for Peninsular Malaysia - synthetic data only")
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

# --- Top & Bottom 5 Companies by Efficiency ---
top5 = filtered_df.sort_values(by="Efficiency", ascending=False).head(5)[["Company", "Region", "Efficiency"]]
bottom5 = filtered_df.sort_values(by="Efficiency", ascending=True).head(5)[["Company", "Region", "Efficiency"]]

st.subheader("Top 5 Companies by Efficiency")
st.dataframe(top5.style.format({"Efficiency": "{:.2f}"}), use_container_width=True)

st.subheader("Least 5 Companies by Efficiency")
st.dataframe(bottom5.style.format({"Efficiency": "{:.2f}"}), use_container_width=True)
