# Projet GrIT 1A - Métro Efrei Dodo

L'objectif de cette première étape est volontairement limité : construire une
base Python propre et testée pour lire les données GTFS, parser les formats
utiles, puis filtrer les lignes qui appartiennent au périmètre du projet.

## Structure actuelle

```text
.
├── data/
│   └── raw/
│       ├── Version1/
│       ├── examples/
│       └── gtfs-idfm-2024/
├── scripts/
│   └── filter_gtfs.py
└── tests/
    ├── fixtures/
    │   └── simple_gtfs/
    │       └── routes.txt
    └── test_filter_gtfs.py
```

## Données

Le dossier `data/` vient du projet de référence.

Les données principales sont dans :

```text
data/raw/gtfs-idfm-2024/
```

Elles suivent le format GTFS d'Ile-de-France Mobilités. Pour cette première
étape, le script utilise seulement `routes.txt`.

Les règles de filtrage sont :

- métro : `route_type = 1` ;
- RER : `route_type = 2` avec `agency_id = IDFM:71` ;
- les autres modes sont ignorés.

## Script Python

Le script principal est :

```text
scripts/filter_gtfs.py
```

Il sait actuellement :

- parser une heure GTFS comme `08:15:30` en secondes ;
- accepter les heures GTFS après minuit comme `25:10:00` ;
- parser une date GTFS comme `20240227` ;
- lire un fichier CSV GTFS en UTF-8 ;
- filtrer et normaliser les lignes métro/RER depuis `routes.txt`.

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
- la normalisation des couleurs et du format JSON produit.

## Prochaines étapes

Les prochaines parties à implémenter seront :

1. charger `trips.txt` uniquement pour les lignes conservées ;
2. lire `calendar.txt` et `calendar_dates.txt` ;
3. charger `stops.txt` et gérer les stations parentes ;
4. transformer `stop_times.txt` en connexions entre arrêts consécutifs ;
5. ajouter les correspondances depuis `transfers.txt` ;
6. produire un premier graphe complet exploitable par l'application.
