import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objs as go

api_key_temp_hum_light = "XSJUTZ46ZKN84UZ4"
api_key_ph = "M36VI314N6R9FLI2"
channel_id_temp_hum_light = "2534868"
channel_id_ph = "2562963"

url_temp_hum_light = f"https://api.thingspeak.com/update?api_key=FUP287STDDY8O6QD&field1=0"
url_ph = f"https://api.thingspeak.com/update?api_key=M36VI314N6R9FLI2&field1=0"

def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        feeds = data.get('feeds')
        if feeds is None:
            st.error("No 'feeds' key found in the data.")
            return []
        return feeds
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
        return []
    except ValueError as e:
        st.error(f"JSON decoding failed: {e}")
        return []

def create_gauge_chart(value, title, min_val, max_val, thresholds=None):
    if thresholds is None:
        thresholds = [(min_val, 'blue'), (max_val, 'red')]
    
    color = 'blue'
    for threshold, col in thresholds:
        if value <= threshold:
            color = col
            break
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={'axis': {'range': [min_val, max_val]},
               'bar': {'color': color}}))
    return fig

def process_feeds(feeds):
    df = pd.DataFrame(feeds)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df.set_index('created_at', inplace=True)
    for field in ['field1', 'field2', 'field3']:
        if field in df.columns:
            df[field] = df[field].astype(float)
    return df

feeds_temp_hum_light = get_data(url_temp_hum_light)
feeds_ph = get_data(url_ph)

# Debugging output
st.write("URL for temp/hum/light data:", url_temp_hum_light)
st.write("URL for pH data:", url_ph)

if feeds_temp_hum_light and feeds_ph:
    df_temp_hum_light = process_feeds(feeds_temp_hum_light)
    df_ph = process_feeds(feeds_ph)

    st.title("Smart Hydroponics")

    latest_temp = df_temp_hum_light['field1'].iloc[-1]
    latest_humidity = df_temp_hum_light['field2'].iloc[-1]
    latest_light = df_temp_hum_light['field3'].iloc[-1]
    latest_ph = df_ph['field1'].iloc[-1]

    st.header("Temperature, Humidity, Light Intensity, and pH Levels")

    st.subheader("Temperature")
    st.plotly_chart(create_gauge_chart(latest_temp, "Temperature (°C)", 0, 50, thresholds=[(15, 'blue'), (29, 'green'), (50, 'red')]))

    st.subheader("Humidity")
    st.plotly_chart(create_gauge_chart(latest_humidity, "Humidity (%)", 0, 100, thresholds=[(65, 'blue'), (89, 'green'), (100, 'red')]))

    st.subheader("Light Intensity")
    st.plotly_chart(create_gauge_chart(latest_light, "Light Intensity (lux)", 0, 1024, thresholds=[(90, 'green'), (1024, 'red')]))

    st.subheader("pH Level")
    st.plotly_chart(create_gauge_chart(latest_ph, "pH Level", 0, 14, thresholds=[(3, 'blue'), (6, 'green'), (14, 'red')]))

    st.header("Historical Data")

    st.subheader("Temperature, Humidity, and Light Intensity Over Time")
    st.line_chart(df_temp_hum_light[['field1', 'field2', 'field3']].rename(columns={
        'field1': 'Temperature',
        'field2': 'Humidity',
        'field3': 'Light Intensity'
    }))

    st.subheader("pH Level Over Time")
    st.line_chart(df_ph[['field1']].rename(columns={'field1': 'pH Level'}))

    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 15)
    if st.sidebar.button("Start Auto-Refresh"):
        while True:
            feeds_temp_hum_light = get_data(url_temp_hum_light)
            feeds_ph = get_data(url_ph)

            if feeds_temp_hum_light and feeds_ph:
                df_temp_hum_light = process_feeds(feeds_temp_hum_light)
                df_ph = process_feeds(feeds_ph)

                latest_temp = df_temp_hum_light['field1'].iloc[-1]
                latest_humidity = df_temp_hum_light['field2'].iloc[-1]
                latest_light = df_temp_hum_light['field3'].iloc[-1]
                latest_ph = df_ph['field1'].iloc[-1]

                with st.empty():
                    st.plotly_chart(create_gauge_chart(latest_temp, "Temperature (°C)", 0, 50, thresholds=[(15, 'blue'), (29, 'green'), (50, 'red')]))
                    st.plotly_chart(create_gauge_chart(latest_humidity, "Humidity (%)", 0, 100, thresholds=[(65, 'blue'), (89, 'green'), (100, 'red')]))
                    st.plotly_chart(create_gauge_chart(latest_light, "Light Intensity (lux)", 0, 1024, thresholds=[(90, 'green'), (1024, 'red')]))
                    st.plotly_chart(create_gauge_chart(latest_ph, "pH Level", 0, 14, thresholds=[(3, 'blue'), (6, 'green'), (14, 'red')]))

            time.sleep(refresh_interval)
            st.experimental_rerun()
