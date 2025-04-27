def calculate_travel_time(departure_city, arrival_city, city_map, mode, osrm_link, params):
    """
    Calculates travel time between two cities using the OSRM API
    
    Args:
        departure_city (str): Name of the departure city
        arrival_city (str): Name of the arrival city
        mode (str): Transportation mode (driving, cycling, walking)
        
    Returns:
        tuple: (time in seconds, distance in meters, formatted time)
    """
    import requests
    
    # Get city coordinates
    try:
        lat1, lon1 = city_map[departure_city]
        lat2, lon2 = city_map[arrival_city]
    except ValueError as e:
        return (None, None, str(e))
    
    # Building the URL for the OSRM API
    url = f"{osrm_link}/{mode}/{lon1},{lat1};{lon2},{lat2}"

    # Call to the OSRM API
    try:
        response = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        return (None, None, f"Request failed: {e}")
    
    if response.status_code != 200:
        return (None, None, f"Error during API call: {response.status_code}")
    
    data = response.json()
    
    if data["code"] != "Ok":
        return (None, None, f"OSRM API error: {data['code']}")
    
    # Extracting time and distance information
    route = data["routes"][0]
    duration_seconds = route["duration"]
    distance_meters = route["distance"]
    
    # Formatting time for display
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    formatted_time = ""
    if hours > 0:
        formatted_time += f"{int(hours)} hour{'s' if hours > 1 else ''} "
    if minutes > 0:
        formatted_time += f"{int(minutes)} minute{'s' if minutes > 1 else ''}"
    
    if duration_seconds != None and distance_meters != None:
        return (duration_seconds, distance_meters, "")

def display_route(departure_city, arrival_city, city_map, mode, osrm_link, params):
    """Displays route information between two cities"""
    modes = {
        "driving": "by car",
        "cycling": "by bicycle",
        "walking": "on foot"
    }
    
    duration, distance, message = calculate_travel_time(departure_city, arrival_city, city_map, mode, osrm_link, params)
    
    if duration is None:
        print(message)
        return
    
    print(f"Route from {departure_city} to {arrival_city} {modes.get(mode, '')}:")
    print(f"Travel time: {message}")
    print(f"Distance: {distance/1000:.1f} km")