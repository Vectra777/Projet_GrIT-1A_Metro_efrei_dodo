# Projet GrIT 1A - Metro Efrei Dodo

L'objectif du projet est de construire une base propre pour exploiter les
donnees GTFS Ile-de-France Mobilites, produire un graphe metro/RER compact,
puis brancher une interface web de recherche d'itineraire.

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
├── src/
│   ├── main.jsx
│   └── styles.css
├── index.html
├── package.json
├── vite.config.js
└── tests/
    ├── fixtures/
    │   └── simple_gtfs/
    │       ├── calendar.txt
    │       ├── calendar_dates.txt
    │       ├── routes.txt
    │       ├── stop_times.txt
    │       ├── stops.txt
    │       ├── transfers.txt
    │       └── trips.txt
    ├── test_build_network.py
    ├── test_graph_algorithms.py
    └── test_filter_gtfs.py
```

## Avancement

Fait :

- parser les dates et heures GTFS ;
- filtrer les lignes metro/RER du perimetre ;
- charger les trips et calendriers utiles ;
- construire un graphe horaire compact avec stations, arrets, arcs horaires et correspondances ;
- calculer un itineraire avec Dijkstra horaire ;
- comparer Dijkstra avec A* optionnel ;
- tester la connexite du graphe ;
- construire un arbre couvrant minimum avec Kruskal ;
- ajouter une preview Vite/React de l'interface cible ;
- couvrir le pipeline Python avec des tests unitaires.

En cours / prochaines etapes :

- brancher le front sur `build/network.json` et les algorithmes Python ;
- afficher les vrais trajets et correspondances dans l'interface ;
- afficher le resultat de connexite et l'arbre couvrant dans la preview.

## Données

Le dossier `data/` vient du projet de référence.

Les données principales sont dans :

```text
data/raw/gtfs-idfm-2024/
```

Elles suivent le format GTFS d'Ile-de-France Mobilites. Le pipeline utilise
maintenant `routes.txt`, `trips.txt`, `calendar.txt`, `calendar_dates.txt`,
`stops.txt`, `stop_times.txt` et `transfers.txt`.

Les règles de filtrage sont :

- métro : `route_type = 1` ;
- RER : `route_type = 2` avec `agency_id = IDFM:71` ;
- les autres modes sont ignorés.

## Filtrage GTFS

Le script de filtrage est :

```text
scripts/filter_gtfs.py
```

Il sert a produire un JSON intermediaire lisible pour verifier que le perimetre
GTFS est correct. Il sait actuellement :

- parser une heure GTFS comme `08:15:30` en secondes ;
- accepter les heures GTFS après minuit comme `25:10:00` ;
- parser une date GTFS comme `20240227` ;
- lire un fichier CSV GTFS en UTF-8 ;
- filtrer et normaliser les lignes metro/RER depuis `routes.txt` ;
- charger les trajets de `trips.txt` uniquement pour les lignes conservées ;
- charger les services de `calendar.txt` utilisés par ces trajets ;
- charger les exceptions de service depuis `calendar_dates.txt`.

Exemple d'utilisation :

```bash
python3 scripts/filter_gtfs.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/routes_summary.json
```

Sans `--output`, le JSON est affiché dans le terminal :

```bash
python3 scripts/filter_gtfs.py --gtfs-dir data/raw/gtfs-idfm-2024
```

## Preview front-end

Un front-end Vite statique montre l'interface cible pendant que les algorithmes
de recherche sont branches progressivement.

Installation et lancement :

```bash
npm install
npm run dev
```

La preview ne depend pas encore des donnees generees. Elle montre le parcours
utilisateur cible : recherche d'itineraire, panneau de resultats, outils de
connexite/Kruskal et progression du projet.

## Graphe horaire

Le script de construction du graphe est :

```text
scripts/build_network.py
```

Ce fichier est volontairement court : il gere seulement la ligne de commande et
l'ecriture JSON. La logique est separee dans `scripts/gtfs_pipeline/` :

- `common.py` : constantes, lecture CSV, parsing date/heure ;
- `routes.py` : routes et trips ;
- `services.py` : calendriers et masques de services actifs ;
- `stops.py` : arrets, stations parentes et index ;
- `network.py` : assemblage du graphe, arcs horaires et transferts.

Il construit `build/network.json` depuis les fichiers GTFS utiles :

- `routes.txt` pour garder les lignes metro/RER ;
- `trips.txt` pour connaitre les trajets ;
- `calendar.txt` et `calendar_dates.txt` pour calculer les services actifs ;
- `stops.txt` pour regrouper les quais dans leurs stations commerciales ;
- `stop_times.txt` pour creer les arcs horaires entre arrets consecutifs ;
- `transfers.txt` pour ajouter les correspondances.

Commande :

```bash
python3 scripts/build_network.py
```

Il est aussi possible de choisir les chemins :

```bash
python3 scripts/build_network.py \
  --gtfs-dir data/raw/gtfs-idfm-2024 \
  --output build/network.json
```

## Algorithmes graphe

Les algorithmes sont separes dans `scripts/graph_algorithms/` :

- `shortest_path.py` : Dijkstra horaire sur les arrets, avec attente du prochain passage et correspondances ;
- `astar.py` : A* optionnel avec heuristique geographique ;
- `compare.py` : comparaison Dijkstra/A* sur une meme requete ;
- `connectivity.py` : parcours BFS pour verifier si toutes les stations sont atteignables ;
- `kruskal.py` : arbre couvrant minimum sur les arcs de stations.

Le Dijkstra travaille sur les `edges` horaires et les `transfers` du
`network.json`. Les tests verifient qu'il choisit l'arrivee la plus tot, meme
si une correspondance a pied est plus rapide que l'attente d'un train.

A* utilise la distance a vol d'oiseau entre arrets comme borne optimiste du
temps restant. Il est garde comme option de comparaison : Dijkstra reste la
reference de correction, A* sert a mesurer si l'heuristique reduit le nombre
d'arrets explores sans changer le resultat.

## Tests

Les tests utilisent un petit fixture GTFS minimal dans :

```text
tests/fixtures/simple_gtfs/
```

Lancer les tests :

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Les tests vérifient pour l'instant :

- le parsing des heures GTFS ;
- le parsing des dates GTFS ;
- le rejet des heures invalides ;
- le filtrage des lignes métro/RER ;
- la normalisation des couleurs ;
- le filtrage des trajets par ligne conservée ;
- le filtrage des calendriers et exceptions par service utilisé ;
- la construction d'un graphe horaire compact avec stations, arcs et transferts ;
- Dijkstra horaire, A* optionnel, comparaison des deux, connexite BFS et Kruskal ;
- le format JSON produit.
