# CHANGELOG V2 — DeFi Portfolio Analyzer

Ce document détaille **toutes les améliorations et additions** apportées dans la version V2 par rapport à V1.

---

## Vue d'ensemble

| Aspect | V1 | V2 |
|--------|----|----|
| **Modules Python** | 7 | 12 (+5 nouveaux) |
| **Fichiers de tests** | 6 | 10 (+4 nouveaux) |
| **Lignes de code** | ~2000 | ~4500+ |
| **Configuration** | Hardcoded | YAML + CLI overrides |
| **Cache** | ❌ | ✅ TTL-based |
| **Optimisation** | ❌ | ✅ Markowitz (3 modes) |
| **Exports** | Console uniquement | CSV/JSON |
| **Visualisations** | 1 plot simple | 4 plots + HTML report |

---

## 1. Nouveaux Modules

### 1.1 `cache.py` — Système de Cache Local

**Objectif** : Éviter les appels API répétitifs et permettre le mode offline.

**Fonctions principales** :
- `load_cached_series(path, ttl_seconds)` — Charge une série de prix depuis le cache si elle n'est pas expirée
- `load_cached_series_allow_stale(path)` — Charge depuis le cache sans vérifier la fraîcheur (mode offline)
- `save_series(path, series)` — Sauvegarde une série de prix en JSON avec timestamp

**Format de stockage** :
```json
{
  "timestamp": 1703808000.0,
  "prices": [
    {"date": "2024-12-01", "price": 45000.0},
    {"date": "2024-12-02", "price": 45500.0}
  ]
}
```

**Avantages** :
- Réduction des appels API (rate limiting CryptoCompare)
- Reproductibilité des résultats
- Mode `--offline` pour travailler sans connexion

---

### 1.2 `config.py` — Gestion de Configuration Typée

**Objectif** : Centraliser tous les paramètres configurables et éviter les valeurs hardcodées.

**Dataclasses implémentées** :
| Classe | Champs |
|--------|--------|
| `AppConfig` | `name`, `log_file` |
| `DataConfig` | `default_portfolio_path`, `cache_dir`, `cache_ttl_seconds` |
| `RiskConfig` | `days`, `risk_free_rate`, `confidence` |
| `OptimizationConfig` | `target_return`, `max_weight_per_asset`, `short_selling_allowed` |
| `VisualizationConfig` | `theme`, `output_dir` |
| `Config` | Agrège toutes les sections ci-dessus |

**Fonctionnement** :
1. Chargement des valeurs par défaut internes (`_default_config_dict()`)
2. Chargement du fichier `config.yml` (optionnel)
3. Merge des deux dictionnaires (`_merge_dicts()`)
4. Validation et construction des dataclasses typées

**Fichier `config.yml`** :
```yaml
app:
  name: "DeFi Portfolio Risk Analyzer V2"
  log_file: "portfolio_analyzer_v2.log"

data:
  default_portfolio_path: "data/sample_portfolio.json"
  cache_dir: "cache"
  cache_ttl_seconds: 3600

risk:
  days: 30
  risk_free_rate: 0.02
  confidence: 0.95

optimization:
  target_return: 0.10
  max_weight_per_asset: 0.30
  short_selling_allowed: false

visualization:
  theme: "plotly_dark"
  output_dir: "figures"
```

---

### 1.3 `optimizer.py` — Optimisation de Portefeuille (Markowitz)

**Objectif** : Proposer des allocations optimales selon différents objectifs.

**Classe de résultat** :
```python
@dataclass(frozen=True)
class OptimizationResult:
    weights: Dict[str, float]      # Allocation par actif
    expected_return: float         # Rendement annualisé attendu
    volatility: float              # Volatilité annualisée
    sharpe: float                  # Ratio de Sharpe
```

**Trois modes d'optimisation** :

| Mode | Fonction | Description |
|------|----------|-------------|
| `min-vol` | `min_variance()` | Minimise la variance du portefeuille |
| `max-sharpe` | `max_sharpe()` | Maximise le ratio rendement/risque |
| `target-return` | `target_return()` | Minimise la variance pour un rendement cible |

**Frontière efficiente** :
- `efficient_frontier(returns_df, num_points=20, bounds=None)` 
- Calcule plusieurs points optimaux entre le rendement min et max faisables
- Gère les cas infaisables avec des logs et skip automatique

