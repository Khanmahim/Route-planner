import streamlit as st
import folium
from streamlit_folium import st_folium
from database import init_db, save_route, load_routes
from optimizer import optimize_route
from datetime import datetime
import random
import pandas as pd

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
    .route-badge {
        background: linear-gradient(90deg, #F4A7B9, #A7C4F4);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 6px;
    }
    .dash-card {
        background: linear-gradient(135deg, #FFE8F4, #E8F4FF);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        border: 1.5px solid #F4A7B9;
        box-shadow: 0 4px 15px rgba(244,167,185,0.2);
        margin-bottom: 12px;
    }
    .dash-card .value {
        font-size: 32px;
        font-weight: 900;
        background: linear-gradient(90deg, #F4A7B9, #A7C4F4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 6px 0;
    }
    .dash-card .label {
        color: #B07DB8;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .dash-card .icon {
        font-size: 28px;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

ROUTE_ADJECTIVES = ["Swift","Breezy","Golden","Turbo","Lucky","Speedy","Stellar","Magic","Smooth","Zippy","Cosmic","Nimble","Rapid","Blazing","Sunny"]
ROUTE_NOUNS = ["Falcon","Arrow","Comet","Drifter","Voyager","Rocket","Dasher","Cruiser","Sprinter","Glider","Pathfinder","Express","Bolt","Rider","Chaser"]

def generate_route_name(origin, num_stops):
    now = datetime.now()
    day = now.strftime("%a")
    time_str = now.strftime("%I:%M %p")
    adj = random.choice(ROUTE_ADJECTIVES)
    noun = random.choice(ROUTE_NOUNS)
    origin_short = origin.split(",")[0].strip()[:15]
    return f"{adj} {noun} — {origin_short} • {num_stops} stops • {day} {time_str}"

def location_input(label, key, input_mode):
    if input_mode == "📍 Address":
        return st.text_input(label, placeholder="e.g. Dallas TX USA", key=key)
    else:
        return st.text_input(label, placeholder="e.g. 32.910097, -96.745197", key=key)

def compute_dashboard_stats(routes, default_mpg=25.0, default_fuel_price=3.50):
    if not routes:
        return None
    total_routes = len(routes)
    total_km = sum(float(r[5]) for r in routes)
    total_miles = round(total_km * 0.621371, 2)
    total_time = round(sum(float(r[6]) for r in routes), 2)
    total_gallons = round(total_miles / default_mpg, 2)
    total_fuel_cost = round(total_gallons * default_fuel_price, 2)
    avg_cost = round(total_fuel_cost / total_routes, 2)

    origins = [r[2] for r in routes]
    destinations = [r[3] for r in routes]
    top_origin = max(set(origins), key=origins.count)
    top_dest = max(set(destinations), key=destinations.count)

    dates = []
    for r in routes:
        try:
            dates.append(datetime.strptime(r[7], "%Y-%m-%d %H:%M").strftime("%Y-%m-%d"))
        except:
            pass

    date_counts = {}
    for d in dates:
        date_counts[d] = date_counts.get(d, 0) + 1

    return {
        "total_routes": total_routes,
        "total_miles": total_miles,
        "total_time": total_time,
        "total_fuel_cost": total_fuel_cost,
        "avg_cost": avg_cost,
        "top_origin": top_origin,
        "top_dest": top_dest,
        "date_counts": date_counts
    }

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📍 Route Details")
    input_mode = st.radio("Input Mode", ["📍 Address", "🌐 Coordinates"], horizontal=True)

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

# ── Header ───────────────────────────────────────────────
st.title("🚚 RoutePro — Delivery Route Planner")
st.markdown("<p style='color:#B07DB8; margin-top:-15px; font-size:1rem;'>✨ Plan smarter. Drive better. Save more.</p>", unsafe_allow_html=True)

# ── Dashboard Button ─────────────────────────────────────
dash_col, _ = st.columns([1, 4])
with dash_col:
    if st.button("📊 Open Dashboard", use_container_width=True):
        st.session_state["show_dashboard"] = not st.session_state.get("show_dashboard", False)

# ── Dashboard Modal ───────────────────────────────────────
if st.session_state.get("show_dashboard", False):
    routes = load_routes()
    stats = compute_dashboard_stats(routes, mpg, fuel_price)

    with st.container():
        st.markdown("---")
        st.markdown("## 📊 Your Driving Dashboard")

        if not stats:
            st.info("🌸 No routes yet! Optimize your first route to see stats here.")
        else:
            # Row 1 — 4 key metrics
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>🗺️</div>
                    <div class='value'>{stats['total_routes']}</div>
                    <div class='label'>TOTAL ROUTES</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>📏</div>
                    <div class='value'>{stats['total_miles']}</div>
                    <div class='label'>TOTAL MILES</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>⏱️</div>
                    <div class='value'>{stats['total_time']}h</div>
                    <div class='label'>TOTAL DRIVE TIME</div>
                </div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>⛽</div>
                    <div class='value'>${stats['total_fuel_cost']}</div>
                    <div class='label'>TOTAL FUEL SPENT</div>
                </div>""", unsafe_allow_html=True)

            # Row 2 — avg cost + top origin + top dest
            c5, c6, c7 = st.columns(3)
            with c5:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>💰</div>
                    <div class='value'>${stats['avg_cost']}</div>
                    <div class='label'>AVG COST PER ROUTE</div>
                </div>""", unsafe_allow_html=True)
            with c6:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>🏆</div>
                    <div class='value' style='font-size:16px;'>{stats['top_origin'][:20]}</div>
                    <div class='label'>MOST USED ORIGIN</div>
                </div>""", unsafe_allow_html=True)
            with c7:
                st.markdown(f"""<div class='dash-card'>
                    <div class='icon'>🎯</div>
                    <div class='value' style='font-size:16px;'>{stats['top_dest'][:20]}</div>
                    <div class='label'>MOST USED DESTINATION</div>
                </div>""", unsafe_allow_html=True)

            # Row 3 — Routes per day chart
            if stats["date_counts"]:
                st.markdown("### 📅 Routes Per Day")
                df = pd.DataFrame(
                    list(stats["date_counts"].items()),
                    columns=["Date", "Routes"]
                ).sort_values("Date")
                st.bar_chart(df.set_index("Date"), color="#F4A7B9")

        st.markdown("---")

# ── Main Content ──────────────────────────────────────────
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
                auto_name = generate_route_name(origin, len(stops))
                result["route_name"] = auto_name
                st.session_state["result"] = result
                save_route(
                    auto_name, origin, destination,
                    result["ordered_stops"],
                    result["total_distance"],
                    result["estimated_time"]
                )
                st.success(f"✅ Route saved as **{auto_name}**")

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

        # Show auto-generated name as badge
        if "route_name" in result:
            st.markdown(f"<div class='route-badge'>🗺️ {result['route_name']}</div>", unsafe_allow_html=True)

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
    st.markdown("### 📚 Route Library")
    routes = load_routes()
    if routes:
        st.markdown(f"<p style='color:#B07DB8; font-size:13px;'>🗂️ {len(routes)} route(s) saved</p>", unsafe_allow_html=True)
        for r in routes:
            with st.expander(f"🗺️ {r[1]}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**📍 From:** {r[2]}")
                    st.markdown(f"**🏁 To:** {r[3]}")
                    st.markdown(f"**🕐 Saved:** {r[7]}")
                with col_b:
                    st.markdown(f"**📏 Distance:** {round(float(r[5]) * 0.621371, 2)} miles")
                    st.markdown(f"**⏱️ Est. Time:** {r[6]} hrs")
                    st.markdown(f"**🛑 Stops:** {r[4]}")
    else:
        st.info("🌸 No saved routes yet!")
