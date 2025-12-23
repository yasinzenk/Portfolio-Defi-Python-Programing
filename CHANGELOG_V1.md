# Changelog V1 - Modifications apportées

Ce document décrit toutes les modifications effectuées sur la V1 par rapport à la version originale.

## Résumé des changements majeurs

1. **Remplacement de l'API CoinGecko par CryptoCompare**
2. **Renommage `coingecko_id` → `crypto_id`** (plus générique)
3. **Ajout de la fonction `portfolio_volatility()`**
4. **Création des tests unitaires** (27 tests)
5. **Corrections PEP 8** sur tous les fichiers
6. **Restructuration du projet** (V0 et V1 séparées et autonomes)

---

## Changement d'API : CoinGecko → CryptoCompare

### Pourquoi ce changement ?

L'API CoinGecko avait des problèmes de rate limiting (erreurs 429). CryptoCompare offre :

- **100 appels/heure** sans clé API
- **250 000 appels/mois** avec une clé gratuite

### Détails techniques

| Aspect | CoinGecko (ancien) | CryptoCompare (nouveau) |
|--------|-------------------|------------------------|
| Base URL | `api.coingecko.com/api/v3` | `min-api.cryptocompare.com/data` |
| Prix actuel | `/simple/price?ids=ethereum` | `/price?fsym=ETH&tsyms=USD` |
| Historique | `/coins/{id}/market_chart` | `/v2/histoday?fsym=ETH&tsym=USD` |
| Identifiant | Slug (`ethereum`, `bitcoin`) | Symbole (`ETH`, `BTC`) |

---

## Modifications par fichier

### `data_fetcher.py`

**Réécriture complète** - Nouvelle classe `CryptoCompareClient` remplaçant `CoingeckoClient`

---

### `portfolio_core.py`

Renommage `coingecko_id` → `crypto_id`

---

### `data_loader.py`

Lecture de `crypto_id` au lieu de `coingecko_id` dans le JSON

---

### `risk_analyzer.py`

Ajout de la fonction `portfolio_volatility()` utilisant la matrice de covariance

---

### `main.py`

- Import de `CryptoCompareClient`
- Utilisation de `crypto_id`
- Affichage de la volatilité portfolio

---

### `data/sample_portfolio.json`

Avant : `{"symbol": "ETH", "coingecko_id": "ethereum", "amount": 1.5}`

Après : `{"symbol": "ETH", "crypto_id": "ETH", "amount": 1.5}`

---

### `tests/` (nouveau)

27 tests unitaires : `pytest tests/ -v`

---

## Comment tester

```bash
cd v1
pip install -r requirements.txt
python main.py --portfolio data/sample_portfolio.json --days 30
pytest tests/ -v
```
