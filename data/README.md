# `data/` — File Manifest

Every file released with the RitelAI replication package, what it contains, and how to
verify it. Column-level definitions for X1–X35 are in [`../DATA_DICTIONARY.md`](../DATA_DICTIONARY.md).

All coordinates are **EPSG:32748** (WGS 84 / UTM zone 48S) unless stated otherwise.
Candidate layers are additionally reprojected to **EPSG:4326** for web display.

---

## Verify before use

```bash
python ../scripts/verify_checksums.py
```

Or manually:

```bash
sha256sum -c checksums.sha256
```

Record the SHA-256 of every file in `checksums.sha256` before publishing the release.
If a checksum mismatches, stop — downstream numbers will not reproduce.

---

## `grid/`

### `grid_alfamart_x1_x35.parquet` · `grid_indomaret_x1_x35.parquet`

The analysis table. One row per grid cell, **685,318 rows** per brand.

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Unique cell key; joins to `grid_geometry_100m.gpkg` and to `partition/` |
| `centroid_x` | float64 | Centroid easting, metres, EPSG:32748 |
| `centroid_y` | float64 | Centroid northing, metres, EPSG:32748 |
| `BLOCK_ID` | int64 | 1 × 1 km spatial block key, 7,278 distinct values |
| `x1` … `x35` | float64 | Predictors; see the data dictionary |
| `target_presence` | int8 | 1 if the cell contains at least one mapped outlet of this brand, else 0 |
| `WADMPR` | string | Province |
| `WADMKK` | string | Regency or city |
| `WADMKC` | string | District (kecamatan) |
| `WADMKD` | string | Village (kelurahan/desa) |

X1–X23 are identical between the two brand files. X24–X26 and X27–X35 are brand-specific.

Expected totals:

| Brand | Rows | Positives | Prevalence | Blocks |
|---|---|---|---|---|
| Alfamart | 685,318 | 3,632 | 0.530% | 7,278 |
| Indomaret | 685,318 | 3,481 | 0.508% | 7,278 |

> The Alfamart positive count reflects the **cached experimental target** used throughout
> the paper. Rebuilding from the current outlet master gives 3,637 instead. Use the
> shipped files to reproduce the published numbers.

### `grid_geometry_100m.gpkg`

Cell geometries, layer `grid_100m`. Two columns: `GRID_ID` (int64) and `geometry`
(Polygon, EPSG:32748). Kept separate from the attribute tables so the 685,318-row
analysis matrix stays light.

```python
import geopandas as gpd, pandas as pd

attrs = pd.read_parquet("data/grid/grid_alfamart_x1_x35.parquet")
geom  = gpd.read_file("data/grid/grid_geometry_100m.gpkg", layer="grid_100m")
grid  = geom.merge(attrs, on="GRID_ID", how="inner")
```

---

## `sentiment/`

### `outlet_features_alfamart_x27_x35.csv` · `outlet_features_indomaret_x27_x35.csv`

Outlet-level aggregated review features, **before** propagation to grids within 500 m.

| Column | Type | Description |
|---|---|---|
| `outlet_id` | string | Anonymised outlet key, stable within this release |
| `latitude`, `longitude` | float64 | Outlet position, EPSG:4326 |
| `n_reviews` | int | Deduplicated reviews behind the aggregation |
| `n_reviews_recent_12m` | int | Reviews inside the twelve-month window used by X31 |
| `x27` … `x30` | float64 | Mean polarity in [−1, 1] for stock, queue/cashier, price, service |
| `x31` | float64 | Mean star rating, most recent twelve months, falling back to all valid ratings |
| `x32` … `x35` | float64 | Newer-half minus older-half mean sentiment, per aspect |

Row counts:

| Brand | Outlet records | With valid coordinates | Reviews classified | Outlets with reviews |
|---|---|---|---|---|
| Alfamart | 3,947 | 3,898 | 118,604 | 3,642 |
| Indomaret | 3,754 | 3,718 | 74,437 | 3,621 |

Outlet records exceed outlets-with-reviews because the join retains master outlets that
carry no review.

**Zero is ambiguous.** In X27–X30 and X32–X35 a zero may mean neutral sentiment, no review
mentioning that aspect, or too few dated reviews to compute a change. Use `n_reviews` and
`n_reviews_recent_12m` to tell coverage apart from genuine neutrality; the released
features themselves do not distinguish the three cases.

---

## `partition/`

### `spatial_blocks_1km.csv`

| Column | Description |
|---|---|
| `GRID_ID` | Cell key |
| `BLOCK_ID` | 1 × 1 km block key |
| `block_row`, `block_col` | Block indices in the projected grid |

685,318 rows, 7,278 distinct blocks.

### `development_holdout_split.csv`

**The file that makes the paper reproducible.** Approximately 80/20 by block, selected
from up to 250 block-disjoint `GroupShuffleSplit` candidates to preserve target prevalence
with zero block overlap.

