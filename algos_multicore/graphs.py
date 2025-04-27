### Generate graph ###
def generate_complete_graph(matrix, cities):
    import networkx as nx
    import matplotlib.pyplot as plt
    
    G = nx.Graph()
    cities_converted = {}
    index = -1

    for city1 in range(len(cities)):
        for city2 in range(len(cities)):
            if city1 != city2:
                if matrix[city1][city2][1] != None:
                    if city1 not in cities_converted: 
                        index+=1
                        cities_converted[city1] = index
                    if city2 not in cities_converted:
                        index+=1
                        cities_converted[city2] = index
                    G.add_edge(cities_converted[city1], cities_converted[city2], weight=f"{matrix[city1][city2][1]}")
            
    pos = nx.spring_layout(G, seed=12, k=1.5)
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=1000, edge_color='gray', font_size=10)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.title("Graphe des villes avec distances")
    i = 0
    plt.text(1, -1, "\n".join([f"{i} : {city}" for i, city in enumerate(cities.keys())]), fontsize=10)
    plt.show()

def generate_hamiltonian_graph(path, path_cost, matrix, cities):
    import networkx as nx
    import matplotlib.pyplot as plt
    
    try :
        G = nx.DiGraph()
        cities_converted = {}
        total_weight = 0

        for city_index in range(len(path) - 1):
            city1 = list(cities.items())[path[city_index]]    
            city2 = list(cities.items())[path[city_index+1]]
            if city1 != city2:
                if city1 not in cities_converted: 
                    cities_converted[city1] = path[city_index]
                if city2 not in cities_converted:
                    cities_converted[city2] = path[city_index+1]

                edge_weight = matrix[list(cities.keys()).index(city1[0])][list(cities.keys()).index(city2[0])][1]
                total_weight += edge_weight
                G.add_edge(cities_converted[city1], cities_converted[city2],weight=f"{edge_weight}")
        
        if path_cost != total_weight:
            raise f"Dissociation between given path cost and computed total weight {path_cost, total_weight}"
        
        pos = nx.circular_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=500, edge_color='gray', font_size=10)
        nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color='gray', width=2, alpha=0.7, arrowstyle='-|>', arrowsize=20)
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
        
        plt.title("Graphe du chemin à suivre entre les villes")
        plt.text(1, -1, "\n".join([f"{i} : {city}" for i, city in enumerate(cities.keys())]) + f"\n\nCoût du chemin : {path_cost}", fontsize=10)
        plt.show()
    except:
        print("error during graph creation")

def generate_complete_map(cities):
    import folium
    import webbrowser
    from collections import defaultdict
    
    french_map = folium.Map(location=[46.5, 2.5], zoom_start=6)
    loc_cities = defaultdict(list)

    for city in cities:
        lat, lon = cities[city]
        if (lat or lon) != None:
            loc_cities[city].append((lat, lon))
        else:
            cities.pop(city)

    for city in cities:
        lat, lon = loc_cities[city][0]
        folium.Marker(location=[lat, lon], popup=city).add_to(french_map)

        for destCity in cities:
            if destCity != city:
                dest_lat, dest_lon = loc_cities[destCity][0]
                folium.PolyLine([(lat, lon), (dest_lat, dest_lon)], color="blue", weight=1).add_to(french_map)
    french_map.save("graphe_complet_sur_carte.html")
    webbrowser.open("graphe_complet_sur_carte.html")

def generate_hamiltonian_map(path, cities):
    import folium
    import webbrowser
    from collections import defaultdict

    french_map = folium.Map(location=[46.5, 2.5], zoom_start=6)
    loc_cities = defaultdict(list)

    for city in cities:
        lat, lon = cities[city]
        if lat and lon:
            loc_cities[city].append((lat, lon))
        else:
            cities.pop(city)

    for i, city in enumerate(cities):
        lat, lon = loc_cities[city][0]
        folium.Marker(
            location=[lat, lon],
            popup=city,
            icon=folium.DivIcon(html=f"""<div style="font-size: 16pt; color: white; background-color: blue; border-radius: 50%; width: 24px; height: 24px; text-align: center; line-height: 24px;">{i}</div>""")
        ).add_to(french_map)

    for i in range(len(path) - 1):
        city1 = list(cities.keys())[path[i]]  
        city2 = list(cities.keys())[path[i + 1]] 
        
        lat1, lon1 = loc_cities[city1][0]
        lat2, lon2 = loc_cities[city2][0]

        folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue", weight=2, opacity=0.6).add_to(french_map)

    french_map.save("graphe_hamiltonien_sur_carte.html")
    webbrowser.open("graphe_hamiltonien_sur_carte.html")