# Fonctionnement du projet

Ce document explique le fonctionnement complet du projet Dijkstreet :
les donnees utilisees, le role de chaque fichier, le pipeline Python, les
algorithmes de graphe, le front statique Vite et des exemples de sorties.

## Vue generale

Le projet transforme des donnees GTFS Ile-de-France Mobilites en un graphe
metro/RER exploitable pour calculer des itineraires et visualiser le reseau.

Flux principal :

```text
donnees GTFS brutes
  -> filtrage metro/RER
  -> chargement trips + calendriers
  -> construction du graphe horaire
  -> algorithmes de trajet / connexite / arbre couvrant
  -> front-end interactif chargeant public/data/network.json
```

Le front actuel reprend le projet complet et l'adapte au nom Dijkstreet. Il est
en HTML, CSS et JavaScript vanilla, servi par Vite.

## Arborescence utile

```text
.
├── README.md
├── FONCTIONNEMENT.md
├── package.json
├── package-lock.json
├── vite.config.js
├── index.html
├── public/
│   ├── data/
│   │   └── network.json
│   ├── logo.png
│   ├── main.js
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
└── data/
    └── raw/
        ├── Version1/
        ├── examples/
        └── gtfs-idfm-2024/
```

`node_modules/` et `dist/` sont generes localement par npm/Vite.

## Fichiers racine

### `README.md`

Documentation courte du projet : objectif, structure, commandes principales et
avancement.

### `FONCTIONNEMENT.md`

Ce fichier. Il detaille le role de chaque partie du projet.

### `package.json`

Declare l'application Vite statique.

Commandes principales :

```bash
npm run dev
npm run build
npm run preview
```

### `package-lock.json`

Verrouille les versions exactes des dependances npm.

### `vite.config.js`

Configuration Vite minimale. Le projet n'utilise plus React ni plugin React.

### `index.html`

Point d'entree HTML du front. Il charge :

```text
/styles.css
/main.js
```

Avec Vite, ces fichiers sont servis depuis `public/`.

## Front-end

### `public/main.js`

Contient toute la logique navigateur :

- chargement de `./data/network.json` ;
- preparation des stations, lignes et arcs ;
- projection geographique pour placer les stations ;
- dessin canvas de la carte ;
- chargement du fond cartographique ;
- zoom, deplacement et recentrage ;
- survol des stations avec tooltip ;
- selection depart/arrivee par clic ;
- calcul et affichage d'un trajet ;
- comparaison Dijkstra / A* sur une meme requete ;
- estimation carbone du trajet a partir des distances GTFS et du facteur ADEME Impact CO2 ;
- test de connexite ;
- calcul et animation de l'arbre couvrant minimum.

Exemple de donnees chargees :

```text
public/data/network.json
```

### `public/styles.css`

Contient le style de l'application :

- panneau de controle ;
- carte plein ecran ;
- boutons et champs ;
- tooltip station ;
- legende des lignes ;
- resultats de trajet ;
- responsive mobile.

### `public/data/network.json`

Graphe metro/RER utilise par le front.

Il contient notamment :

- `stations` : stations commerciales avec coordonnees ;
- `stops` : arrets/quais GTFS ;
- `routes` : lignes metro/RER ;
- `edges` : arcs horaires entre arrets consecutifs ;
- `transfers` : correspondances ;
- metadonnees utiles au rendu.

## Donnees GTFS

### `data/raw/gtfs-idfm-2024/`

Dossier principal des donnees GTFS.

Fichiers importants :

- `routes.txt` : lignes de transport ;
- `trips.txt` : trajets commerciaux ;
- `calendar.txt` : jours standards de circulation ;
- `calendar_dates.txt` : exceptions de calendrier ;
- `stops.txt` : arrets, quais et stations parentes ;
- `stop_times.txt` : horaires de passage ;
- `transfers.txt` : correspondances entre arrets.

## Script de filtrage GTFS

### `scripts/filter_gtfs.py`

Produit un JSON intermediaire lisible pour verifier le perimetre metro/RER.

Il fait :

1. parse les heures GTFS comme `08:15:30` ou `25:10:00` ;
2. parse les dates GTFS comme `20240227` ;
3. lit les CSV GTFS en UTF-8 ;
4. garde seulement le metro et le RER IDFM ;
5. charge les trips, calendriers et exceptions utiles.

