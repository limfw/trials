import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# --- Title ---
st.title("Rainfall and Wind Dashboard -(Simulated Data) illustration ")

# --- Load Data ---
@st.cache_data
def load_data():
    import requests
    from io import BytesIO

    # Load private file from GitHub using token
    url = "https://raw.githubusercontent.com/limfw/smf/main/data/output.csv"
    # no auth needed for public repo"}
    response = requests.get(url, headers=headers)
    df = pd.read_csv(BytesIO(response.content))
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
selected_year = st.sidebar.selectbox("Select Year", sorted(df['Year'].unique()))
selected_month = st.sidebar.selectbox("Select Month", ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

# --- Aggregated Data by Region ---
rain_col = f"Rain_{selected_month}"
wind_col = f"Wind_{selected_month}"

agg_df = df[df['Year'] == selected_year].groupby("Region")[[rain_col, wind_col]].mean().reset_index()
agg_df.rename(columns={rain_col: "Rainfall (mm)", wind_col: "Wind Speed (km/h)"}, inplace=True)

# --- Charts ---
st.subheader(f"Average Rainfall and Wind Speed - {selected_month} {selected_year}")

col1, col2 = st.columns(2)

with col1:
    chart_rain = alt.Chart(agg_df).mark_bar().encode(
        x=alt.X('Region', sort='-y'),
        y='Rainfall (mm)',
        color=alt.Color('Rainfall (mm)', scale=alt.Scale(scheme='blues')),
        tooltip=['Region', 'Rainfall (mm)']
    ).properties(width=350, height=300, title="Rainfall Intensity")
    st.altair_chart(chart_rain)

with col2:
    chart_wind = alt.Chart(agg_df).mark_bar().encode(
        x=alt.X('Region', sort='-y'),
        y='Wind Speed (km/h)',
        color=alt.Color('Wind Speed (km/h)', scale=alt.Scale(scheme='oranges')),
        tooltip=['Region', 'Wind Speed (km/h)']
    ).properties(width=350, height=300, title="Wind Speed Intensity")
    st.altair_chart(chart_wind)

#Show Raw Data per Region ---
#st.subheader("Company-Level Performance")
#filtered_df = df[(df['Year'] == selected_year)][['Region', 'Company', 'Efficiency', rain_col, wind_col]]
#filtered_df.columns = ['Region', 'Company', 'Efficiency Score', 'Rainfall (mm)', 'Wind Speed (km/h)']
#st.dataframe(filtered_df.sort_values(by='Region'))
