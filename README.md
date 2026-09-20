# RitelAI: Retail Location Suitability Assessment for Jabodetabek

Processed spatial dataset for machine learning-based suitability assessment of retail expansion locations (Alfamart and Indomaret) in the Jakarta-Bogor-Depok-Tangerang metropolitan area.

**📖 Methods & results:** See the published paper in *IAENG IJCS*.

---

## Quick Start

### Access the data:

```python
import pandas as pd
import geopandas as gpd

# Load grid with predictors (685,318 rows per brand)
alfamart = pd.read_parquet("data/grid/grid_alfamart_x1_x35.parquet")
indomaret = pd.read_parquet("data/grid/grid_indomaret_x1_x35.parquet")

# Load geometries
geom = gpd.read_file("data/grid/grid_geometry_100m.gpkg", layer="grid_100m")

# Join
alfamart_geo = geom.merge(alfamart, on="GRID_ID", how="inner")

# Load sentiment features (outlet-level, before spatial propagation)
sentiment_alfa = pd.read_csv("data/sentiment/outlet_features_alfamart_x27_x35.csv")

# Load development/holdout split (block-disjoint, ~80/20)
split = pd.read_csv("data/partition/development_holdout_split.csv")

# Load candidate locations (Top 10%, 1%, 5% tiers with SHAP explanations)
candidates = gpd.read_file("data/candidates/candidates_alfamart_xgboost_top1_top5_top10.gpkg")
```

### Verify data integrity:

```bash
cd data/
sha256sum -c checksums.sha256
```

All files must show "OK".

---

## 📊 Dataset Overview

### Grid Analysis Tables

**`grid/grid_alfamart_x1_x35.parquet` · `grid/grid_indomaret_x1_x35.parquet`**

One row per 100 × 100 m grid cell. **685,318 rows per brand.**

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Unique cell key; joins to geometries and partition |
| `centroid_x`, `centroid_y` | float64 | Cell centroid, metres, EPSG:32748 |
| `BLOCK_ID` | int64 | 1 × 1 km spatial block; 7,278 distinct |
| `x1` … `x35` | float64 | Predictors; see DATA_DICTIONARY.md |
| `target_presence` | int8 | 1 if cell contains ≥1 outlet, else 0 |
| `WADMPR`, `WADMKK`, `WADMKC`, `WADMKD` | string | Admin boundaries (province, regency, district, village) |

**Expected totals:**

| Brand | Rows | Outlets (target=1) | Prevalence | Blocks |
|---|---|---|---|---|
| Alfamart | 685,318 | 3,632 | 0.530% | 7,278 |
| Indomaret | 685,318 | 3,481 | 0.508% | 7,278 |

> Alfamart count reflects the cached experimental target used in the paper. Rebuilding from the current outlet master gives 3,637 instead. **Use the shipped value (3,632) to match the paper exactly.**

---

### Geometries

**`grid/grid_geometry_100m.gpkg`**

Cell boundaries: one row per GRID_ID, polygon geometry in EPSG:32748.

```python
import geopandas as gpd, pandas as pd

# Load in two steps
geom = gpd.read_file("data/grid/grid_geometry_100m.gpkg", layer="grid_100m")
attrs = pd.read_parquet("data/grid/grid_alfamart_x1_x35.parquet")

# Join
grid = geom.merge(attrs, on="GRID_ID", how="inner")
```

---

### Sentiment Features

**`sentiment/outlet_features_alfamart_x27_x35.csv` · `sentiment/outlet_features_indomaret_x27_x35.csv`**

Outlet-level aggregated review data **before** spatial propagation to grids (see DATA_DICTIONARY.md for X27–X35 definitions).

| Column | Type | Description |
|---|---|---|
| `outlet_id` | string | Anonymised outlet key |
| `latitude`, `longitude` | float64 | Outlet position, EPSG:4326 |
| `n_reviews` | int | Total deduplicated reviews |
| `n_reviews_recent_12m` | int | Reviews in 12-month window (for X31) |
| `x27` … `x30` | float64 | Mean polarity [−1, 1] for stock, queue, price, service |
| `x31` | float64 | Mean star rating, recent 12m, fallback all |
| `x32` … `x35` | float64 | Sentiment change: newer half − older half |

**Row counts:**

| Brand | Outlets | With coordinates | With reviews | Reviews classified |
|---|---|---|---|---|
| Alfamart | 3,947 | 3,898 | 3,642 | 118,604 |
| Indomaret | 3,754 | 3,718 | 3,621 | 74,437 |

**⚠️ Zero is ambiguous** in X27–X30 and X32–X35: may mean neutral sentiment, no review mentioning that aspect, or too few dated reviews for change calculation. Use `n_reviews` and `n_reviews_recent_12m` to distinguish.

---

### Spatial Partitioning

**`partition/spatial_blocks_1km.csv`**

Maps 685,318 grid cells to 7,278 blocks (1 × 1 km). Used for fold-safe feature construction.

| Column | Description |
|---|---|
| `GRID_ID` | Cell key |
| `BLOCK_ID` | Block key |
| `block_row`, `block_col` | Block indices in projected grid |

---

**`partition/development_holdout_split.csv`**

**The file that makes reproducible evaluation possible.** Block-disjoint 80/20 split, selected to preserve target prevalence with zero block overlap.

| Partition | Blocks | Alfamart grids | Alfamart outlets | Indomaret grids | Indomaret outlets |
|---|---|---|---|---|---|
| Development | 5,822 | 548,111 | 2,904 | 548,272 | 2,785 |
| Holdout | 1,456 | 137,207 | 728 | 137,046 | 696 |

