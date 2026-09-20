# `data/` — File Manifest

Every file in the RitelAI dataset, what it contains, and how to verify integrity.

Complete predictor definitions (X1–X35) are in [`../DATA_DICTIONARY.md`](../DATA_DICTIONARY.md).

---

## Verify Before Use

```bash
sha256sum -c checksums.sha256
```

All files must return "OK". If any checksum mismatches, the file is corrupt—download again.

Record the SHA-256 hash of every file before publishing. Checksums are listed in this directory as `checksums.sha256`.

---

## File Manifest

### Grid Analysis Tables

#### `grid/grid_alfamart_x1_x35.parquet` · `grid/grid_indomaret_x1_x35.parquet`

The analysis table. One row per grid cell.

- **Format:** Parquet (snappy compression)
- **Size:** ~80–120 MB each
- **Rows:** 685,318 per brand
- **Columns:** 39 (GRID_ID, centroid_x/y, BLOCK_ID, x1–x35, target_presence, WADMPR/WADMKK/WADMKC/WADMKD)

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Unique cell key; joins to `grid_geometry_100m.gpkg` and to `partition/` |
| `centroid_x` | float64 | Centroid easting, metres, EPSG:32748 |
| `centroid_y` | float64 | Centroid northing, metres, EPSG:32748 |
| `BLOCK_ID` | int64 | 1 × 1 km spatial block key, 7,278 distinct values |
| `x1` … `x35` | float64 | Predictors; see the data dictionary |
| `target_presence` | int8 | 1 if the cell contains at least one mapped outlet of this brand, else 0 |
| `WADMPR` | string | Province (provinsi) |
| `WADMKK` | string | Regency or city (kabupaten/kota) |
| `WADMKC` | string | District (kecamatan) |
| `WADMKD` | string | Village (kelurahan/desa) |

**X1–X23 are identical between brands.** X24–X26 and X27–X35 are brand-specific.

**Expected totals:**

| Brand | Rows | Outlets (target=1) | Prevalence | Blocks |
|---|---|---|---|---|
| Alfamart | 685,318 | 3,632 | 0.530% | 7,278 |
| Indomaret | 685,318 | 3,481 | 0.508% | 7,278 |

> ⚠️ **Alfamart count note:** The 3,632 count reflects the cached experimental target used during model development. Rebuilding from the current outlet master gives 3,637. **Use 3,632 to match the published paper.**

**Python (pandas + geopandas):**

```python
import pandas as pd
import geopandas as gpd

# Load grid attributes
attrs = pd.read_parquet("grid/grid_alfamart_x1_x35.parquet")

# Load geometries separately (to keep grid matrix light)
geom = gpd.read_file("grid/grid_geometry_100m.gpkg", layer="grid_100m")

# Join geometries with attributes
grid = geom.merge(attrs, on="GRID_ID", how="inner")
```

---

#### `grid/grid_geometry_100m.gpkg`

Cell boundaries: 100 × 100 m polygon geometries.

- **Format:** GeoPackage (GeoPackage Container)
- **Size:** ~250–350 MB
- **Layer:** `grid_100m`
- **Rows:** 685,318
- **Columns:** 2 (GRID_ID, geometry)
- **CRS:** EPSG:32748

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Cell key (joins to attribute tables) |
| `geometry` | Polygon | Cell boundary, EPSG:32748 |

Kept separate from attribute tables to reduce memory footprint during analysis (685K-row parquet stays light).

---

### Sentiment Features

#### `sentiment/outlet_features_alfamart_x27_x35.csv` · `sentiment/outlet_features_indomaret_x27_x35.csv`

Outlet-level aggregated review features, **before propagation** to grids within 500 m. Used to construct X27–X35.

- **Format:** CSV, UTF-8 encoding
- **Size:** ~1–2 MB each
- **Delimiter:** Comma
- **Rows:** ~3,900–4,000 per brand

| Column | Type | Description |
|---|---|---|
| `outlet_id` | string | Anonymised outlet key, stable within this release |
| `latitude`, `longitude` | float64 | Outlet position, EPSG:4326 (decimal degrees) |
| `n_reviews` | int | Total deduplicated reviews used in aggregation |
| `n_reviews_recent_12m` | int | Reviews falling inside the 12-month window (for X31 and recent-window sentiment) |
| `x27` | float64 | Mean polarity [−1, 1] for reviews mentioning stock |
| `x28` | float64 | Mean polarity for reviews mentioning queue or cashier |
| `x29` | float64 | Mean polarity for reviews mentioning price |
| `x30` | float64 | Mean polarity for reviews mentioning service |
| `x31` | float64 | Mean star rating (most recent 12 months, fallback to all valid ratings) |
| `x32` | float64 | Stock sentiment change: newer-half mean − older-half mean |
| `x33` | float64 | Queue sentiment change: idem |
| `x34` | float64 | Price sentiment change: idem |
| `x35` | float64 | Service sentiment change: idem |

