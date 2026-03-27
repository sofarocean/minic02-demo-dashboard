import streamlit as st
import requests
import folium
import pandas as pd
import struct
import os
from folium.plugins import MarkerCluster
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# MiniCO2 unpacking schema
# Based on the reference decoder struct:
#   uint16_t sample_count
#   double co2_min
#   double co2_max
#   double co2_mean
#   double co2_stdev
MINI_CO2_STRUCT = [
    ('uint16_t', 'sample_count'),
    ('double', 'co2_min'),
    ('double', 'co2_max'),
    ('double', 'co2_mean'),
    ('double', 'stdev'),
]


def format_timestamp(ts, to_local=False):
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    if to_local:
        return dt.astimezone().strftime('%Y-%m-%d %H:%M %Z')
    else:
        return dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


# Decoder
def hex_to_struct(hex_data, struct_description):
    byte_data = bytes.fromhex(hex_data.strip())
    fmt = '<'
    for dt, _ in struct_description:
        fmt += {'uint32_t': 'I', 'uint16_t': 'H', 'float': 'f', 'double': 'd', 'char': 'c'}[dt]
    size = struct.calcsize(fmt)
    if len(byte_data) != size:
        return None
    values = struct.unpack(fmt, byte_data)
    return {name: val.decode() if isinstance(val, bytes) else val
            for (_, name), val in zip(struct_description, values)}


st.set_page_config(layout="wide")

# Streamlit UI
st.title("Bristlemouth MiniCO2 Sensor Dashboard")

# Load credentials from secrets
spotter_id = st.secrets["SPOTTER_ID"]
api_token = st.secrets["API_TOKEN"]

default_start = os.getenv('DEFAULT_START_DATE') or (datetime.now(timezone.utc) - timedelta(days=30)).strftime('%Y-%m-%dT%H:%MZ')
start_date = st.text_input("Start Date (ISO)", default_start)

# Option to show results in local browser time
local_time = st.checkbox("Show timestamps in local browser time", value=True)

if st.button("Fetch & Decode Data"):
    url = f"https://api.sofarocean.com/api/sensor-data?token={api_token}&spotterId={spotter_id}&startDate={start_date}"
    r = requests.get(url)
    if not r.ok:
        st.error("Failed to fetch data.")
        print(r.text)
        print(url)
    else:
        readings = []
        for point in r.json().get('data', []):
            try:
                ts_raw = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                decoded = hex_to_struct(point['value'], MINI_CO2_STRUCT)
                
                if decoded:
                    decoded.update({
                        'time': format_timestamp(point['timestamp'], to_local=local_time),
                        'dt': ts_raw,
                        'latitude': point['latitude'],
                        'longitude': point['longitude']
                    })
                    readings.append(decoded)
            except Exception as e:
                print(e)
                continue
        st.session_state['readings'] = readings

if 'readings' in st.session_state:
    readings = st.session_state['readings']
    st.write(f"Found {len(readings)} reading(s).")

    # Create columns for Map and Chart
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### Map")
        m = folium.Map(location=[36.7411, -121.8180], zoom_start=10)
        cluster = MarkerCluster().add_to(m)
        for d in readings:
            folium.Marker(
                location=[d['latitude'], d['longitude']],
                popup=f"CO2: {d['co2_mean']:.1f} ppm @ {d['time']}",
            ).add_to(cluster)
        
        # Fit map to show all markers
        if readings:
            locations = [[d['latitude'], d['longitude']] for d in readings]
            m.fit_bounds(locations)
        
        st.components.v1.html(m._repr_html_(), height=500)

    with col2:
        st.write("### CO2 Levels Over Time")
        if readings:
            df = pd.DataFrame(readings)
            df = df.sort_values('dt')
            
            # Prepare chart data with min, mean, max
            chart_data = df[['dt', 'co2_min', 'co2_mean', 'co2_max']].copy()
            chart_data = chart_data.set_index('dt')
            chart_data.columns = ['Min', 'Mean', 'Max']
            
            st.line_chart(chart_data)
        else:
            st.info("No data to display in chart.")

    # Sort by timestamp descending
    sorted_readings = sorted(
        readings,
        key=lambda d: d['dt'],
        reverse=True
    )

    # Render the table
    st.write("### CO2 Readings Table")
    st.dataframe([
        {
            'Time': d['time'],
            'Samples': d['sample_count'],
            'CO2 Min (ppm)': f"{d['co2_min']:.1f}",
            'CO2 Mean (ppm)': f"{d['co2_mean']:.1f}",
            'CO2 Max (ppm)': f"{d['co2_max']:.1f}",
            'Latitude': f"{d['latitude']:.5f}",
            'Longitude': f"{d['longitude']:.5f}",
        }
        for d in sorted_readings
    ])