| Column | Description |
|---|---|
| `BLOCK_ID` | 1 × 1 km block key |
| `partition` | `development` or `holdout` |

| Partition | Blocks | Alfamart grids | Alfamart positives | Indomaret grids | Indomaret positives |
|---|---|---|---|---|---|
| Development | 5,822 | 548,111 | 2,904 | 548,272 | 2,785 |
| Holdout | 1,456 | 137,207 | 728 | 137,046 | 696 |

Block overlap is zero by construction. The holdout was not used for ablation, pruning,
parameter selection or model choice until the single final evaluation.

---

## `candidates/`

### `candidates_{brand}_{algorithm}_top1_top5_top10.gpkg`

Four files: two brands × two algorithms. Layer name
`{brand}_{algorithm}_candidates`, CRS EPSG:4326.

Each file holds the **Top 10%** cells, with Top 1% and Top 5% nested inside as flags.

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Cell key |
| `BRAND` | string | Alfamart or Indomaret |
| `ALGORITHM` | string | xgboost or geoxgboost |
| `PRED_PROBA` | float64 | Relative suitability score in [0, 1] — **not a probability** |
| `PERCENTILE` | float64 | Percentile within this brand's eligible-grid pool |
| `CAND_TOP1` | int8 | 1 if in the Top 1% tier |
| `CAND_TOP5` | int8 | 1 if in the Top 5% tier |
| `CAND_TOP10` | int8 | 1 if in the Top 10% tier (always 1 in this file) |
| `REC_LEVEL` | string | TOP1, TOP5 or TOP10 |
| `DIST_EXIST_M` | float64 | Metres to the nearest existing same-brand outlet |
| `TOP1_FEAT` … `TOP7_FEAT` | string | Seven strongest local drivers, ranked by absolute SHAP |
| `TOP1_XVAL` … `TOP7_XVAL` | float64 | Observed feature value of each driver |
| `TOP1_SHAP` … `TOP7_SHAP` | float64 | Signed SHAP contribution |
| `TOP1_DIR` … `TOP7_DIR` | string | Raises or lowers the score |
| `SHAP_BASE` | float64 | Explainer base value |
| `SHAP_KIND` | string | `direct_tree_shap_xgboost` or `surrogate_shap_for_geoxgboost` |
| `WADMKK` | string | Regency or city |

Row counts:

| Brand | Algorithm | Top 1% | Top 5% | Top 10% |
|---|---|---|---|---|
| Alfamart | XGBoost | 6,233 | 31,161 | 62,322 |
| Alfamart | GeoXGBoost | 6,233 | 31,161 | 62,322 |
| Indomaret | XGBoost | 6,259 | 31,295 | 62,589 |
| Indomaret | GeoXGBoost | 6,259 | 31,295 | 62,589 |

Tier sizes match across algorithms because they are percentiles of the same eligible pool;
the selected cells differ.

**Eligibility.** A cell qualifies when `target_presence == 0` **and** its centroid is at
least 250 m from an existing same-brand outlet. The filter is applied *after* full-grid
scoring, never during training or prediction. Eligible pools: 623,220 cells for Alfamart
and 625,928 for Indomaret.

**`SHAP_KIND` matters.** For GeoXGBoost the attributions come from an XGBoost surrogate
fitted to the GeoXGBoost score surface, not from the local ensembles themselves. Never
pool surrogate values with direct TreeSHAP values in the same comparison.

---

## Reading the score correctly

`PRED_PROBA` measures how closely a cell resembles the feature signature of the existing
outlet network. It is **not**:

- a probability that a store will open there
- a probability that a store there would succeed
- a revenue, footfall or profit estimate
- a substitute for site survey or feasibility analysis

A small share of raw scores fell outside [0, 1] and was clipped: about 0.173% for
Alfamart-XGBoost, 0.085% for Alfamart-GeoXGBoost, 0.004% for Indomaret-GeoXGBoost, and
none for Indomaret-XGBoost. The clipping itself is a reminder that the output is an index,
not a calibrated probability.

---

## Suggested file formats and sizes

| Path | Format | Approximate size |
|---|---|---|
| `grid/grid_{brand}_x1_x35.parquet` | Parquet, snappy | 80–120 MB each |
| `grid/grid_geometry_100m.gpkg` | GeoPackage | 250–350 MB |
| `sentiment/outlet_features_{brand}_x27_x35.csv` | CSV, UTF-8 | 1–2 MB each |
| `partition/spatial_blocks_1km.csv` | CSV | 15–20 MB |
| `partition/development_holdout_split.csv` | CSV | < 1 MB |
| `candidates/*.gpkg` | GeoPackage | 30–60 MB each |

Files above GitHub's 100 MB limit should go to the Zenodo archive, with the repository
holding a small loader that fetches them by DOI. Git LFS is the alternative if you prefer
everything in one place.
