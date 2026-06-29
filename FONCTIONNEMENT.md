# Fonctionnement du projet

Ce document explique le fonctionnement complet du projet Metro Efrei Dodo :
les donnees utilisees, le role de chaque fichier, le pipeline Python, les
algorithmes de graphe, le front Vite/React et des exemples de sorties.

## Vue generale

Le projet transforme des donnees GTFS Ile-de-France Mobilites en un graphe
metro/RER exploitable pour calculer des itineraires.

Flux principal :

```text
donnees GTFS brutes
  -> filtrage metro/RER
  -> chargement trips + calendriers
  -> construction du graphe horaire
  -> algorithmes de trajet / connexite / arbre couvrant
  -> front-end de preview
```

Le front actuel est encore une preview statique. La logique metier avancee est
dans les scripts Python.

## Arborescence utile

```text
.
├── README.md
├── FONCTIONNEMENT.md
├── .gitignore
├── package.json
├── package-lock.json
├── vite.config.js
├── index.html
├── src/
│   ├── main.jsx
│   └── styles.css
├── scripts/
│   ├── filter_gtfs.py
│   ├── build_network.py
│   ├── gtfs_pipeline/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── routes.py
│   │   ├── services.py
│   │   ├── stops.py
│   │   └── network.py
│   └── graph_algorithms/
│       ├── __init__.py
│       ├── shortest_path.py
│       ├── astar.py
│       ├── compare.py
│       ├── connectivity.py
│       └── kruskal.py
├── tests/
│   ├── test_filter_gtfs.py
│   ├── test_build_network.py
│   ├── test_graph_algorithms.py
│   └── fixtures/simple_gtfs/
│       ├── routes.txt
│       ├── trips.txt
│       ├── calendar.txt
│       ├── calendar_dates.txt
│       ├── stops.txt
│       ├── stop_times.txt
│       └── transfers.txt
├── build/
│   └── routes_summary.json
└── data/
    ├── README.md
    └── raw/
        ├── Version1/
        ├── examples/
        └── gtfs-idfm-2024/
```

`node_modules/` et `dist/` sont des dossiers generes localement par npm/Vite.
Ils ne font pas partie du code metier.

## Fichiers racine

### `README.md`

Documentation courte du projet. Elle donne :

- l'objectif ;
- la structure principale ;
- les commandes importantes ;
- l'avancement ;
- les prochaines etapes.

### `FONCTIONNEMENT.md`

Ce fichier. Il detaille le fonctionnement complet et donne des exemples de
sorties.

### `.gitignore`

Indique a Git les fichiers ou dossiers a ignorer :

- `data/` pour eviter de versionner les donnees lourdes ;
- `dist/` pour eviter de versionner le build front ;
- `node_modules/` pour eviter de versionner les dependances npm.

### `package.json`

Declaration du front Vite/React.

Commandes principales :

```bash
npm run dev
npm run build
npm run preview
```

### `package-lock.json`

Verrouille les versions exactes des dependances npm. Il permet de reinstaller
les memes versions sur une autre machine.

### `vite.config.js`

Configure Vite avec le plugin React.

### `index.html`

Point d'entree HTML du front. Il charge :

```text
/src/main.jsx
```

## Front-end

### `src/main.jsx`

Contient l'application React de preview.

Elle affiche :

- un panneau de recherche depart/arrivee/date/heure ;
- une carte metro schematique en SVG ;
- des boutons pour les modes Trajet, Kruskal, Connexite ;
- une liste d'avancement du projet ;
- un resultat simule.

Important : pour l'instant ce front ne consomme pas encore `build/network.json`.
Il montre l'interface cible pendant que la logique Python est construite.

### `src/styles.css`

Contient tout le style du front :

- layout sidebar + carte ;
- boutons, champs, panneaux ;
- carte metro SVG ;
- responsive mobile.

## Donnees GTFS

### `data/README.md`

Explique le role du dossier `data/`.

### `data/raw/Version1/`

Anciennes donnees fournies dans le sujet initial :

- `metro.txt` ;
- `pospoints.txt` ;
- image de reference.

Elles servent surtout de reference historique.

### `data/raw/examples/`