**Row counts:**

| Brand | Outlet records | With valid coordinates | Outlets with reviews | Reviews classified |
|---|---|---|---|---|
| Alfamart | 3,947 | 3,898 | 3,642 | 118,604 |
| Indomaret | 3,754 | 3,718 | 3,621 | 74,437 |

Outlet records exceed outlets-with-reviews because the outlet master includes locations not yet reviewed.

**⚠️ Zero is ambiguous** in X27–X30 and X32–X35. Zero may mean:
- Neutral sentiment was observed for that aspect
- No review mentioned that aspect (e.g., no stock-related reviews)
- Too few dated reviews to compute change

Use `n_reviews` and `n_reviews_recent_12m` to distinguish. Gridded X27–X35 do not preserve this detail.

---

### Spatial Partitioning

#### `partition/spatial_blocks_1km.csv`

Maps grid cells to 1 × 1 km spatial blocks.

- **Format:** CSV
- **Size:** ~15–20 MB
- **Rows:** 685,318 (one per grid cell)
- **Columns:** 4

| Column | Description |
|---|---|
| `GRID_ID` | Cell key |
| `BLOCK_ID` | 1 × 1 km block key (7,278 distinct blocks) |
| `block_row` | Row index of block in projected grid |
| `block_col` | Column index of block in projected grid |

Used for fold-safe feature construction: `GroupKFold` on `BLOCK_ID` prevents data leakage by ensuring validation-region blocks never contribute to training features.

---

#### `partition/development_holdout_split.csv`

**The file that makes the paper reproducible.** Block-disjoint 80/20 split preserving target class prevalence.

- **Format:** CSV
- **Size:** <1 MB
- **Rows:** 7,278 (one per block)
- **Columns:** 2

| Column | Description |
|---|---|
| `BLOCK_ID` | 1 × 1 km block key |
| `partition` | Either "development" or "holdout" |

**Partition summary:**

| Partition | Blocks | Alfamart cells | Alfamart outlets | Indomaret cells | Indomaret outlets |
|---|---|---|---|---|---|
| Development | 5,822 | 548,111 | 2,904 | 548,272 | 2,785 |
| Holdout | 1,456 | 137,207 | 728 | 137,046 | 696 |

**Invariants:**
- Block overlap is zero by construction
- The holdout was not used for ablation, pruning, parameter selection, or model choice until the single final evaluation
- Cross-validation during tuning used only the development set with 5-fold GroupKFold on BLOCK_ID

```python
# Verify zero overlap
import pandas as pd

split = pd.read_csv("partition/development_holdout_split.csv")
dev = split[split["partition"] == "development"]["BLOCK_ID"].unique()
hold = split[split["partition"] == "holdout"]["BLOCK_ID"].unique()

assert len(set(dev) & set(hold)) == 0, "Block overlap detected!"
```

---

### Candidate Locations

#### `candidates/candidates_{brand}_{algorithm}_top1_top5_top10.gpkg`

Four files: 2 brands × 2 algorithms. Each contains the **Top 10%** of scored cells, with Top 1% and Top 5% nested as flags.

- **Format:** GeoPackage
- **Size:** ~30–60 MB each
- **CRS:** EPSG:4326 (WGS 84, decimal degrees — for web display)
- **Layer:** `{brand}_{algorithm}_candidates`

