import data_formator, graphs
import ponderation_matrix as pdm
import calculate_travel_time as ctt

import pytz, os
import pandas as pd
import numpy as np
from datetime import datetime
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

def compute_row(args):
    
    print("\n### compute row ###")

    sourceCity, cities, mode, link, params, toPrint = args
    submatrix = []
    for destinationCity in cities:
        if sourceCity != destinationCity:
            duration, distance, _ = ctt.calculate_travel_time(sourceCity, destinationCity, cities, mode, link, params)
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

def generated_matrice_file(Cities, link, params):
    matrix = data_formator.matrix_generation(Cities, "driving", link, params)
    # matrix = data_formator.matrix_generation_parallele(Cities, "driving", link, params)

    City_Dependance = pdm.generate_city_dependance(Cities)

    ponderation_matrix = pdm.generate_ponderation_matrix(matrix)
    ponderation_matrix = np.where(np.isinf(ponderation_matrix), 1e8, ponderation_matrix)
    # Convertir en DataFrame
    df = pd.DataFrame(ponderation_matrix, columns=Cities)

    # Sauvegarder en fichier CSV
    df.to_csv(os.path.join(os.getcwd(), ".\\projet\\algos_multicore\\weighted_matrix.csv"), index=False)

def held_karp_from_file(file_path):
    df = pd.read_csv(file_path)
    ponderation_matrix = df.to_numpy()
    Cities = df.columns
    graphs.generate_complete_graph(ponderation_matrix, Cities)
    graphs.generate_complete_map(Cities)

    min_cost, path = held_karp(ponderation_matrix, start=0)
    print(f"Coût minimum : {min_cost}\nChemin : {path}")
    graphs.generate_hamiltonian_graph(path, min_cost, ponderation_matrix, Cities)
    graphs.generate_hamiltonian_map(path, Cities)


if __name__ == "__main__":
    # Cities = data_formator.GenerateCityMapFromCSV(35)

    link = "http://router.project-osrm.org/route/v1/"
    params = {
        "overview": "false",
        "alternatives": "false",
        }
    # generated_matrice_file(Cities, link, params)

    held_karp_from_file('./weighted_matrix.csv')