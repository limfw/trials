import streamlit as st
import pandas as pd
import folium
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

# --- Inline Filters ---
st.title("🌧️ Rainfall & 🌬️ Wind Map with Operator Gauges (Malaysia Demo)")

col_y1, col_m1, col_o1 = st.columns([1, 2, 4])

with col_y1:
    selected_year = st.selectbox("Select Year", sorted(rain_df['Year'].unique()))

with col_m1:
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_slider = st.slider("Select Month (1=Jan ... 12=Dec)", 1, 12, 1)
    selected_month = months[month_slider - 1]
    selected_column = f"Rain_{selected_month}"

with col_o1:
    all_operators = sorted(rain_df['Company'].unique())
    selected_operators = st.multiselect("Select Operators", all_operators, default=all_operators)

# --- Filter Data ---
filtered_df = rain_df[(rain_df['Year'] == selected_year) & (rain_df['Company'].isin(selected_operators))].copy()
region_month = filtered_df[['Region', selected_column]].rename(columns={selected_column: "Rainfall"})

# --- Two Maps Side by Side ---
col1, col2 = st.columns(2)

# --- Rainfall Map ---
with col1:
    st.subheader(f"Rainfall Map - {selected_month} {selected_year}")
    m1 = folium.Map(location=[4.5, 102], zoom_start=6, tiles="CartoDB positron")
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

# --- Wind Map (Fake Intensity) ---
with col2:
    st.subheader("Wind Intensity Map (Synthetic)")
    filtered_df["WindIndex"] = 20 + (filtered_df["Efficiency"] * 80)  # Scale up for display
    wind_data = filtered_df[['Region', 'WindIndex']]

    m2 = folium.Map(location=[4.5, 102], zoom_start=6, tiles="CartoDB positron")
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

# --- Gauges for Operator Performance ---
# --- Gauges for Operator Performance ---
st.markdown("---")
st.subheader("🔧 Operator Efficiency Gauges (0–100%)")

if filtered_df.empty:
    st.warning("⚠️ No data available for the selected filters.")
else:
    filtered_df["EfficiencyPct"] = (filtered_df["Efficiency"] * 100).clip(0, 100)
    sorted_df = filtered_df.sort_values(by="EfficiencyPct", ascending=False)

    # Top 5 and Bottom 5
    top5 = sorted_df.head(5)
    bottom5 = sorted_df.tail(5).sort_values(by="EfficiencyPct", ascending=False)

    # 🔼 Top 5 Gauges
    st.markdown("### 🔼 Top 5 Operators")
    top_cols = st.columns(5)
    for i, row in enumerate(top5.itertuples()):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row.EfficiencyPct,
            title={'text': f"Top {i+1}<br>{row.Company}<br>({row.Region})", 'font': {'size': 12}},
            number={'suffix': '%', 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#4682B4"},
                'steps': [
                    {'range': [0, 40], 'color': '#F08080'},
                    {'range': [40, 70], 'color': '#FFD580'},
                    {'range': [70, 100], 'color': '#B0E57C'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': row.EfficiencyPct
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(t=20, b=20, l=5, r=5), paper_bgcolor="#F8F8F8")
        top_cols[i].plotly_chart(fig, use_container_width=True)

    # 🔽 Bottom 5 Gauges
    st.markdown("### 🔽 Bottom 5 Operators")
    bottom_cols = st.columns(5)
    for i, row in enumerate(bottom5.itertuples(), start=6):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=row.EfficiencyPct,
            title={'text': f"Bottom {i}<br>{row.Company}<br>({row.Region})", 'font': {'size': 12}},
            number={'suffix': '%', 'font': {'size': 16}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#4682B4"},
                'steps': [
                    {'range': [0, 40], 'color': '#F08080'},
                    {'range': [40, 70], 'color': '#FFD580'},
                    {'range': [70, 100], 'color': '#B0E57C'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': row.EfficiencyPct
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(t=20, b=20, l=5, r=5), paper_bgcolor="#F8F8F8")
        bottom_cols[i - 6].plotly_chart(fig, use_container_width=True)
