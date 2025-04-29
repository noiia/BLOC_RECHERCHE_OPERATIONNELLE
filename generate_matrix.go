package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"sync"
	"sync/atomic"
	"time"
)

type NominatimResponse struct {
	Lat string `json:"lat"`
	Lon string `json:"lon"`
}

type OSRMResponse struct {
	Code   string `json:"code"`
	Routes []struct {
		Duration float64 `json:"duration"`
		Distance float64 `json:"distance"`
	} `json:"routes"`
}

func CalculateTravelTime(departureCity, arrivalCity string, cityMap map[string][2]float64, mode, osrmLink string, params map[string]string) (float64, float64, string, error) {
	coordsDeparture, ok1 := cityMap[departureCity]
	coordsArrival, ok2 := cityMap[arrivalCity]

	if !ok1 || !ok2 {
		return 0, 0, "", fmt.Errorf("city not found in city map")
	}

	lat1, lon1 := coordsDeparture[0], coordsDeparture[1]
	lat2, lon2 := coordsArrival[0], coordsArrival[1]

	url := fmt.Sprintf("%s/%s/%.6f,%.6f;%.6f,%.6f", osrmLink, mode, lon1, lat1, lon2, lat2)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return 0, 0, "", err
	}

	query := req.URL.Query()
	for key, value := range params {
		query.Add(key, value)
	}
	req.URL.RawQuery = query.Encode()

	client := http.Client{Timeout: 50 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return 0, 0, "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return 0, 0, "", fmt.Errorf("API call error: %d", resp.StatusCode)
	}

	var osrmResp OSRMResponse
	err = json.NewDecoder(resp.Body).Decode(&osrmResp)
	if err != nil {
		return 0, 0, "", err
	}

	if osrmResp.Code != "Ok" {
		return 0, 0, "", fmt.Errorf("OSRM API error: %s", osrmResp.Code)
	}

	duration := osrmResp.Routes[0].Duration
	distance := osrmResp.Routes[0].Distance

	hours := int(duration) / 3600
	minutes := (int(duration) % 3600) / 60

	formattedTime := ""
	if hours > 0 {
		formattedTime += fmt.Sprintf("%d hour(s) ", hours)
	}
	if minutes > 0 {
		formattedTime += fmt.Sprintf("%d minute(s)", minutes)
	}

	return duration, distance, formattedTime, nil
}

func subMatrixGeneration(sourceCity, mode, link string, params map[string]string, cities []string, cityMap map[string][2]float64, toPrint bool, ch chan<- [][]interface{}) {
	submatrix := make([][]interface{}, 0)
	for _, destinationCity := range cities {
		if sourceCity != destinationCity {
			duration, distance, _, err := CalculateTravelTime(sourceCity, destinationCity, cityMap, mode, link, params)
			if err != nil {
				fmt.Println("Error:", err)
				submatrix = append(submatrix, []interface{}{0, 0})
				continue
			}

			if toPrint {
				formatted := time.Duration(duration * float64(time.Second)).String()
				submatrix = append(submatrix, []interface{}{formatted, int(distance / 1000)})
			} else {
				submatrix = append(submatrix, []interface{}{duration, int(distance / 1000)})
			}
		} else {
			submatrix = append(submatrix, []interface{}{0, 0})
		}
	}
	ch <- submatrix
}

func MatrixGeneration(mode, link string, params map[string]string, toPrint bool, cityMap map[string][2]float64) [][][]interface{} {
	matrix := make([][][]interface{}, 0)
	var cities []string
	for city := range cityMap {
		cities = append(cities, city)
	}

	total := len(cities)
	var progress int32 // Utilisation de la variable atomique

	numTasks := len(cities) * len(cities)

	ch := make(chan [][]interface{}, numTasks)
	var wg sync.WaitGroup

	for _, sourceCity := range cities {

		wg.Add(1)
		go func(sourceCity string) {
			defer wg.Done()
			subMatrixGeneration(sourceCity, mode, link, params, cities, cityMap, toPrint, ch)

			// Utilisation d'atomic.Add pour mettre à jour le progrès de manière sûre
			atomic.AddInt32(&progress, 1)
			fmt.Printf("\rProgress: %d/%d", progress, total)
		}(sourceCity)

	}
	wg.Wait()
	close(ch)

	for result := range ch {
		matrix = append(matrix, result)
	}

	fmt.Println("\nMatrix generation completed.")
	return matrix
}

