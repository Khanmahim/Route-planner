import streamlit as st
import folium
from streamlit_folium import st_folium
from database import init_db, save_route, load_routes
from optimizer import optimize_route

init_db()

st.set_page_config(page_title="RoutePro", page_icon="🚚", layout="wide")

def location_input(label, key, input_mode):
    if input_mode == "📍 Address":
        return st.text_input(label, placeholder="e.g. Dallas TX USA", key=key)
    else:
        return st.text_input(label, placeholder="e.g. 32.910097, -96.745197", key=key)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #FFF0F5 0%, #F0F8FF 50%, #F5FFF0 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFE4F0 0%, #E4F0FF 100%);
        border-right: 2px solid #F4A7B9;
    }
    h1 {
        background: linear-gradient(90deg, #F4A7B9, #A7C4F4, #A7F4C4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
    }
    h2, h3 { color: #B07DB8 !important; font-weight: 700 !important; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFE8F4, #E8F4FF);
        border-radius: 16px;
        padding: 12px 16px;
        border: 1.5px solid #F4A7B9;
        margin-bottom: 8px;
    }
    [data-testid="stMetricLabel"] { color: #B07DB8 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #7DB8B0 !important; font-weight: 800 !important; }
    .stButton > button {
        background: linear-gradient(90deg, #F4A7B9, #A7C4F4) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(244, 167, 185, 0.4) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(244, 167, 185, 0.6) !important;
    }
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #F4A7B9 !important;
        background: #FFF8FB !important;
        color: #5C4A6E !important;
    }
    .stNumberInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #A7C4F4 !important;
        background: #F8FBFF !important;
    }
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #FFE8F4, #E8F4FF) !important;
        border-radius: 12px !important;
        color: #B07DB8 !important;
        font-weight: 600 !important;
    }
    hr { border-color: #F4A7B9 !important; opacity: 0.4; }
    .stInfo {
        background: linear-gradient(90deg, #E8F4FF, #F0E8FF) !important;
        border-left: 4px solid #A7C4F4 !important;
        border-radius: 12px !important;
    }
    .coord-tip {
        background: linear-gradient(135deg, #F0E8FF, #E8F4FF);
        border-radius: 12px;
        padding: 10px 14px;
        border: 1.5px dashed #B07DB8;
        margin-bottom: 10px;
        font-size: 12px;
        color: #5C4A6E;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📍 Route Details")

    input_mode = st.radio(
        "Input Mode",
        ["📍 Address", "🌐 Coordinates"],
        horizontal=True
    )

    if input_mode == "🌐 Coordinates":
        st.markdown("""
        <div class='coord-tip'>
        📌 <b>How to get coordinates:</b><br>
        1. Open <a href='https://maps.google.com' target='_blank'>Google Maps</a><br>
        2. Right-click any location<br>
        3. Click the numbers at the top<br>
        4. They auto-copy! Paste here 👇<br><br>
        📋 <b>Format:</b> <code>32.910097, -96.745197</code>
        </div>
        """, unsafe_allow_html=True)

    route_name = st.text_input("Route Name", placeholder="e.g. Monday Deliveries")
    origin = location_input("📍 Origin", "origin", input_mode)
    destination = location_input("🏁 Destination", "destination", input_mode)

    st.markdown("### 🛑 Stops")
    num_stops = st.number_input("Number of Stops", min_value=1, max_value=20, value=2)
    stops = []
    for i in range(num_stops):
        stop = location_input(f"🛑 Stop {i+1}", f"stop_{i}", input_mode)
        stops.append(stop)

    st.divider()
    st.markdown("### ⛽ Fuel Settings")
    fuel_price = st.number_input("Fuel Price ($ per gallon)", min_value=0.01, value=3.50, step=0.01)
    mpg = st.number_input("Vehicle Fuel Efficiency (MPG)", min_value=1.0, value=25.0, step=0.5)

    optimize_btn = st.button("🗺️ Optimize My Route!", use_container_width=True)

st.title("🚚 RoutePro — Delivery Route Planner")
st.markdown("<p style='color:#B07DB8; margin-top:-15px; font-size:1rem;'>✨ Plan smarter. Drive better. Save more.</p>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🗺️ Route Map")
    if optimize_btn:
        if not origin or not destination or any(s == "" for s in stops):
            st.error("⚠️ Please fill in all location fields!")
        else:
            with st.spinner("🌸 Optimizing your route..."):
                result, error = optimize_route(origin, stops, destination)
            if error:
                st.error(f"Error: {error}")
            else:
                st.session_state["result"] = result
                if route_name:
                    save_route(
                        route_name, origin, destination,
                        result["ordered_stops"],
                        result["total_distance"],
                        result["estimated_time"]
                    )
                    st.success(f"🌸 Route '{route_name}' saved!")

    if "result" in st.session_state:
        result = st.session_state["result"]
        all_coords = result["all_coords"]
        map_coords = result.get("map_coords", all_coords)
        routing_mode = result.get("routing_mode", "straight")

        if routing_mode == "real":
            st.success("✅ Using real road routing!")
        else:
            st.warning("⚠️ Using straight-line estimate")

        m = folium.Map(location=all_coords[0], zoom_start=12, tiles="CartoDB Positron")
        folium.Marker(all_coords[0], tooltip="🟢 Origin", icon=folium.Icon(color="pink", icon="home")).add_to(m)
        for i, coord in enumerate(all_coords[1:-1]):
            folium.Marker(coord, tooltip=f"🟠 Stop {i+1}: {result['ordered_stops'][i]}", icon=folium.Icon(color="purple", icon="map-marker")).add_to(m)
        folium.Marker(all_coords[-1], tooltip="🔴 Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)
        folium.PolyLine(map_coords, color="#F4A7B9", weight=5, opacity=0.9).add_to(m)

        st_folium(m, width=700, height=500)
    else:
        m = folium.Map(location=[32.7767, -96.7970], zoom_start=10, tiles="CartoDB Positron")
        st_folium(m, width=700, height=500)

with col2:
    st.markdown("### 📊 Route Summary")
    if "result" in st.session_state:
        result = st.session_state["result"]
        total_km = result["total_distance"]
        total_miles = round(total_km * 0.621371, 2)
        est_time = result["estimated_time"]
        gallons_used = round(total_miles / mpg, 2)
        fuel_cost = round(gallons_used * fuel_price, 2)
        all_coords = result["all_coords"]
        all_labels = [result["origin"]] + result["ordered_stops"] + [result["destination"]]

        st.metric("📏 Total Distance", f"{total_miles} miles")
        st.metric("⏱️ Estimated Time", f"{est_time} hrs")

        st.divider()
        st.markdown("### ⛽ Fuel Breakdown")
        st.metric("🔢 Gallons Used", f"{gallons_used} gal")
        st.metric("💵 Fuel Price", f"${fuel_price}/gal")
        st.metric("🚗 Vehicle MPG", f"{mpg} MPG")

        st.divider()
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FFE4F0, #E4F0FF);
                    padding:20px; border-radius:20px; text-align:center;
                    border: 2px solid #F4A7B9;
                    box-shadow: 0 4px 15px rgba(244,167,185,0.3);'>
            <p style='color:#B07DB8; font-size:13px; margin:0; font-weight:600;
                      letter-spacing:1px;'>💰 TOTAL FUEL COST</p>
            <p style='background: linear-gradient(90deg, #F4A7B9, #A7C4F4);
                      -webkit-background-clip: text;
                      -webkit-text-fill-color: transparent;
                      font-size:42px; font-weight:900; margin:8px 0'>${fuel_cost}</p>
            <p style='color:#B07DB8; font-size:11px; margin:0;'>
                {total_miles} miles • {gallons_used} gal • ${fuel_price}/gal</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🛣️ Leg-by-Leg Breakdown")
        colors = ["#FFB3C6", "#B3D4FF", "#B3FFD4", "#FFD4B3", "#D4B3FF"]
        for i in range(len(all_coords) - 1):
            from geopy.distance import geodesic
            leg_km = round(geodesic(all_coords[i], all_coords[i+1]).kilometers, 2)
            leg_miles = round(leg_km * 0.621371, 2)
            leg_gallons = round(leg_miles / mpg, 2)
            leg_cost = round(leg_gallons * fuel_price, 2)
            color = colors[i % len(colors)]
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {color}40, {color}20);
                        padding: 10px 14px; border-radius: 12px;
                        border-left: 4px solid {color}; margin-bottom: 8px;'>
                <b style='color:#5C4A6E;'>{i+1}. {all_labels[i]} → {all_labels[i+1]}</b><br>
                <span style='color:#888; font-size:13px;'>
                    📏 {leg_miles} mi &nbsp;|&nbsp; ⛽ {leg_gallons} gal &nbsp;|&nbsp; 💵 ${leg_cost}
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.markdown("### 💾 Saved Routes")
        routes = load_routes()
        if routes:
            for r in routes:
                with st.expander(f"📦 {r[1]} — {r[7]}"):
                    st.write(f"**Origin:** {r[2]}")
                    st.write(f"**Destination:** {r[3]}")
                    st.write(f"**Distance:** {r[5]} km")
                    st.write(f"**Est. Time:** {r[6]} hrs")
        else:
            st.info("🌸 No saved routes yet.")
    else:
        st.info("✨ Enter your route details and click Optimize to see the magic!")
        st.divider()
        st.markdown("### 💾 Saved Routes")
        routes = load_routes()
        if routes:
            for r in routes:
                with st.expander(f"📦 {r[1]} — {r[7]}"):
                    st.write(f"**Origin:** {r[2]}")
                    st.write(f"**Destination:** {r[3]}")
                    st.write(f"**Distance:** {r[5]} km")
                    st.write(f"**Est. Time:** {r[6]} hrs")
        else:
            st.info("🌸 No saved routes yet.")