```python
# Verify zero overlap
dev_blocks = set(split[split["partition"] == "development"]["BLOCK_ID"])
hold_blocks = set(split[split["partition"] == "holdout"]["BLOCK_ID"])
assert dev_blocks & hold_blocks == set()  # Must be empty
```

---

### Candidate Locations

**`candidates/candidates_{brand}_{algorithm}_top1_top5_top10.gpkg`**

Four files: 2 brands × 2 algorithms (XGBoost, GeoXGBoost). Layer `{brand}_{algorithm}_candidates`, CRS EPSG:4326.

Each file contains the **Top 10% scored cells**, with Top 1% and Top 5% nested as flags.

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Cell key |
| `BRAND` | string | Alfamart or Indomaret |
| `ALGORITHM` | string | xgboost or geoxgboost |
| `PRED_PROBA` | float64 | Relative suitability score [0, 1] — **not a probability** |
| `PERCENTILE` | float64 | Percentile rank within eligible pool |
| `CAND_TOP1`, `CAND_TOP5`, `CAND_TOP10` | int8 | Tier flags (0 or 1) |
| `REC_LEVEL` | string | TOP1, TOP5, or TOP10 |
| `DIST_EXIST_M` | float64 | Metres to nearest same-brand outlet |
| `TOP1_FEAT` … `TOP7_FEAT` | string | Seven strongest local drivers (by abs SHAP) |
| `TOP1_XVAL` … `TOP7_XVAL` | float64 | Observed feature value |
| `TOP1_SHAP` … `TOP7_SHAP` | float64 | Signed SHAP contribution |
| `TOP1_DIR` … `TOP7_DIR` | string | Raises or lowers score |
| `SHAP_BASE` | float64 | Explainer base value |
| `SHAP_KIND` | string | `direct_tree_shap_xgboost` or `surrogate_shap_for_geoxgboost` |
| `WADMKK` | string | Regency or city |

**Candidate counts:**

| Brand | XGBoost Top 1% | Top 5% | Top 10% | GeoXGBoost Top 1% | Top 5% | Top 10% |
|---|---|---|---|---|---|---|
| Alfamart | 6,233 | 31,161 | 62,322 | 6,233 | 31,161 | 62,322 |
| Indomaret | 6,259 | 31,295 | 62,589 | 6,259 | 31,295 | 62,589 |

**Eligibility:** Cell qualifies if `target_presence == 0` **and** centroid is ≥250 m from nearest same-brand outlet. Applied *after* full-grid scoring.

Eligible pools: 623,220 (Alfamart), 625,928 (Indomaret).

---

## 📖 Understanding PRED_PROBA

`PRED_PROBA` measures how closely a cell resembles the feature signature of the existing outlet network. It is **NOT**:

- A probability that a store will open there
- A probability that a store would succeed
- A revenue, footfall, or profit estimate
- A substitute for site survey or feasibility analysis

About 0.1–0.2% of raw scores fell outside [0, 1] and were clipped. The output is a spatial index, not a calibrated probability.

---

## 🔍 File Manifest & Verification

| Path | Format | Size | Checksum |
|---|---|---|---|
| `grid/grid_geometry_100m.gpkg` | GeoPackage | ~250–350 MB | idem |
| `sentiment/outlet_features_alfamart_x27_x35.csv` | UTF-8 CSV | ~1–2 MB | idem |
| `sentiment/outlet_features_indomaret_x27_x35.csv` | UTF-8 CSV | ~1–2 MB | idem |
| `partition/spatial_blocks_1km.csv` | CSV | ~15–20 MB | idem |
| `partition/development_holdout_split.csv` | CSV | <1 MB | idem |
| `candidates/candidates_alfamart_xgboost_*.gpkg` | GeoPackage | ~30–60 MB | idem |
| `candidates/candidates_alfamart_geoxgboost_*.gpkg` | GeoPackage | ~30–60 MB | idem |
| `candidates/candidates_indomaret_xgboost_*.gpkg` | GeoPackage | ~30–60 MB | idem |
| `candidates/candidates_indomaret_geoxgboost_*.gpkg` | GeoPackage | ~30–60 MB | idem |

**⚠️ All coordinates are EPSG:32748 (WGS 84 / UTM zone 48S) unless stated otherwise.**

Candidate layers are additionally reprojected to EPSG:4326 for web display.

**Cite as:**

```bibtex
@dataset{ritelai2026,
  author = {Budi Carto},
  title = {RitelAI: Retail Location Suitability Assessment for Jabodetabek},
  year = {2026},
  url = {https://github.com/budioibud/ritel-ai},
  doi = {10.5281/zenodo.XXXXX}
}
```

---

## 📚 Documentation

- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** — Full definition of X1–X35 predictors, data sources, construction methods
- **[REPRODUCE.md](REPRODUCE.md)** — Methodology overview and key reproduction metrics
- **[LICENSE](LICENSE)** — MIT license (applies to any derivative code)
- **[LICENSE-DATA.md](LICENSE-DATA.md)** — CC BY 4.0 for data + third-party attribution

---

## 🤝 Contact & Support

For questions about the dataset or to report issues:

- **Email**: budioibud@gmail.com

---

## ⚠️ Limitations & Disclaimer

The data is provided **as-is**, without warranty of any kind.

- The suitability score is a relative spatial index, not a probability
- Not a prediction of commercial success
- Field survey, parcel availability, zoning checks, and financial feasibility analysis are required before any real siting decision
- No liability accepted for commercial decisions based on this data

---

**Last updated:** 2024-09-20  
**Repository:** https://github.com/budioibud/ritel-ai
**Archive DOI:** https://doi.org/10.5281/zenodo.XXXXX