Captures d'exemples UI fournies avec le sujet.

### `data/raw/gtfs-idfm-2024/`

Dossier principal des donnees GTFS.

Fichiers importants :

- `routes.txt` : lignes de transport ;
- `trips.txt` : trajets commerciaux ;
- `calendar.txt` : jours standards de circulation ;
- `calendar_dates.txt` : exceptions de calendrier ;
- `stops.txt` : arrets, quais et stations parentes ;
- `stop_times.txt` : horaires de passage ;
- `transfers.txt` : correspondances entre arrets ;
- `agency.txt`, `pathways.txt`, `stop_extensions.txt` : donnees GTFS presentes mais peu ou pas utilisees actuellement.

## Script de filtrage GTFS

### `scripts/filter_gtfs.py`

Ce script produit un JSON intermediaire lisible. Il sert a verifier que le
perimetre metro/RER est bien charge avant de construire le vrai graphe.

Il fait :

1. parse les heures GTFS comme `08:15:30` ou `25:10:00` ;
2. parse les dates GTFS comme `20240227` ;
3. lit les CSV GTFS en UTF-8 ;
4. garde seulement :
   - metro : `route_type = 1` ;
   - RER : `route_type = 2` et `agency_id = IDFM:71` ;
5. charge seulement les trips des lignes gardees ;
6. charge seulement les calendriers des services utilises ;
7. charge seulement les exceptions de ces services.

Commande :

```bash
python3 scripts/filter_gtfs.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/routes_summary.json
```

Exemple de sortie avec le fixture de test :

```json
{
  "source": "tests/fixtures/simple_gtfs",
  "routeCount": 3,
  "tripCount": 3,
  "serviceCount": 2,
  "calendarExceptionCount": 2,
  "routes": [
    {
      "id": "metro_1",
      "shortName": "1",
      "longName": "Metro 1",
      "mode": "metro",
      "color": "#FFBE00",
      "textColor": "#000000"
    }
  ],
  "trips": [
    {
      "id": "trip_m1_1",
      "routeId": "metro_1",
      "serviceId": "weekday",
      "headsign": "La Defense",
      "directionId": "0",
      "shapeId": "shape_m1"
    }
  ]
}
```

## Pipeline de construction du graphe

Le pipeline de graphe est separe dans `scripts/gtfs_pipeline/`.

### `scripts/build_network.py`

Point d'entree CLI. Il reste court volontairement.

Il fait :

1. lit les arguments `--gtfs-dir` et `--output` ;
2. appelle `build_network()` ;
3. ecrit le JSON final ;
4. affiche un resume.

Commande :

```bash
python3 scripts/build_network.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/network.json
```

Exemple de sortie console sur les vraies donnees :

```text
Wrote /tmp/network.json
Routes: 21
Stations: 540
Stops: 1024
Scheduled edge groups: 8869
Transfers: 2436
```

### `scripts/gtfs_pipeline/__init__.py`

Marque le dossier comme package Python.

### `scripts/gtfs_pipeline/common.py`

Contient les constantes et helpers communs :

- `PROJECT_ROOT` ;
- `DEFAULT_GTFS_DIR` ;
- `DEFAULT_OUTPUT` ;
- types GTFS metro/RER ;
- temps de correspondance par defaut ;
- `parse_time()` ;
- `parse_date()` ;
- `read_csv()`.

Exemple :

```python
parse_time("08:15:30") == 29730
parse_time("25:10:00") == 90600
```

### `scripts/gtfs_pipeline/routes.py`

Charge les lignes et les trajets.

Fonctions principales :

- `load_routes()` ;
- `load_trips()` ;
- `route_sort_key()`.

Il transforme les routes GTFS longues en objets compacts :

```json
{
  "id": "metro_1",
  "shortName": "1",
  "longName": "Metro 1",
  "mode": "metro",
  "color": "#FFBE00",
  "textColor": "#000000"
}
```

### `scripts/gtfs_pipeline/services.py`

Charge les calendriers de circulation.

Il lit :

- `calendar.txt` ;
- `calendar_dates.txt`.

Il produit des masques binaires de service. Chaque bit represente une date du
tableau `dates`.

