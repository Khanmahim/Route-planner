from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time

ORS_API_KEY = ""  # Optional: add your free key from openrouteservice.org

geolocator = Nominatim(user_agent="route-planner")

def geocode_address(address):
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
    coords = {}
    
    origin_coord = geocode_address(origin)
    if not origin_coord:
        return None, "Could not geocode origin address."
    coords["origin"] = origin_coord

    stop_coords = []
    for stop in stops:
        coord = geocode_address(stop)
        if not coord:
            return None, f"Could not geocode stop: {stop}"
        stop_coords.append(coord)

    dest_coord = geocode_address(destination)
    if not dest_coord:
        return None, "Could not geocode destination address."
    coords["destination"] = dest_coord

    ordered_stops = nearest_neighbor(origin_coord, stop_coords, dest_coord)
    ordered_stop_names = [stops[i] for i, _ in ordered_stops]
    ordered_stop_coords = [c for _, c in ordered_stops]

    all_coords = [origin_coord] + ordered_stop_coords + [dest_coord]
    total_distance = sum(
        calculate_distance(all_coords[i], all_coords[i+1])
        for i in range(len(all_coords) - 1)
    )
    estimated_time = total_distance / 50

    return {
        "origin": origin,
        "destination": destination,
        "ordered_stops": ordered_stop_names,
        "all_coords": all_coords,
        "total_distance": round(total_distance, 2),
        "estimated_time": round(estimated_time, 2)
    }, None