**Contraintes supportées** :
- Somme des poids = 1 (contrainte d'égalité)
- Bornes par actif : `[0, max_weight]` (pas de short-selling par défaut)
- Configurable via `optimization.max_weight_per_asset`

**Algorithme** : SLSQP (Sequential Least Squares Programming) via `scipy.optimize.minimize`

---

### 1.4 `output_writer.py` — Exports Structurés

**Objectif** : Sauvegarder les résultats d'analyse dans des formats réutilisables.

**Fonctions d'export** :
| Fonction | Output |
|----------|--------|
| `write_metrics_csv()` | Métriques par actif en CSV |
| `write_metrics_json()` | Métriques par actif en JSON (records) |
| `write_allocation_csv()` | Poids d'allocation en CSV |
| `write_allocation_json()` | Poids d'allocation en JSON |
| `write_dataframe_csv()` | DataFrame générique en CSV |
| `write_dataframe_json()` | DataFrame générique en JSON (orient=split) |

**Fichiers générés** :
```
outputs/
├── metrics.csv          # Volatilité, Sharpe, VaR par actif
├── metrics.json
├── allocation.csv       # Poids actuels
├── allocation.json
├── correlation.csv      # Matrice de corrélation
├── correlation.json
└── optimal_allocation.csv/json  # Résultat de l'optimisation
```

---

### 1.5 `report_writer.py` — Génération de Rapport HTML

**Objectif** : Produire un rapport interactif et compréhensible pour les utilisateurs non-finance.

**Contenu du rapport** :
1. **Résumé du portefeuille** : Nom, valeur totale, date de génération
2. **Paramètres utilisés** : Jours, taux sans risque, niveau de confiance
3. **Métriques de risque** : Tableau avec volatilité, Sharpe, VaR par actif
4. **Allocation actuelle** : Tableau des poids
5. **Matrice de corrélation** : Tableau interactif
6. **Visualisations** : Images PNG intégrées (risk bars, heatmap, allocation, frontier)
7. **Interprétation** : Paragraphes générés automatiquement basés sur les données
8. **Glossaire** : Définitions des termes financiers pour les non-experts

**Fonctions d'interprétation** :
- `_describe_portfolio_summary()` — Résumé des métriques agrégées
- `_describe_volatility()` — Analyse de la distribution des volatilités
- `_describe_sharpe()` — Commentaire sur les ratios Sharpe
- `_describe_var()` — Explication des VaR et risque de perte
- `_describe_weights()` — Analyse de la concentration/diversification
- `_describe_correlation()` — Interprétation de la diversification
- `_describe_frontier()` — Comparaison avec la frontière efficiente

---

## 2. Modules Enrichis

### 2.1 `data_fetcher.py` — Intégration du Cache

**Ajouts par rapport à V1** :
- Intégration avec `cache.py` pour stocker les prix historiques
- Support du mode `--offline` (utilise uniquement le cache)
- Support du mode `--refresh-cache` (ignore le cache et rafraîchit)
- Configuration du TTL via `config.yml`

**Logique de fetch** :
```
1. Si --offline → charge depuis cache (même expiré)
2. Si --refresh-cache → ignore le cache, fetch API
3. Sinon → charge cache si frais, sinon fetch API
4. Sauvegarde dans le cache après fetch réussi
```

---

### 2.2 `visualizer.py` — Nouvelles Visualisations

**V1** : Un seul plot simple de volatilité

**V2** : 4 plots professionnels avec matplotlib :

| Fonction | Description | Output |
|----------|-------------|--------|
| `plot_risk_bars()` | Graphique en barres (volatilité + Sharpe) | `risk_bars.png` |
| `plot_correlation_heatmap()` | Heatmap colorée de corrélation | `correlation_heatmap.png` |
| `plot_allocation_pie()` | Graphique circulaire des poids | `allocation.png` |
| `plot_efficient_frontier()` | Courbe rendement/risque | `frontier.png` |

**Améliorations techniques** :
- Backend `Agg` pour génération sans GUI
- Création automatique des répertoires parents
- DPI ajusté (120) pour netteté
- Colorscheme cohérent (`#4C78A8`, `#F58518`, `coolwarm`)

---

### 2.3 `main.py` — CLI Enrichie avec Sous-commandes

**V1** : Un seul script avec `argparse` simple

**V2** : Architecture avec sous-commandes :

```bash
python v2/main.py analyze [options]   # Analyse complète
python v2/main.py optimize [options]  # Optimisation
python v2/main.py visualize [options] # Visualisations + rapport
```

**Nouvelles options CLI** :
| Option | Description |
|--------|-------------|
| `--outdir` | Répertoire de sortie pour les fichiers |
| `--format` | Format d'export (`csv` ou `json`) |
| `--pretty` | Affichage console formaté (tableaux lisibles) |
| `--offline` | Mode hors-ligne (cache uniquement) |
| `--refresh-cache` | Force le rafraîchissement du cache |
| `--mode` | Mode d'optimisation (`min-vol`, `max-sharpe`, `target-return`) |
| `--target-return` | Rendement cible pour le mode `target-return` |
| `--report` | Génère le rapport HTML avec `visualize` |
| `--log-level` | Niveau de log (DEBUG, INFO, WARNING, ERROR) |
| `--quiet` / `--verbose` | Raccourcis pour niveaux de verbosité |

---

## 3. Suite de Tests Étendue

### Nouveaux fichiers de tests (V2)

| Fichier | Tests couverts |
|---------|----------------|
| `test_cache.py` | Round-trip cache, expiration TTL, fichiers corrompus |
| `test_config.py` | Chargement YAML, merge avec défauts, validation |
| `test_optimizer.py` | Contraintes, convergence, bornes par actif |
| `test_cli.py` | Sous-commandes, parsing d'arguments, mocking API |

### Tests enrichis (déjà existants en V1)

| Fichier | Ajouts V2 |
|---------|-----------|
| `test_data_fetcher.py` | Tests avec cache, mode offline |
| `test_visualizer.py` | Vérification génération des 4 plots |
| `test_risk_analyzer.py` | Edge cases (valeurs nulles, séries courtes) |

**Exécution** :
```bash
# Depuis v2/
pytest tests/ -v

# Depuis la racine
pytest v2/tests/ -v
```

---

## 4. Améliorations de l'Architecture

### 4.1 Séparation des responsabilités

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLI (main.py)                         │
│                     Sous-commandes + orchestration              │
└───────────────┬─────────────────┬───────────────────────────────┘
                │                 │
    ┌───────────▼───────┐ ┌───────▼────────┐
    │   Configuration   │ │  Data Loading  │
    │   (config.py)     │ │ (data_loader)  │
    └───────────────────┘ └───────┬────────┘
                                  │
              ┌───────────────────▼───────────────────┐
              │            Data Fetcher               │
              │    (data_fetcher.py + cache.py)       │
              └───────────────────┬───────────────────┘
                                  │
              ┌───────────────────▼───────────────────┐
              │           Risk Analyzer               │
              │        (risk_analyzer.py)             │
              └──────┬───────────────────┬────────────┘
                     │                   │
         ┌───────────▼──────┐ ┌──────────▼──────────┐
         │    Optimizer     │ │     Visualizer      │
         │  (optimizer.py)  │ │   (visualizer.py)   │
         └──────────────────┘ └──────────┬──────────┘
                                         │
                   ┌─────────────────────┼─────────────────────┐
                   │                     │                     │
           ┌───────▼───────┐   ┌─────────▼─────────┐   ┌───────▼───────┐
           │ Output Writer │   │   Report Writer   │   │     Plots     │
           │ (CSV / JSON)  │   │      (HTML)       │   │     (PNG)     │
           └───────────────┘   └───────────────────┘   └───────────────┘
```

### 4.2 Gestion des chemins

- Résolution automatique des chemins relatifs depuis la racine du projet
- `pathlib.Path` utilisé partout pour compatibilité cross-platform
- Création automatique des répertoires parents (`mkdir(parents=True)`)

---

## 5. Résumé des Dépendances Ajoutées

```txt
# requirements.txt V2
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0      # NOUVEAU - pour l'optimisation SLSQP
matplotlib>=3.7.0
requests>=2.28.0
pyyaml>=6.0.0      # NOUVEAU - pour la configuration YAML
pytest>=7.0.0
```

---

## 6. Commandes Rapides

```bash
# Analyse complète avec export CSV
python v2/main.py analyze --portfolio data/sample_portfolio.json --format csv --outdir outputs --pretty

# Optimisation max-sharpe
python v2/main.py optimize --portfolio data/sample_portfolio.json --mode max-sharpe --outdir outputs

# Génération des visualisations + rapport HTML
python v2/main.py visualize --portfolio data/sample_portfolio.json --outdir figures --report

# Mode offline (utilise uniquement le cache)
python v2/main.py analyze --portfolio data/sample_portfolio.json --offline

# Rafraîchir le cache
python v2/main.py analyze --portfolio data/sample_portfolio.json --refresh-cache
```

---

## 7. Points Techniques Clés

1. **Annualisation** : 365 jours/an (crypto = 24/7)
2. **VaR historique** : Quantile empirique (non-paramétrique)
3. **Optimisation** : SLSQP avec tolérance `1e-9`, max 2000 itérations
4. **Cache TTL** : 1 heure par défaut (configurable)
5. **Logs** : Fichier `portfolio_analyzer_v2.log` + console configurable

---

*Document généré le 29 décembre 2024*