Interet :

- JSON plus compact ;
- test rapide pour savoir si un service circule a une date donnee.

Exemple conceptuel :

```text
dates = ["2024-02-27", "2024-02-28", "2024-02-29"]
service actif les jours 0 et 2 -> masque binaire 101 -> entier 5
```

### `scripts/gtfs_pipeline/stops.py`

Charge et organise les arrets.

Il fait :

1. lit `stops.txt` ;
2. garde les coordonnees latitude/longitude ;
3. detecte les stations parentes ;
4. regroupe les quais dans leur station commerciale ;
5. cree des index numeriques.

Exemple de station :

```json
{
  "id": "station_c",
  "name": "Station C",
  "lat": 48.852,
  "lon": 2.32,
  "stops": [2, 3],
  "routes": [1, 2]
}
```

Exemple de stop :

```json
{
  "id": "stop_c_1",
  "name": "Station C quai 1",
  "station": 2,
  "lat": 48.8521,
  "lon": 2.3201,
  "routes": [1, 2],
  "platform": "1",
  "wheelchair": "1"
}
```

### `scripts/gtfs_pipeline/network.py`

Assemble le graphe final.

Il fait :

1. charge routes et trips ;
2. calcule les services actifs ;
3. charge les stops ;
4. lit `stop_times.txt` ;
5. cree des arcs horaires entre arrets consecutifs ;
6. ajoute les correspondances de `transfers.txt` ;
7. ajoute des correspondances internes entre quais d'une meme station ;
8. produit l'objet final `network`.

Exemple d'edge horaire :

```json
[
  0,
  1,
  0,
  0,
  [
    [0, 28860, 29100]
  ]
]
```

Lecture de cet exemple :

```text
fromStop = 0
toStop = 1
route = 0
headsign = 0
schedule = service 0, depart 08:01:00, arrivee 08:05:00
```

Exemple de transfert :

```json
[1, 2, 240]
```

Lecture :

```text
stop 1 -> stop 2 en 240 secondes
```

## Structure du `network.json`

Le JSON final contient :

```json
{
  "generatedAt": "2026-06-29T...",
  "source": "data/raw/gtfs-idfm-2024",
  "fallbackTransferSeconds": 180,
  "dates": ["2024-02-27", "..."],
  "routes": [],
  "services": [],
  "headsigns": [],
  "stations": [],
  "stops": [],
  "edges": [],
  "transfers": [],
  "stationEdges": []
}
```

Role des champs :

- `dates` : dates disponibles dans le GTFS ;
- `routes` : lignes metro/RER ;
- `services` : masques de circulation par service ;
- `headsigns` : directions ;
- `stations` : stations commerciales ;
- `stops` : quais/arrets precis ;
- `edges` : arcs horaires entre stops ;
- `transfers` : correspondances entre stops ;
- `stationEdges` : graphe simplifie station -> station pour connexite/Kruskal.

## Algorithmes de graphe

Les algorithmes sont dans `scripts/graph_algorithms/`.

### `scripts/graph_algorithms/__init__.py`

Marque le dossier comme package Python.

### `scripts/graph_algorithms/shortest_path.py`

Contient Dijkstra horaire.

Il prend :

- le `network` ;
- une station de depart ;
- une station d'arrivee ;
- une date ;
- une heure de depart.

Il cherche l'arrivee la plus tot.

Il prend en compte :

- l'attente du prochain train/RER ;
- les temps de trajet ;
- les correspondances.

Exemple de sortie lisible :

```json
{
  "algorithm": "dijkstra",
  "from": "Station A",
  "to": "Station C",
  "departure": "08:00:00",
  "arrival": "08:09:00",
  "duration": 540,
  "exploredStops": 3,
  "steps": [
    {
      "type": "ride",
      "from": "Station A quai 1",
      "to": "Station B quai 1",
      "departure": "08:01:00",
      "arrival": "08:05:00",
      "line": "1",
      "mode": "metro",
      "headsign": "La Defense",
      "wait": 60
    },
    {
      "type": "transfer",
      "from": "Station B quai 1",
      "to": "Station C quai 1",
      "departure": "08:05:00",
      "arrival": "08:09:00",
      "duration": 240
    }
  ]
}
```

