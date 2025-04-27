from multiprocessing import Pool, cpu_count
import calculate_travel_time

def geocode_city(city_name):
    from geopy.geocoders import Nominatim
    """Converts a city name to coordinates (latitude, longitude)"""
    geolocator = Nominatim(user_agent="routing_app", timeout=10)
    location = geolocator.geocode(city_name,country_codes="FR")
    
    if location:
        return (location.latitude, location.longitude)
    else:
        return None, None
    

def geocode_worker(city):
    lat, lon = geocode_city(city) 
    if lat is not None and lon is not None:
        return city, (lat, lon)
    return None
    
def GenerateCityMapFromCSV(size):
    """Generates a list of cities from a CSV file"""
    import pandas as pd
    import random
    from tqdm import tqdm
    
    city_map = {} 
    df = pd.read_csv("projet\CityName.csv", on_bad_lines='skip')
    city_list = df['City'].dropna().tolist()
    city_list = random.sample(city_list, size)
    
    with Pool(processes=cpu_count()) as pool:
        results = list(tqdm(pool.imap(geocode_worker, city_list)))
        
    # Filtrer les résultats None et ajouter au dictionnaire
    for result in results:
        if result:
            city, coords = result
            city_map[city] = coords
            
    return city_map

def matrix_generation(cities, mode, link, params, toPrint=False):
    import pytz
    from datetime import datetime
    from tqdm import tqdm

    matrix = []

    for sourceCity in tqdm(cities):
        submatrix = []
        for destinationCity in cities:
            if sourceCity is not destinationCity:
                duration, distance, _ = calculate_travel_time(sourceCity, destinationCity, cities, mode, link, params)
                if toPrint:
                    submatrix.append([datetime.fromtimestamp(duration, tz=pytz.utc).strftime('%H:%M:%S'), int(distance / 1000)])
                else:
                    submatrix.append([duration, int(distance / 1000)])
            else:
                submatrix.append([0, 0])
        matrix.append(submatrix)

    return matrix
