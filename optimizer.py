from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import time

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjI4MjcyYmU5ODU2ZDQ2N2U5OWExMjBkYzViYmRlZTQ4IiwiaCI6Im11cm11cjY0In0="

geolocator = Nominatim(user_agent="route-planner")

def parse_coord_string(s):
    try:
        parts = s.strip().split(",")
        if len(parts) == 2:
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return (lat, lon)
    except:
        pass
    return None

def geocode_address(address):
    # Check if it's already coordinates
    coord = parse_coord_string(address)
    if coord:
        return coord
    try:
        time.sleep(1)
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        return None

def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).kilometers

def get_real_route(coords):
    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }
        body = {"coordinates": [[c[1], c[0]] for c in coords]}
        response = requests.post(url, json=body, headers=headers)
        data = response.json()
        if "features" not in data:
            return None, None, None
        feature = data["features"][0]
        summary = feature["properties"]["summary"]
        distance_km = round(summary["distance"] / 1000, 2)
        duration_hrs = round(summary["duration"] / 3600, 2)
        route_coords = [(c[1], c[0]) for c in feature["geometry"]["coordinates"]]
        return distance_km, duration_hrs, route_coords
    except Exception as e:
        return None, None, None

def nearest_neighbor(origin_coord, stop_coords, dest_coord):
    unvisited = list(enumerate(stop_coords))
    ordered = []
    current = origin_coord
    while unvisited:
        nearest = min(unvisited, key=lambda x: calculate_distance(current, x[1]))
        ordered.append(nearest)
        current = nearest[1]
        unvisited.remove(nearest)
    return ordered

def optimize_route(origin, stops, destination):
    origin_coord = geocode_address(origin)
    if not origin_coord:
        return None, "Could not geocode origin address."

    stop_coords = []
    for stop in stops:
        coord = geocode_address(stop)
        if not coord:
            return None, f"Could not geocode stop: {stop}"
        stop_coords.append(coord)

    dest_coord = geocode_address(destination)
    if not dest_coord:
        return None, "Could not geocode destination address."

    ordered_stops = nearest_neighbor(origin_coord, stop_coords, dest_coord)
    ordered_stop_names = [stops[i] for i, _ in ordered_stops]
    ordered_stop_coords = [c for _, c in ordered_stops]
    all_coords = [origin_coord] + ordered_stop_coords + [dest_coord]

    real_distance, real_duration, route_coords = get_real_route(all_coords)

    if real_distance and real_duration and route_coords:
        return {
            "origin": origin, "destination": destination,
            "ordered_stops": ordered_stop_names,
            "all_coords": all_coords, "map_coords": route_coords,
            "total_distance": real_distance, "estimated_time": real_duration,
            "routing_mode": "real"
        }, None
    else:
        total_distance = sum(
            calculate_distance(all_coords[i], all_coords[i+1])
            for i in range(len(all_coords) - 1)
        )
        return {
            "origin": origin, "destination": destination,
            "ordered_stops": ordered_stop_names,
            "all_coords": all_coords, "map_coords": all_coords,
            "total_distance": round(total_distance, 2),
            "estimated_time": round(total_distance / 50, 2),
            "routing_mode": "straight"
        }, None