### `scripts/graph_algorithms/astar.py`

Contient A* optionnel.

Il utilise une heuristique geographique :

```text
distance a vol d'oiseau jusqu'a l'arrivee / vitesse maximale theorique
```

Pourquoi :

- Dijkstra est la reference de correction ;
- A* peut explorer moins de stops ;
- on peut comparer les deux sans remplacer Dijkstra.

### `scripts/graph_algorithms/compare.py`

Compare Dijkstra et A* sur la meme requete.

Exemple :

```json
{
  "sameResult": true,
  "dijkstra": {
    "found": true,
    "arrival": 29340,
    "duration": 540,
    "exploredStops": 3,
    "elapsedMs": "..."
  },
  "astar": {
    "found": true,
    "arrival": 29340,
    "duration": 540,
    "exploredStops": 3,
    "elapsedMs": "..."
  }
}
```

### `scripts/graph_algorithms/connectivity.py`

Teste si le reseau est connecte avec un BFS.

Il utilise `stationEdges`, donc le graphe station par station.

Exemple :

```json
{
  "connected": true,
  "reachableCount": 3,
  "stationCount": 3,
  "missing": []
}
```

### `scripts/graph_algorithms/kruskal.py`

Construit un arbre couvrant minimum avec Kruskal.

Il utilise :

- `stationEdges` ;
- les poids minimums entre stations ;
- une structure Union-Find.

Exemple :

```json
{
  "complete": true,
  "stationCount": 3,
  "edgeCount": 2,
  "totalWeight": 660,
  "edges": [
    [0, 1, 0, 240],
    [1, 2, 2, 420]
  ]
}
```

## Tests

### `tests/test_filter_gtfs.py`

Teste le script de filtrage :

- parsing des heures ;
- parsing des dates ;
- rejet des heures invalides ;
- filtrage routes metro/RER ;
- chargement trips/calendriers/exceptions ;
- forme du JSON intermediaire.

### `tests/test_build_network.py`

Teste le graphe horaire :

- routes gardees ;
- dates disponibles ;
- edges horaires ;
- stationEdges ;
- transferts explicites ;
- transferts internes a une station.

### `tests/test_graph_algorithms.py`

Teste les algorithmes :

- Dijkstra trouve le chemin le plus tot ;
- la description du chemin contient lignes et horaires ;
- les transferts sont pris en compte ;
- A* donne le meme resultat que Dijkstra sur le fixture ;
- la comparaison Dijkstra/A* expose des metriques ;
- la connexite est correcte ;
- Kruskal produit un arbre couvrant minimum.

### `tests/fixtures/simple_gtfs/*.txt`

Petit GTFS minimal utilise par les tests.

Role des fichiers :

- `routes.txt` : 3 lignes utiles et 2 lignes ignorees ;
- `trips.txt` : trips associes aux lignes ;
- `calendar.txt` : services weekday/weekend ;
- `calendar_dates.txt` : exceptions ;
- `stops.txt` : 3 stations, 4 stops ;
- `stop_times.txt` : horaires de passage ;
- `transfers.txt` : correspondances.

## Commandes utiles

Installer le front :

```bash
npm install
```

Lancer la preview :

```bash
npm run dev
```

Compiler le front :

```bash
npm run build
```

Tester Python :

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Generer le resume filtre :

```bash
python3 scripts/filter_gtfs.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/routes_summary.json
```

Generer le graphe :

```bash
python3 scripts/build_network.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/network.json
```

## Etat fonctionnel actuel

Fait :

- lecture et filtrage GTFS ;
- trips et calendriers ;
- graphe horaire ;
- Dijkstra horaire ;
- A* optionnel ;
- comparaison Dijkstra/A* ;
- connexite BFS ;
- Kruskal ;
- preview front.

Pas encore branche :

- le front ne lit pas encore `build/network.json` ;
- le front n'appelle pas encore les algorithmes Python ;
- les resultats affiches dans le front sont encore simules.

Prochaine etape logique :

```text
creer une petite API Python ou porter les algorithmes en JavaScript,
puis brancher le front sur les vraies donnees.
```
