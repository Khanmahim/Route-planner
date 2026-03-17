import streamlit as st
import folium
from streamlit_folium import st_folium
from database import init_db, save_route, load_routes
from optimizer import optimize_route

init_db()

st.set_page_config(page_title="RoutePro", page_icon="🚚", layout="wide")
st.title("🚚 RoutePro — Delivery Route Planner")

with st.sidebar:
    st.header("📍 Enter Route Details")
    route_name = st.text_input("Route Name", placeholder="e.g. Monday Deliveries")
    origin = st.text_input("Origin Address", placeholder="e.g. 123 Main St, Dallas, TX")
    destination = st.text_input("Final Destination", placeholder="e.g. 456 Elm St, Dallas, TX")
    
    st.subheader("🛑 Stops")
    num_stops = st.number_input("Number of Stops", min_value=1, max_value=20, value=2)
    stops = []
    for i in range(num_stops):
        stop = st.text_input(f"Stop {i+1}", placeholder=f"e.g. Stop {i+1} address", key=f"stop_{i}")
        stops.append(stop)
    
    st.divider()
    st.subheader("⛽ Fuel Settings")
    fuel_price = st.number_input("Fuel Price ($ per gallon)", min_value=0.01, value=3.50, step=0.01)
    mpg = st.number_input("Vehicle Fuel Efficiency (MPG)", min_value=1.0, value=25.0, step=0.5)
    
    optimize_btn = st.button("🗺️ Optimize Route", use_container_width=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Route Map")
    if optimize_btn:
        if not origin or not destination or any(s == "" for s in stops):
            st.error("Please fill in all address fields.")
        else:
            with st.spinner("Geocoding addresses and optimizing route..."):
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
                    st.success(f"Route '{route_name}' saved!")

    if "result" in st.session_state:
        result = st.session_state["result"]
        all_coords = result["all_coords"]
        map_coords = result.get("map_coords", all_coords)
        routing_mode = result.get("routing_mode", "straight")

        m = folium.Map(location=all_coords[0], zoom_start=12)

        if routing_mode == "real":
            st.success("✅ Using real road routing!")
        else:
            st.warning("⚠️ Using straight-line estimate (real routing unavailable)")

        folium.Marker(all_coords[0], tooltip="Origin", icon=folium.Icon(color="green")).add_to(m)
        for i, coord in enumerate(all_coords[1:-1]):
            folium.Marker(coord, tooltip=f"Stop {i+1}: {result['ordered_stops'][i]}", icon=folium.Icon(color="orange")).add_to(m)
        folium.Marker(all_coords[-1], tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)
        folium.PolyLine(map_coords, color="blue", weight=4).add_to(m)

        st_folium(m, width=700, height=500)
    else:
        m = folium.Map(location=[32.7767, -96.7970], zoom_start=10)
        st_folium(m, width=700, height=500)

with col2:
    st.subheader("📊 Route Summary")
    if "result" in st.session_state:
        result = st.session_state["result"]

        total_km = result["total_distance"]
        total_miles = round(total_km * 0.621371, 2)
        est_time = result["estimated_time"]

        gallons_used = round(total_miles / mpg, 2)
        fuel_cost = round(gallons_used * fuel_price, 2)

        all_coords = result["all_coords"]
        all_labels = (
            [result["origin"]]
            + result["ordered_stops"]
            + [result["destination"]]
        )

        st.metric("📏 Total Distance", f"{total_miles} miles")
        st.metric("⏱️ Estimated Time", f"{est_time} hrs")

        st.divider()
        st.subheader("⛽ Fuel Cost Breakdown")
        st.metric("🔢 Gallons Used", f"{gallons_used} gal")
        st.metric("💵 Fuel Price", f"${fuel_price}/gal")
        st.metric("🚗 Vehicle MPG", f"{mpg} MPG")

        st.divider()
        st.markdown(
            f"""
            <div style='background-color:#1e1e2e;padding:16px;border-radius:10px;text-align:center'>
                <p style='color:#aaa;font-size:14px;margin:0'>💰 TOTAL ESTIMATED FUEL COST</p>
                <p style='color:#00e676;font-size:36px;font-weight:bold;margin:4px 0'>${fuel_cost}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()
        st.subheader("🛣️ Leg-by-Leg Breakdown")
        for i in range(len(all_coords) - 1):
            from geopy.distance import geodesic
            leg_km = round(geodesic(all_coords[i], all_coords[i+1]).kilometers, 2)
            leg_miles = round(leg_km * 0.621371, 2)
            leg_gallons = round(leg_miles / mpg, 2)
            leg_cost = round(leg_gallons * fuel_price, 2)
            st.markdown(f"""
            **{i+1}. {all_labels[i]} → {all_labels[i+1]}**
            📏 {leg_miles} mi &nbsp;|&nbsp; ⛽ {leg_gallons} gal &nbsp;|&nbsp; 💵 ${leg_cost}
            """)

        st.divider()
        st.subheader("💾 Saved Routes")
        routes = load_routes()
        if routes:
            for r in routes:
                with st.expander(f"📦 {r[1]} — {r[7]}"):
                    st.write(f"**Origin:** {r[2]}")
                    st.write(f"**Destination:** {r[3]}")
                    st.write(f"**Distance:** {r[5]} km")
                    st.write(f"**Est. Time:** {r[6]} hrs")
        else:
            st.info("No saved routes yet.")
    else:
        st.info("Enter your route details and click Optimize Route to see the cost breakdown.")

        st.divider()
        st.subheader("💾 Saved Routes")
        routes = load_routes()
        if routes:
            for r in routes:
                with st.expander(f"📦 {r[1]} — {r[7]}"):
                    st.write(f"**Origin:** {r[2]}")
                    st.write(f"**Destination:** {r[3]}")
                    st.write(f"**Distance:** {r[5]} km")
                    st.write(f"**Est. Time:** {r[6]} hrs")
        else:
            st.info("No saved routes yet.")
