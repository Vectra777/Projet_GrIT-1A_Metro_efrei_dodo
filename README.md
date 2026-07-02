# Projet GrIT 1A - Dijkstreet

Le projet exploite les donnees GTFS Ile-de-France Mobilites pour construire un
graphe metro/RER, tester des algorithmes de graphe et afficher une interface web
interactive de recherche d'itineraire.

## Structure actuelle

```text
.
├── data/
│   └── raw/
│       ├── Version1/
│       ├── examples/
│       └── gtfs-idfm-2024/
├── scripts/
│   ├── build_network.py
│   ├── filter_gtfs.py
│   ├── graph_algorithms/
│   │   ├── astar.py
│   │   ├── compare.py
│   │   ├── connectivity.py
│   │   ├── kruskal.py
│   │   └── shortest_path.py
│   └── gtfs_pipeline/
│       ├── common.py
│       ├── network.py
│       ├── routes.py
│       ├── services.py
│       └── stops.py
├── public/
│   ├── data/
│   │   └── network.json
│   ├── logo.png
│   ├── main.js
│   └── styles.css
├── index.html
├── package.json
├── vite.config.js
└── tests/
    ├── fixtures/simple_gtfs/
    ├── test_build_network.py
    ├── test_filter_gtfs.py
    └── test_graph_algorithms.py
```

## Avancement

Fait :

- parser les dates et heures GTFS ;
- filtrer les lignes metro/RER du perimetre ;
- charger les trips et calendriers utiles ;
- construire un graphe horaire compact avec stations, arrets, arcs horaires et correspondances ;
- calculer un itineraire avec Dijkstra horaire ;
- comparer Dijkstra avec A* optionnel ;
- exposer la comparaison Dijkstra / A* dans le front ;
- estimer l'empreinte carbone des trajets dans le front ;
- tester la connexite du graphe ;
- construire un arbre couvrant minimum avec Kruskal ;
- remplacer le front par l'interface complete adaptee pour Dijkstreet ;
- couvrir le pipeline Python avec des tests unitaires.

Reste possible en amelioration :

- optimiser la taille de `public/data/network.json` ;
- brancher les algorithmes Python sur une API si le calcul navigateur devient trop lourd ;
- ajouter des donnees temps reel si le perimetre final le demande.

## Donnees

Le dossier `data/` vient du projet de reference.

Les donnees principales sont dans :

```text
data/raw/gtfs-idfm-2024/
```

Elles suivent le format GTFS d'Ile-de-France Mobilites. Le pipeline utilise
`routes.txt`, `trips.txt`, `calendar.txt`, `calendar_dates.txt`, `stops.txt`,
`stop_times.txt` et `transfers.txt`.

Les regles de filtrage sont :

- metro : `route_type = 1` ;
- RER : `route_type = 2` avec `agency_id = IDFM:71` ;
- les autres modes sont ignores.

## Front-end

Le front est une application statique Vite en HTML, CSS et JavaScript vanilla.
Il reprend le front du projet complet et l'adapte au nom Dijkstreet.

Fichiers principaux :

- `index.html` : structure de l'application ;
- `public/styles.css` : styles de l'interface ;
- `public/main.js` : logique de carte, interactions et calculs cote navigateur ;
- `public/data/network.json` : graphe charge par le front.

Installation et lancement :

```bash
npm install
npm run dev
```

Fonctionnalites disponibles :

- carte interactive avec fond cartographique ;
- zoom, deplacement et recentrage ;
- survol des stations avec tooltip ;
- selection depart/arrivee par clic sur la carte ;
- recherche d'itineraire ;
- comparaison Dijkstra / A* ;
- estimation de l'empreinte carbone du trajet ;
- affichage des routes avec les couleurs des lignes ;
- test de connexite du reseau ;
- affichage et animation de l'arbre couvrant minimum.

## Filtrage GTFS

Le script de filtrage est :

```text
scripts/filter_gtfs.py
```

Il produit un JSON intermediaire lisible pour verifier que le perimetre GTFS est
correct.

Exemple d'utilisation :

```bash
python3 scripts/filter_gtfs.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/routes_summary.json
```

Sans `--output`, le JSON est affiche dans le terminal :

```bash
python3 scripts/filter_gtfs.py --gtfs-dir data/raw/gtfs-idfm-2024
```

## Graphe horaire

Le script de construction du graphe est :

```text
scripts/build_network.py
```

La logique est separee dans `scripts/gtfs_pipeline/` :

- `common.py` : constantes, lecture CSV, parsing date/heure ;
- `routes.py` : routes et trips ;
- `services.py` : calendriers et masques de services actifs ;
- `stops.py` : arrets, stations parentes et index ;
- `network.py` : assemblage du graphe, arcs horaires et transferts.

Commande :

```bash
python3 scripts/build_network.py
```

Pour alimenter le front :

```bash
python3 scripts/build_network.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output public/data/network.json
```

## Algorithmes graphe

Les algorithmes Python sont separes dans `scripts/graph_algorithms/` :

- `shortest_path.py` : Dijkstra horaire sur les arrets ;
- `astar.py` : A* optionnel avec heuristique geographique ;
- `compare.py` : comparaison Dijkstra/A* sur une meme requete ;
- `connectivity.py` : parcours BFS pour verifier si toutes les stations sont atteignables ;
- `kruskal.py` : arbre couvrant minimum sur les arcs de stations.

Dijkstra reste l'algorithme de reference pour garantir le plus court temps. A*
sert a comparer le nombre d'etats explores avec une heuristique geographique.

## Tests

Les tests utilisent un petit fixture GTFS minimal dans :

```text
tests/fixtures/simple_gtfs/
```

Lancer les tests :

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Verifier le build front :

```bash
npm run build
```
