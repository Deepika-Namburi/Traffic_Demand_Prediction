import streamlit as st
import pandas as pd
import googlemaps
import folium
from streamlit_folium import folium_static
import pickle
from datetime import datetime
from folium.plugins import PolyLineTextPath

# Google Maps API Client
gmaps = googlemaps.Client(key="AIzaSyA9o2QRMtI5BJGn_UFN6NueWvHqSxGMCY4")

# Load the trained demand prediction model
with open("demand_prediction_xgboost.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Function to Predict Demand
def predict_demand(hour, day, weather, travel_time, traffic_level):
    # Mapping days to numerical values
    day_mapping = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                   "Friday": 4, "Saturday": 5, "Sunday": 6}
    day_numeric = day_mapping.get(day, -1)

    # Ensure correct feature order
    input_data = pd.DataFrame([[hour, day_numeric, traffic_level, weather, travel_time]],
                              columns=["Hour", "Day", "Traffic_Congestion_Level", "Weather_Conditions", "Travel_Time_Between_Stops"])

    # Make prediction
    prediction = model.predict(input_data)[0]
    return int(prediction)

# Function to Fetch Live Traffic Data
def get_live_traffic(origin, destination):
    try:
        directions = gmaps.directions(origin, destination, mode="driving", departure_time="now", alternatives=True)
        routes = []
        
        for route in directions:
            leg = route['legs'][0]
            distance = leg['distance']['text']
            duration = leg['duration_in_traffic']['text']
            traffic_level = len(route.get("warnings", []))  # Approximate traffic congestion level
            steps = [(step["start_location"]["lat"], step["start_location"]["lng"]) for step in leg["steps"]]
            routes.append((distance, duration, traffic_level, steps))
        
        return routes
    except Exception as e:
        st.error(f"Error fetching traffic data: {e}")
        return []

# Function to Display Routes on Map
def display_map(routes):
    if not routes:
        st.error("No routes available to display.")
        return

    # Initialize the map at the starting location
    m = folium.Map(location=[routes[0][3][0][0], routes[0][3][0][1]], zoom_start=12)

    # Mark origin and destination
    folium.Marker(location=[routes[0][3][0][0], routes[0][3][0][1]], popup="Origin", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=[routes[0][3][-1][0], routes[0][3][-1][1]], popup="Destination", icon=folium.Icon(color='red')).add_to(m)

    # Color different routes uniquely
    colors = ['blue', 'purple', 'orange', 'green']
    
    for i, route in enumerate(routes):
        polyline = folium.PolyLine(route[3], color=colors[i % len(colors)], weight=5, opacity=0.7).add_to(m)
        # Add route number along the polyline
        folium.plugins.PolyLineTextPath(
            polyline,
            text=f' Route {i+1} ',
            repeat=True,
            offset=7,
            attributes={'fill': colors[i % len(colors)], 'font-weight': 'bold', 'font-size': '12'}
        ).add_to(m)

    folium_static(m)

# Streamlit UI
st.title("🚦 Commuter Demand & Traffic Analysis")
tabs = st.tabs(["🚗 Traffic Data", "🗺️ Route Map","🚌 Demand Prediction"])

# Demand Prediction Tab
with tabs[2]:
    st.header("🚌 Public Transport Demand Prediction")
    hour = st.slider("Select Hour of the Day:", 0, 23, 8)
    day = st.selectbox("Select Day of the Week:", ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    weather = st.selectbox("Weather Conditions (0 - Clear, 1 - Cloudy, 2 - Rainy):", [0, 1, 2])
    travel_time = st.number_input("Enter Estimated Travel Time (minutes):", min_value=1, value=30)

    if st.button("Predict Demand"):
        traffic_level = 1  # Placeholder value; will be updated dynamically later
        demand = predict_demand(hour, day, weather, travel_time, traffic_level)
        st.success(f"Predicted Commuter Demand: {demand} passengers")

# Live Traffic Data Tab
with tabs[0]:
    st.header("🚗 Live Traffic Congestion Data")
    origin = st.text_input("Enter Origin" )
    destination = st.text_input("Enter Destination"
 )

    if st.button("Get Traffic Data"):
        routes = get_live_traffic(origin, destination)
        if routes:
            for i, (distance, duration, traffic_level, _) in enumerate(routes, start=1):
                st.write(f"**Route {i}:** {distance}, Estimated Time: {duration}, Traffic Level: {traffic_level}")
        else:
            st.error("No routes found. Please check the locations.")

# Route Map Tab
with tabs[1]:
    st.header("🗺️ Route Map")
    if st.button("Show Map"):
        routes = get_live_traffic(origin, destination)
        if routes:
            display_map(routes)
        else:
            st.error("No routes found. Please check the locations.")
