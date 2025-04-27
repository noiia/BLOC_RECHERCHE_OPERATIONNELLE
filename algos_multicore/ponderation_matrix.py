import random
from pyprobs import Probability as pr
import math
# Définition d'une constante pour la valeur maximale
MAX = math.inf  

City_Dependance = []

def generate_city_dependance(cities):
    """
    Generates a city dependence matrix based on the number of cities.
    """
    city_dependance = []
    for i in range(len(cities)):
        submatrix = []
        for j in range(len(cities)):
            if i == j:
                submatrix.append(0)
            else:
                road_blocked = pr.prob(0.25)  # 5% de probabilité
                if road_blocked:
                    submatrix.append(0)
                else:
                    submatrix.append(1)
        city_dependance.append(submatrix)
    return city_dependance


def generate_ponderation_matrix(matrix):
    ponderation_matrix = []

    for i in range(len(matrix)):
        submatrix = []
        for j in range(len(matrix[i])):
            road_blocked = pr.prob(0.05)# 5% de probabilité
            road_cost = random.uniform(0.6, 1.4)

            if road_blocked or matrix[i][j][0] == 0:
                submatrix.append(MAX)
            else:
                distance = matrix[i][j][0]
                time = matrix[i][j][1]
                cost = int(distance * 0.7) + int(time * 0.5 * road_cost)
                submatrix.append(cost)

        ponderation_matrix.append(submatrix)

    return ponderation_matrix


def calcul_fitness(chemin, matrice_ponderation, City_Dependance ):
    """
    Calcule la distance totale d'un chemin donné dans la matrice de distances.
    """
    ponderation_totale = 0
    for i in range(len(chemin) - 1):
        
        if matrice_ponderation[chemin[i]][chemin[i + 1]] == MAX:
            return float('inf')
        if City_Dependance[chemin[i]][chemin[i + 1]] == 0:
            return float('inf')
        if City_Dependance[chemin[i]][chemin[i + 1]] == 1:
            ponderation_totale += matrice_ponderation[chemin[i]][chemin[i + 1]]
    return ponderation_totale