func SaveMatrixToCSV(matrix [][][]interface{}, cities []string, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Première ligne : entête
	header := append([]string{""}, cities...)
	if err := writer.Write(header); err != nil {
		return err
	}

	// Corps : distances ou durées
	for i, row := range matrix {
		line := []string{cities[i]}
		for _, cell := range row {
			switch v := cell[0].(type) {
			case string:
				// Format temps "02:15:00"
				line = append(line, v)
			case float64:
				// Durée brute en secondes
				sec := strconv.FormatFloat(v, 'f', 2, 64)
				line = append(line, sec)
			default:
				line = append(line, "0")
			}
		}
		if err := writer.Write(line); err != nil {
			return err
		}
	}

	return nil
}

func main() {
	cityMap := map[string][2]float64{"Saint-Hilaire-de-la-Cote": {45.3903684, 5.32457}, "Rimouren": {44.4123787, 4.555342}, "Le Guineau": {47.2210814, -1.6933367}, "Saint-Georges": {50.3583949, 2.0874312}, "Vendegies-sur-Ecaillon": {50.2649195, 3.5150142}, "Le Gonnu": {46.0285726, 4.6332726}, "Sencenac-Puy-de-Fourches": {45.3152806, 0.6815095}, "Montepeau": {48.351617, 3.1486307}, "Lieudieu": {45.4584898, 5.1823288}, "Nans-les-Pins": {43.3732163, 5.7840241}, "La Reserve": {45.5047096, 3.4723583}, "Totainville": {48.3252, 5.9853}, "Azay-le-Ferron": {46.8512505, 1.071916}, "Seringour": {45.6246946, 2.2341964}, "La Billonniere": {48.7329176, -0.3695714}, "Veuxhaulles-sur-Aube": {47.9431941, 4.8043978}, "Chamarande": {48.5136159, 2.2174622}, "Port Cogolin": {43.2672642, 6.5785751}, "Bouverans": {46.8532028, 6.2085407}, "Habere-Lullin": {46.2346105, 6.452953}, "Les Generelles": {46.3403493, -1.4407234}, "Caer": {49.0670339, 1.1729273}, "Montbavin": {49.5232224, 3.5274844}, "Cambernard": {43.4752, 1.18071}, "L'Atelier": {46.9115105, 3.2431739}, "Billy-le-Grand": {49.1084612, 4.2306507}, "Audenfort": {50.7831675, 1.972389}, "Kerzean": {48.6433336, -4.1534422}, "Les Saulets": {47.2189116, 2.9458828}, "Cussey-les-Forges": {47.6428846, 5.0781663}, "Montmartin-en-Graignes": {49.2751306, -1.1458554}, "Saint-Vinnemer": {47.8258402, 4.0634891}, "Prats-de-Carlux": {44.9047823, 1.3143779}, "Villefrancon": {47.4146922, 5.7394708}, "Grand'Combe-des-Bois": {47.1377779, 6.7905904}, "Laigne-Saint-Gervais": {47.8740074, 0.2172097}, "Saint-Jeure-d'Ay": {45.146459, 4.7062686}, "Le Melleret": {49.5306949, -1.319348}, "Jarnac": {45.6791182, -0.1740904}, "Le Lys-Saint-Georges": {46.6414123, 1.8230968}, "Les Vieilles Fumades": {44.1863974, 4.2206274}, "La Mariolle": {47.6166905, -1.1366853}, "Malafretaz": {46.3218, 5.14516}, "Saint-Pierre-de-Vassols": {44.100156, 5.1390917}, "Boe": {44.2569693, 0.6124105}, "Graulhet": {43.7578, 1.99723}, "Boutenot": {47.1468946, 3.9842969}, "Avesnes-les-Aubert": {50.1976627, 3.3777081}, "Saliccia": {41.9673561, 8.6384618}, "Dingsheim": {48.6313586, 7.670241}, "Pleurs": {48.6875462, 3.8692493}, "Haut de Borde": {43.7757839, 0.1821763}, "Mezieres-sur-Issoire": {46.1098028, 0.9210491}, "Les Balines": {43.9249651, 0.6256444}, "Arvieu": {44.1904449, 2.6624576}, "Blarians": {47.4123951, 6.1796074}, "Cantebonne": {49.4580219, 5.9305167}, "Le Carroue": {47.488673, 2.9304281}, "La Gardiere": {47.2478856, 0.185631}, "Pouy-sur-Vannes": {48.306457, 3.588818}, "Thoiry": {46.236193, 5.9804153}, "Pruines": {44.5295098, 2.5036652}, "La Grande Garenne": {48.4386289, -1.1430931}, "Les Hauts Boises": {49.4294192, 1.3612957}, "Vernancourt": {48.8575905, 4.8231039}, "Rouet": {43.8119467, 3.8133382}, "Lucelle": {47.4215055, 7.2465475}, "Bonnevaux": {46.8079607, 6.1841936}, "Adelans-et-le-Val-de-Bithaine": {47.7102, 6.39856}, "Damville": {48.8665594, 1.0893351}, "Le Thureau": {46.1861401, 2.2402481}, "Quartier de Belloc": {44.1038704, 1.0856619}, "Lanrelas": {48.2520281, -2.2938122}, "Les Clauzels": {44.466243, 2.2309565}, "Steinbrunn-le-Haut": {47.6626861, 7.3479226}, "Les Trois-Saints": {45.4464341, 1.4930727}, "Mousterlin": {47.8495147, -4.040737}, "Foulognes": {49.1423195, -0.8161764}, "Loubizargues": {45.0651069, 2.9077627}, "Nantbellet": {45.7772421, 6.3262099}, "Mailly-le-Camp": {48.6700396, 4.2005817}, "Les Arcis": {48.4983304, -0.0174372}, "La Croix du Bas": {45.1853983, 5.6200231}, "Ix": {42.4338377, 1.9542449}, "Lirey": {48.1561393, 4.0453491}, "Molas": {43.3992, 0.785772}, "Besse-Mathieu": {46.1696621, 2.3484064}, "La Roche-Posay": {46.7862025, 0.812291}, "Hinguer": {48.6495763, -3.7508309}, "Seranon": {43.7742384, 6.7041357}, "Vignacourt": {50.0118385, 2.1967768}, "La Salamonie": {44.9953665, 1.3968404}, "Sagnat": {46.30354, 1.6279}, "Saint-Martin-Lys": {42.8273372, 2.2266605}, "Clery-en-Vexin": {49.1273725, 1.8401715}, "Chazelet": {46.5082911, 1.4426828}, "Le Pontgamp": {48.2773844, -2.7082452}, "Ottmarsheim": {47.7888815, 7.5094906}, "Balagny": {49.2959835, 2.3361068}, "Fertreve": {46.9686617, 3.5884101}, "Pollier": {46.4242502, 1.8839709}, "L'Istre": {43.6291718, 6.8446031}, "Les Issards": {43.0783483, 1.7355451}, "Salt-en-Donzy": {45.7372, 4.28816}, "Cavignac": {45.10045, -0.39039}, "Montignat": {46.164437, 2.9273024}, "Pierry": {49.0208997, 3.9391731}, "Planche": {46.8283914, 5.0039936}, "Roncheres": {49.1445, 3.60368}, "Bellegarde-en-Diois": {44.537799, 5.4277878}, "Rouge-Perriers": {49.1477725, 0.8338704}, "Sorges et Ligueux en Perigord": {45.2929355, 0.8456403}, "Thorigne-en-Charnie": {48.0008711, -0.3583521}, "Saint-Salvi-de-Carcaves": {43.8058236, 2.5967444}, "Saint-Georges du Plain": {47.9889242, 0.1715829}, "Le Richardet": {46.1445478, 2.6506329}, "Labenne": {43.5977, -1.42811}, "Dreuil-les-Amiens": {49.9141154, 2.2335005}, "Montgerain": {49.5368242, 2.5751383}, "Cravant-les-Coteaux": {47.15863, 0.346307}, "Saint-Vaize": {45.8128617, -0.6315818}, "Nota": {41.6062094, 9.2402315}, "Cite Wendel Nord": {49.2129631, 6.8752324}, "Masevaux-Niederbruck": {47.7817273, 7.0088677}, "Braucourt": {48.5473095, 4.8036965}, "Saint-Vaast-en-Cambresis": {50.1925792, 3.4251165}, "Lespinat": {45.551902, 1.7704944}, "Vaucelles": {49.2861286, -0.7388699}, "Sainte-Magnance": {47.4502934, 4.0753293}, "Le Fugeret": {44.0041444, 6.6407753}, "Sapareddu": {41.7363887, 9.3386788}, "Saint-Pierre-sur-Dives": {49.0192284, -0.0333457}, "Conilieu": {45.8256032, 5.3830567}, "Bonnemaison": {49.011708, -0.5833572}, "Saint-Aubin-en-Bray": {49.4217312, 1.8767596}, "Domloup": {48.0626279, -1.5236949}, "Les Pinasses": {45.6925875, 3.8275969}, "Viglain": {47.7274474, 2.3026499}, "Gottesheim": {48.7755403, 7.4808619}, "Lambezen": {48.2778566, -4.5666044}, "Pournoy-la-Chetive": {49.0201465, 6.1552512}, "Sant'Andrea-di-Tallano": {41.6993998, 9.0667479}, "Guethary": {43.423001, -1.6062693}, "Nonhigny": {48.5507594, 6.8811969}, "Le Ginou": {44.4003711, 3.0588197}, "Condamine": {46.1092, 5.55085}, "Vizzavona": {42.1285849, 9.1337639}, "Banaster": {47.5179884, -2.6674686}, "La Solane": {45.2941204, 1.7578581}, "Barges": {47.2128437, 5.060142}, "Barbezieux-Saint-Hilaire": {45.4812213, -0.1419472}, "Brouthieres": {48.4044433, 5.3254321}, "Verlac": {44.5057, 3.00796}, "Oreyte": {43.3915611, -0.9383153}, "Villemoirieu": {45.719104, 5.2271758}, "Hautecour la Basse": {45.4988435, 6.5440062}, "Aissey": {47.2687309, 6.3319395}, "Les Conquerants": {50.6573446, 3.0201397}, "Riblaire": {46.8887918, -0.2016182}, "Porte-Joie": {49.2523401, 1.2496503}, "Morenchies": {50.1940263, 3.2436076}, "La Fleuriais": {48.0900935, -1.3976263}, "Murcier": {46.0766462, 5.9569166}, "La Praz": {46.0038629, 4.9054277}, "Portbail": {49.3355434, -1.6999359}, "Bilos": {44.5240093, -0.895359}, "Le Mesnil-Roux": {49.5394931, 0.9731412}, "Tully": {50.0857478, 1.5160219}, "Terret": {45.2936431, 3.1701779}, "Village-Neuf": {47.6054816, 7.5696755}, "La Jaunais": {48.0128489, -1.5678356}, "Villeveix": {46.3778612, 2.0124024}, "Chenaumorte": {46.1152299, 0.8729354}, "Auffreville-Brasseuil": {48.9548027, 1.7102362}, "Puissalicon": {43.4578937, 3.235739}, "Les Fontanilles": {44.1388905, 4.0042318}, "Pont-de-Cervieres": {44.8866863, 6.6384345}, "Le Crey": {44.9870361, 5.7624044}, "Saint-Vidal": {45.0741643, 3.7993506}, "Le Mariquet": {49.2263119, -0.2540974}, "Pecquencourt": {50.3775793, 3.2150839}, "Champguyon": {48.77587, 3.54159}, "Amathay-Vesigneux": {47.0247083, 6.2024473}, "Vialot": {45.0936568, 1.1577349}, "Montreuil-l'Argille": {48.9392099, 0.4807965}, "Damvix": {46.3156917, -0.7337345}, "La Vignotte": {47.2429294, 5.1407379}, "Bizay": {47.1584627, -0.0223328}, "Sonnenberg": {49.4303607, 6.2540585}, "Trehiguier": {47.4932786, -2.4418582}, "Behorleguy": {43.1282741, -1.1177255}, "Aubigne": {48.2941715, -1.6345141}, "L'Arbrisseau": {49.5143238, 4.4091166}}
	mode := "driving"
	// link := "http://router.project-osrm.org/route/v1/"
	link := "http://osrm.panini.simon511000.fr/route/v1"
	params := map[string]string{
		"overview":     "false",
		"alternatives": "false",
	}

	startTime := time.Now()

	matrix := MatrixGeneration(mode, link, params, false, cityMap)

	endTime := time.Now()
	fmt.Printf("\nGenerated matrix in %.2f seconds.\n", endTime.Sub(startTime).Seconds())

	// Example: Print part of the matrix
	fmt.Println("\nSample matrix:")
	for _, row := range matrix {
		fmt.Println(row)
	}

	// err = SaveMatrixToCSV(matrix, cities, "matrix_output.csv")
	// if err != nil {
	// 	fmt.Println("Error saving matrix:", err)
	// } else {
	// 	fmt.Println("Matrix saved successfully to matrix_output.csv")
	// }
}