Commande :

```bash
python3 scripts/filter_gtfs.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/routes_summary.json
```

Exemple de sortie simplifiee :

```json
{
  "source": "tests/fixtures/simple_gtfs",
  "routeCount": 3,
  "tripCount": 3,
  "serviceCount": 2,
  "calendarExceptionCount": 2
}
```

## Construction du graphe horaire

### `scripts/build_network.py`

Point d'entree CLI. Il lit les donnees GTFS, appelle le pipeline, puis ecrit le
JSON de sortie.

Commande :

```bash
python3 scripts/build_network.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output public/data/network.json
```

### `scripts/gtfs_pipeline/common.py`

Fonctions partagees :

- lecture CSV GTFS ;
- parsing des heures ;
- parsing des dates ;
- normalisation de couleurs ;
- constantes de filtrage metro/RER.

### `scripts/gtfs_pipeline/routes.py`

Charge les lignes et trajets :

- garde les routes metro/RER ;
- normalise les noms et couleurs ;
- garde les trips lies aux routes retenues.

### `scripts/gtfs_pipeline/services.py`

Charge les calendriers :

- services standards ;
- exceptions de dates ;
- jours actifs.

### `scripts/gtfs_pipeline/stops.py`

Construit les stations :

- regroupe les quais dans leurs stations parentes ;
- conserve les coordonnees ;
- cree les index utiles au graphe.

### `scripts/gtfs_pipeline/network.py`

Assemble le graphe final :

- arcs horaires entre deux arrets consecutifs ;
- durees de trajet ;
- references route/trip/service ;
- correspondances depuis `transfers.txt`.

Exemple de sortie simplifiee :

```json
{
  "routes": [],
  "stations": [],
  "stops": [],
  "edges": [],
  "transfers": []
}
```

## Algorithmes graphe

### `scripts/graph_algorithms/shortest_path.py`

Implemente Dijkstra horaire.

Il utilise :

- l'heure de depart demandee ;
- les arcs horaires ;
- les temps d'attente ;
- les correspondances.

Objectif : trouver l'arrivee la plus tot possible.

### `scripts/graph_algorithms/astar.py`

Implemente A* optionnel.

Il ajoute une heuristique geographique basee sur la distance a vol d'oiseau
entre l'arret courant et la destination. L'heuristique sert uniquement a
comparer les performances avec Dijkstra.

### `scripts/graph_algorithms/compare.py`

Lance Dijkstra et A* sur la meme requete et retourne :

- le resultat de chaque algorithme ;
- le nombre d'etats explores ;
- les temps de calcul.

### `scripts/graph_algorithms/connectivity.py`

Teste si le graphe de stations est relie avec un parcours BFS.

### `scripts/graph_algorithms/kruskal.py`

Construit un arbre couvrant minimum. Il sert a visualiser une structure de
connexion minimale du reseau.

## Empreinte carbone

Le front calcule une estimation par voyageur pour chaque trajet trouve.

Principe :

1. garder seulement les segments `ride` du resultat ;
2. mesurer la distance approximative entre l'arret de depart et l'arret d'arrivee
   avec les coordonnees GTFS ;
3. additionner les distances ;
4. appliquer un facteur d'emission en kgCO2e par kilometre et par personne.

Facteur utilise :

```text
Metro : 0,0042 kgCO2e / km / personne
RER   : 0,0042 kgCO2e / km / personne
```

La source est ADEME Impact CO2, qui expose le facteur `Metro` a
`0,0042 kgCO2e/km/personne`. Le RER n'est pas fourni comme mode separe dans
l'API Impact CO2 utilisee ici ; le projet applique donc le meme facteur ferre
urbain au RER. Cette constante est centralisee dans `public/main.js`.

## Tests

Les tests unitaires utilisent `tests/fixtures/simple_gtfs/`.

Commande :

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Ils verifient :

- parsing des heures et dates ;
- filtrage metro/RER ;
- construction du graphe ;
- Dijkstra horaire ;
- A* ;
- comparaison ;
- connexite ;
- Kruskal.

## Build front

Commande :

```bash
npm run build
```

Vite produit `dist/` avec :

- `index.html` ;
- `main.js` ;
- `styles.css` ;
- `data/network.json`.
