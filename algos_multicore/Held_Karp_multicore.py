import data_formator, calculate_travel_time, graphs
import ponderation_matrix as pdm

Cities = data_formator.GenerateCityMapFromCSV(25)

link = "http://router.project-osrm.org/route/v1/"
params = {
    "overview": "false",
    "alternatives": "false",
    }
matrix = data_formator.matrix_generation(Cities, "driving", link, params)

City_Dependance = pdm.generate_city_dependance(Cities)

ponderation_matrix = pdm.generate_ponderation_matrix(matrix)

graphs.generate_complete_graph(ponderation_matrix, Cities)
graphs.generate_complete_map(Cities)

import pytz
from datetime import datetime
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def compute_row(args):
    sourceCity, cities, mode, link, params, toPrint = args
    submatrix = []
    for destinationCity in cities:
        if sourceCity is not destinationCity:
            duration, distance, _ = calculate_travel_time(sourceCity, destinationCity, cities, mode, link, params)
            if toPrint:
                submatrix.append([
                    datetime.fromtimestamp(duration, tz=pytz.utc).strftime('%H:%M:%S'),
                    int(distance / 1000)
                ])
            else:
                submatrix.append([
                    duration,
                    int(distance / 1000)
                ])
        else:
            submatrix.append([0, 0])
    return submatrix

def matrix_generation(cities, mode, link, params, toPrint=False):
    args = [(city, cities, mode, link, params, toPrint) for city in cities]

    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap(compute_row, args), total=len(cities)))

    matrix = results
    return matrix



import itertools
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

def process_subset(args):
    S, subset, C, dist = args
    results = []
    for k in subset:
        prev_subset = S - {k}
        min_cost = float('inf')
        min_path = []

        for m in prev_subset:
            prev_cost, prev_path = C.get((prev_subset, m), (float('inf'), []))
            cost = prev_cost + dist[m][k]
            if cost < min_cost:
                min_cost = cost
                min_path = prev_path + [k]

        results.append(((S, k), (min_cost, min_path)))
    return results

def held_karp(dist, start=0):
    n = len(dist)
    C = {}

    for k in range(n):
        if k == start:
            continue
        C[(frozenset([k]), k)] = (dist[start][k], [start, k])

    for subset_size in tqdm(range(2, n)):
        subsets = list(itertools.combinations([i for i in range(n) if i != start], subset_size))

        args = []
        for subset in subsets:
            S = frozenset(subset)
            args.append((S, subset, C.copy(), dist))

        with Pool(cpu_count()) as pool:
            all_results = pool.map(process_subset, args)

        for results in all_results:
            for key, value in results:
                C[key] = value

    # Reconstruction du chemin optimal
    full_set = frozenset([i for i in range(n) if i != start])
    min_cost = float('inf')
    min_path = []

    for k in range(n):
        if k == start:
            continue
        cost, path = C.get((full_set, k), (float('inf'), []))
        total_cost = cost + dist[k][start]
        if total_cost < min_cost:
            min_cost = total_cost
            min_path = path + [start]

    return min_cost, min_path

min_cost, path = held_karp(ponderation_matrix, start=0)
print(f"Coût minimum : {min_cost}\nChemin : {path}")
graphs.generate_hamiltonian_graph(path, min_cost, ponderation_matrix, Cities)
graphs.generate_hamiltonian_map(path, Cities)