**Files:**
1. `candidates_alfamart_xgboost_top1_top5_top10.gpkg`
2. `candidates_alfamart_geoxgboost_top1_top5_top10.gpkg`
3. `candidates_indomaret_xgboost_top1_top5_top10.gpkg`
4. `candidates_indomaret_geoxgboost_top1_top5_top10.gpkg`

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Cell key |
| `BRAND` | string | Alfamart or Indomaret |
| `ALGORITHM` | string | xgboost or geoxgboost |
| `PRED_PROBA` | float64 | Relative suitability score [0, 1] — **not a probability** |
| `PERCENTILE` | float64 | Percentile rank within this brand's eligible-grid pool |
| `CAND_TOP1` | int8 | 1 if in Top 1%, else 0 |
| `CAND_TOP5` | int8 | 1 if in Top 5%, else 0 |
| `CAND_TOP10` | int8 | 1 if in Top 10%, else 0 (always 1 in this file) |
| `REC_LEVEL` | string | Recommendation level: TOP1, TOP5, or TOP10 |
| `DIST_EXIST_M` | float64 | Metres to nearest existing same-brand outlet |
| `TOP1_FEAT` … `TOP7_FEAT` | string | Seven strongest local drivers, ranked by absolute SHAP value |
| `TOP1_XVAL` … `TOP7_XVAL` | float64 | Observed feature value of each driver |
| `TOP1_SHAP` … `TOP7_SHAP` | float64 | Signed SHAP contribution to prediction |
| `TOP1_DIR` … `TOP7_DIR` | string | Direction: "raises" or "lowers" the score |
| `SHAP_BASE` | float64 | Explainer base value (model's mean prediction on training data) |
| `SHAP_KIND` | string | `direct_tree_shap_xgboost` or `surrogate_shap_for_geoxgboost` |
| `WADMKK` | string | Regency or city (kabupaten/kota) |

**Row counts:**

| Brand | XGBoost Top 1% | Top 5% | Top 10% | GeoXGBoost Top 1% | Top 5% | Top 10% |
|---|---|---|---|---|---|---|
| Alfamart | 6,233 | 31,161 | 62,322 | 6,233 | 31,161 | 62,322 |
| Indomaret | 6,259 | 31,295 | 62,589 | 6,259 | 31,295 | 62,589 |

Tier sizes match across algorithms because they are percentiles of the same eligible pool. **Selected cells differ between algorithms.**

**Eligibility:** A cell qualifies if:
- `target_presence == 0` (no existing outlet in cell), **AND**
- Centroid is ≥250 m from nearest same-brand outlet

Applied **after** full-grid scoring, never during training.

Eligible pools: 623,220 (Alfamart), 625,928 (Indomaret).

**SHAP attributions:**
- **XGBoost:** Direct TreeSHAP (tree-based explanation)
- **GeoXGBoost:** Surrogate SHAP (XGBoost regressor fitted to GeoXGBoost score surface for local explanation)

**⚠️ Never pool direct and surrogate SHAP values in the same analysis.**

---

## Checksum File

### `checksums.sha256`

SHA-256 hashes for all data files. Generated with:

```bash
python ../scripts/verify_checksums.py --write
```

Or manually (from `data/` directory):

```bash
sha256sum grid/*.parquet grid/*.gpkg sentiment/*.csv partition/*.csv candidates/*.gpkg > checksums.sha256
```

**Format:** One line per file, `<hash>  <path>` (two spaces).

**Verification:**

```bash
sha256sum -c checksums.sha256
```

Output: `<filename>: OK` for each file. If any mismatch occurs, stop—the file is corrupt.

---

## Coordinate Systems

- **Grid and geometries (`grid_geometry_100m.gpkg`):** EPSG:32748 (WGS 84 / UTM zone 48S)
  - Distances in metres
  - Suitable for spatial operations (buffer, intersection, etc.)

- **Candidates (`candidates_*.gpkg`):** EPSG:4326 (WGS 84)
  - Decimal degrees
  - Suitable for web mapping and display

- **Sentiment outlets:** EPSG:4326
  - Decimal degrees (`latitude`, `longitude` columns)

**Reproject as needed:**

```python
import geopandas as gpd

# Load candidates (already in EPSG:4326)
candidates = gpd.read_file("candidates/candidates_alfamart_xgboost_*.gpkg")

# Convert to UTM for distance calculations
candidates_utm = candidates.to_crs("EPSG:32748")
```

---

## File Sizes and Approximate Disk Space

| Path | Format | Size |
|---|---|---|
| `grid/grid_alfamart_x1_x35.parquet` | Parquet, snappy | ~80–120 MB |
| `grid/grid_indomaret_x1_x35.parquet` | Parquet, snappy | ~80–120 MB |
| `grid/grid_geometry_100m.gpkg` | GeoPackage | ~250–350 MB |
| `sentiment/outlet_features_alfamart_x27_x35.csv` | CSV, UTF-8 | ~1–2 MB |
| `sentiment/outlet_features_indomaret_x27_x35.csv` | CSV, UTF-8 | ~1–2 MB |
| `partition/spatial_blocks_1km.csv` | CSV | ~15–20 MB |
| `partition/development_holdout_split.csv` | CSV | <1 MB |
| `candidates/candidates_alfamart_xgboost_*.gpkg` | GeoPackage | ~30–60 MB |
| `candidates/candidates_alfamart_geoxgboost_*.gpkg` | GeoPackage | ~30–60 MB |
| `candidates/candidates_indomaret_xgboost_*.gpkg` | GeoPackage | ~30–60 MB |
| `candidates/candidates_indomaret_geoxgboost_*.gpkg` | GeoPackage | ~30–60 MB |
| **Total** | **Mixed** | **~600–900 MB** |

---

## License & Attribution

All files are released under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

**You are free to:**
- Share (copy, redistribute)
- Adapt (remix, transform, build upon)

**Under the following terms:**
- **Attribution** — Give credit and indicate changes made

**Third-party sources:** Not redistributed. Processed predictors only. See `../LICENSE-DATA.md` for source licenses and terms.

---

## Questions?

- **Data questions:** See [`../DATA_DICTIONARY.md`](../DATA_DICTIONARY.md) for predictor definitions
- **Methodology:** See [`../REPRODUCE.md`](../REPRODUCE.md) for usage guidance
- **Issues:** Open an issue on GitHub or contact the maintainers
