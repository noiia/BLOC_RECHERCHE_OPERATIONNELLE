import calculate_travel_time as ctt

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
    
    print("\n### generate city map from csv ###")

    city_map = {} 
    df = pd.read_csv("projet\CityName.csv", on_bad_lines='skip')
    city_list = df['City'].dropna().tolist()
    city_list = random.sample(city_list, size)
    for city in tqdm(city_list):
        lat, lon = geocode_city(city) 
        if  (lat or lon) is not None:
            city_map[city] = (lat,lon)
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
                duration, distance, _ = ctt.calculate_travel_time(sourceCity, destinationCity, cities, mode, link, params)
                if toPrint:
                    submatrix.append([datetime.fromtimestamp(duration, tz=pytz.utc).strftime('%H:%M:%S'), int(distance / 1000)])
                else:
                    submatrix.append([duration, int(distance / 1000)])
            else:
                submatrix.append([0, 0])
        matrix.append(submatrix)

    return matrix


def submatrix_generation(args):
    import pytz
    from datetime import datetime

    sourceCity= args[0]
    cities= args[1]
    mode = args[2]
    link= args[3]
    params = args[4]
    toPrint = args[5]

    submatrix = []
    for destinationCity in cities:
        if sourceCity is not destinationCity:
            duration, distance, _ = ctt.calculate_travel_time(sourceCity, destinationCity, cities, mode, link, params)
            if toPrint:
                submatrix.append([datetime.fromtimestamp(duration, tz=pytz.utc).strftime('%H:%M:%S'), int(distance / 1000)])
            else:
                submatrix.append([duration, int(distance / 1000)])
        else:
            submatrix.append([0, 0])

def matrix_generation_parallele(cities, mode, link, params, toPrint=False):
    from tqdm import tqdm
    import multiprocessing
    from multiprocessing import Pool

    matrix = []
    tempoMatrix = {}

    with Pool(processes=16) as pool:
        for i, sourceCity in tqdm(enumerate(cities)):
            tempoMatrix[i] = [submatrix for submatrix in pool.imap(submatrix_generation, [sourceCity, cities, mode, link, params, toPrint])]

    for i in range(len(tempoMatrix)):
        matrix.append(tempoMatrix[i])

    return matrix