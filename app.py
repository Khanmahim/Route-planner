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

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #FFF0F5 0%, #F0F8FF 50%, #F5FFF0 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #FFE4F0 0%, #E4F0FF 100%); border-right: 2px solid #F4A7B9; }
    h1 { background: linear-gradient(90deg, #F4A7B9, #A7C4F4, #A7F4C4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem !important; font-weight: 800 !important; }
    h2, h3 { color: #B07DB8 !important; font-weight: 700 !important; }
    [data-testid="stMetric"] { background: linear-gradient(135deg, #FFE8F4, #E8F4FF); border-radius: 16px; padding: 12px 16px; border: 1.5px solid #F4A7B9; margin-bottom: 8px; }
    [data-testid="stMetricLabel"] { color: #B07DB8 !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #7DB8B0 !important; font-weight: 800 !important; }
    .stButton > button { background: linear-gradient(90deg, #F4A7B9, #A7C4F4) !important; color: white !important; border: none !important; border-radius: 20px !important; font-weight: 700 !important; box-shadow: 0 4px 15px rgba(244,167,185,0.4) !important; }
    .stTextInput > div > div > input { border-radius: 12px !important; border: 1.5px solid #F4A7B9 !important; background: #FFF8FB !important; color: #5C4A6E !important; }
    .stNumberInput > div > div > input { border-radius: 12px !important; border: 1.5px solid #A7C4F4 !important; }
    hr { border-color: #F4A7B9 !important; opacity: 0.4; }
    .dash-card { background: linear-gradient(135deg, #FFE8F4, #E8F4FF); border-radius: 20px; padding: 20px; text-align: center; border: 1.5px solid #F4A7B9; box-shadow: 0 4px 15px rgba(244,167,185,0.2); margin-bottom: 12px; }
    .dash-value { font-size: 32px; font-weight: 900; background: linear-gradient(90deg, #F4A7B9, #A7C4F4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 6px 0; }
    .dash-label { color: #B07DB8; font-size: 13px; font-weight: 600; letter-spacing: 0.5px; }
    .dash-icon { font-size: 28px; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

ROUTE_ADJECTIVES = ["Swift","Breezy","Golden","Turbo","Lucky","Speedy","Stellar","Magic","Smooth","Zippy"]
ROUTE_NOUNS = ["Falcon","Arrow","Comet","Drifter","Voyager","Rocket","Dasher","Cruiser","Sprinter","Glider"]

def generate_route_name(origin, num_stops):
    now = datetime.now()
    adj = random.choice(ROUTE_ADJECTIVES)
    noun = random.choice(ROUTE_NOUNS)
    origin_short = origin.split(",")[0].strip()[:15]
    return f"{adj} {noun} — {origin_short} • {num_stops} stops • {now.strftime('%a %I:%M %p')}"

def location_input(label, key, input_mode):
    if input_mode == "📍 Address":
        return st.text_input(label, placeholder="e.g. Dallas TX USA", key=key)
    else:
        return st.text_input(label, placeholder="e.g. 32.910097, -96.745197", key=key)

def compute_stats(routes, mpg, fuel_price):
    if not routes:
        return None
    total_routes = len(routes)
    total_km = sum(float(r[5]) for r in routes)
    total_miles = round(total_km * 0.621371, 2)
    total_time = round(sum(float(r[6]) for r in routes), 2)
    total_gallons = round(total_miles / mpg, 2)
    total_fuel_cost = round(total_gallons * fuel_price, 2)
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
        "total_routes": total_routes, "total_miles": total_miles,
        "total_time": total_time, "total_fuel_cost": total_fuel_cost,
        "avg_cost": avg_cost, "top_origin": top_origin,
        "top_dest": top_dest, "date_counts": date_counts
    }

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("📍 Route Details")
    input_mode = st.radio("Input Mode", ["📍 Address", "🌐 Coordinates"], horizontal=True)

    if input_mode == "🌐 Coordinates":
        st.markdown("""
        <div style='background:#F0E8FF;border-radius:12px;padding:10px;border:1.5px dashed #B07DB8;font-size:12px;color:#5C4A6E;'>
        📌 <b>Google Maps</b> → Right-click → Copy coords<br>
        📋 Format: <code>32.910097, -96.745197</code>
        </div>
        """, unsafe_allow_html=True)

    origin = location_input("📍 Origin", "origin", input_mode)
    destination = location_input("🏁 Destination", "destination", input_mode)

    st.subheader("🛑 Stops")
    num_stops = st.number_input("Number of Stops", min_value=1, max_value=20, value=2)
    stops = []
    for i in range(int(num_stops)):
        stop = location_input(f"Stop {i+1}", f"stop_{i}", input_mode)
        stops.append(stop)

    st.divider()
    st.subheader("⛽ Fuel Settings")
    fuel_price = st.number_input("Fuel Price ($/gal)", min_value=0.01, value=3.50, step=0.01)
    mpg = st.number_input("Vehicle MPG", min_value=1.0, value=25.0, step=0.5)

    optimize_btn = st.button("🗺️ Optimize My Route!", use_container_width=True)

# ── Header ────────────────────────────────────────────────
st.title("🚚 RoutePro — Delivery Route Planner")
st.markdown("<p style='color:#B07DB8;margin-top:-15px;font-size:1rem;'>✨ Plan smarter. Drive better. Save more.</p>", unsafe_allow_html=True)

# ── Dashboard Toggle ──────────────────────────────────────
if st.button("📊 Open Dashboard", use_container_width=False):
    st.session_state["show_dashboard"] = not st.session_state.get("show_dashboard", False)

# ── Dashboard ─────────────────────────────────────────────
if st.session_state.get("show_dashboard", False):
    routes = load_routes()
    stats = compute_stats(routes, mpg, fuel_price)
    st.markdown("---")
    st.markdown("## 📊 Your Driving Dashboard")
    if not stats:
        st.info("🌸 No routes yet! Optimize your first route to see stats.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        for col, icon, val, label in zip(
            [c1, c2, c3, c4],
            ["🗺️", "📏", "⏱️", "⛽"],
            [stats["total_routes"], f"{stats['total_miles']} mi", f"{stats['total_time']}h", f"${stats['total_fuel_cost']}"],
            ["TOTAL ROUTES", "TOTAL MILES", "DRIVE TIME", "FUEL SPENT"]
        ):
            with col:
                st.markdown(f"""<div class='dash-card'>
                    <div class='dash-icon'>{icon}</div>
                    <div class='dash-value'>{val}</div>
                    <div class='dash-label'>{label}</div>
                </div>""", unsafe_allow_html=True)

        c5, c6, c7 = st.columns(3)
        for col, icon, val, label in zip(
            [c5, c6, c7],
            ["💰", "🏆", "🎯"],
            [f"${stats['avg_cost']}", stats["top_origin"][:22], stats["top_dest"][:22]],
            ["AVG COST/ROUTE", "TOP ORIGIN", "TOP DESTINATION"]
        ):
            with col:
                st.markdown(f"""<div class='dash-card'>
                    <div class='dash-icon'>{icon}</div>
                    <div class='dash-value' style='font-size:{"32px" if icon=="💰" else "15px"}'>{val}</div>
                    <div class='dash-label'>{label}</div>
                </div>""", unsafe_allow_html=True)

        if stats["date_counts"]:
            st.markdown("### 📅 Routes Per Day")
            df_chart = pd.DataFrame(list(stats["date_counts"].items()), columns=["Date","Routes"]).sort_values("Date")
            st.bar_chart(df_chart.set_index("Date"), color="#F4A7B9")
    st.markdown("---")

# ── Main Layout ───────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Route Map")

    if optimize_btn:
        if not origin or not destination or any(s == "" for s in stops):
            st.error("Please fill in all fields!")
        else:
            with st.spinner("🌸 Optimizing route..."):
                result, error = optimize_route(origin, stops, destination)
            if error:
                st.error(f"Error: {error}")
            else:
                auto_name = generate_route_name(origin, len(stops))
                result["route_name"] = auto_name
                st.session_state["result"] = result
                save_route(auto_name, origin, destination,
                          result["ordered_stops"],
                          result["total_distance"],
                          result["estimated_time"])
                st.success(f"✅ Saved as **{auto_name}**")

    # Check if we should show a saved route on map
    map_result = st.session_state.get("map_saved_route", None)
    active_result = st.session_state.get("result", None)
    display_result = map_result if map_result else active_result

    if display_result:
        all_coords = display_result["all_coords"]
        map_coords = display_result.get("map_coords", all_coords)
        routing_mode = display_result.get("routing_mode", "straight")

        if routing_mode == "real":
            st.success("✅ Real road routing!")
        else:
            st.warning("⚠️ Straight-line estimate")

        m = folium.Map(location=all_coords[0], zoom_start=12, tiles="CartoDB Positron")
        folium.Marker(all_coords[0], tooltip="🟢 Origin", icon=folium.Icon(color="green", icon="home")).add_to(m)
        for i, coord in enumerate(all_coords[1:-1]):
            folium.Marker(coord,
                tooltip=f"🛑 Stop {i+1}: {display_result['ordered_stops'][i]}",
                icon=folium.Icon(color="purple")).add_to(m)
        folium.Marker(all_coords[-1], tooltip="🔴 Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)
        folium.PolyLine(map_coords, color="#F4A7B9", weight=5).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        m = folium.Map(location=[32.7767, -96.7970], zoom_start=10, tiles="CartoDB Positron")
        st_folium(m, width=700, height=500)

with col2:
    st.subheader("📊 Route Summary")
    if st.session_state.get("result"):
        result = st.session_state["result"]
        total_miles = round(result["total_distance"] * 0.621371, 2)
        est_time = result["estimated_time"]
        gallons_used = round(total_miles / mpg, 2)
        fuel_cost = round(gallons_used * fuel_price, 2)

        st.metric("📏 Distance", f"{total_miles} miles")
        st.metric("⏱️ Est. Time", f"{est_time} hrs")
        st.metric("⛽ Gallons Used", f"{gallons_used} gal")

        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#FFE4F0,#E4F0FF);padding:20px;border-radius:20px;
                    text-align:center;border:2px solid #F4A7B9;margin-top:8px;'>
            <p style='color:#B07DB8;font-size:13px;margin:0;font-weight:600;'>💰 TOTAL FUEL COST</p>
            <p style='background:linear-gradient(90deg,#F4A7B9,#A7C4F4);-webkit-background-clip:text;
                      -webkit-text-fill-color:transparent;font-size:42px;font-weight:900;margin:8px 0'>${fuel_cost}</p>
        </div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("🛣️ Stop Order")
        colors = ["#FFB3C6","#B3D4FF","#B3FFD4","#FFD4B3","#D4B3FF"]
        all_labels = [result["origin"]] + result["ordered_stops"] + [result["destination"]]
        all_coords = result["all_coords"]
        for i in range(len(all_coords) - 1):
            from geopy.distance import geodesic
            leg_km = round(geodesic(all_coords[i], all_coords[i+1]).kilometers, 2)
            leg_miles = round(leg_km * 0.621371, 2)
            leg_cost = round((leg_miles / mpg) * fuel_price, 2)
            color = colors[i % len(colors)]
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,{color}40,{color}20);padding:10px 14px;
                        border-radius:12px;border-left:4px solid {color};margin-bottom:8px;'>
                <b style='color:#5C4A6E;'>{i+1}. {all_labels[i]} → {all_labels[i+1]}</b><br>
                <span style='color:#888;font-size:13px;'>📏 {leg_miles} mi &nbsp;|&nbsp; 💵 ${leg_cost}</span>
            </div>""", unsafe_allow_html=True)

    # ── Route Library ─────────────────────────────────────
    st.divider()
    st.subheader("📚 Route Library")
    routes = load_routes()

    if routes:
        st.caption(f"🗂️ {len(routes)} route(s) saved")

        # Table view
        df = pd.DataFrame({
            "🗺️ Route Name": [r[1] for r in routes],
            "📍 From": [r[2][:20] for r in routes],
            "🏁 To": [r[3][:20] for r in routes],
            "📏 Miles": [round(float(r[5]) * 0.621371, 1) for r in routes],
            "⏱️ Hrs": [round(float(r[6]), 1) for r in routes],
            "💰 Cost": [f"${round((float(r[5])*0.621371/mpg)*fuel_price, 2)}" for r in routes],
            "🕐 Date": [r[7] for r in routes],
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Click to show on map
        st.markdown("**🗺️ Show a saved route on map:**")
        route_names = [r[1] for r in routes]
        selected = st.selectbox("Select route", ["— select —"] + route_names, key="lib_select")

        if selected != "— select —":
            chosen = next(r for r in routes if r[1] == selected)
            with st.spinner("Loading route on map..."):
                import json
                stops_list = json.loads(chosen[4]) if chosen[4] else []
                saved_result, err = optimize_route(chosen[2], stops_list, chosen[3])
                if not err:
                    st.session_state["map_saved_route"] = saved_result
                    st.success(f"✅ Showing: {selected}")
                    st.rerun()
                else:
                    st.error("Could not reload this route on map.")

        if st.button("🧹 Clear Map", use_container_width=True):
            st.session_state.pop("map_saved_route", None)
            st.rerun()
    else:
        st.info("🌸 No saved routes yet!")
