# Using RitelAI Dataset

Guidance for accessing, verifying, and using the processed spatial dataset from the RitelAI study published in *IAENG Transactions on Engineering Sciences*.

**For complete methodology, model specifications, and results**, refer to the published paper (pseudo-code included).

---

## 1. Data Integrity Verification

Before analysis, verify that all files match their checksums.

```bash
cd data/
sha256sum -c checksums.sha256
```

**Expected output:**
```
grid_alfamart_x1_x35.parquet: OK
grid_indomaret_x1_x35.parquet: OK
grid_geometry_100m.gpkg: OK
outlet_features_alfamart_x27_x35.csv: OK
outlet_features_indomaret_x27_x35.csv: OK
spatial_blocks_1km.csv: OK
development_holdout_split.csv: OK
candidates_alfamart_xgboost_top1_top5_top10.gpkg: OK
candidates_alfamart_geoxgboost_top1_top5_top10.gpkg: OK
candidates_indomaret_xgboost_top1_top5_top10.gpkg: OK
candidates_indomaret_geoxgboost_top1_top5_top10.gpkg: OK
```

**Stop here if any file mismatches.** Download again and re-verify.

---

## 2. Load the Grid Data

### Python (pandas + geopandas):

```python
import pandas as pd
import geopandas as gpd

# Load grid predictors and target
alfamart = pd.read_parquet("data/grid/grid_alfamart_x1_x35.parquet")
indomaret = pd.read_parquet("data/grid/grid_indomaret_x1_x35.parquet")

# Inspect
print(alfamart.shape)  # (685318, 39)
print(alfamart.columns)
print(alfamart[["target_presence"]].sum())  # Should be 3,632 for Alfamart

# Load geometries
geom = gpd.read_file("data/grid/grid_geometry_100m.gpkg", layer="grid_100m")
print(geom.shape)  # (685318, 2)

# Join geometries with attributes
alfamart_geo = geom.merge(alfamart, on="GRID_ID", how="inner")
print(alfamart_geo.crs)  # EPSG:32748

# Reproject to EPSG:4326 if needed for web mapping
alfamart_geo_4326 = alfamart_geo.to_crs("EPSG:4326")
```

### R (sf + data.table):

```r
library(sf)
library(data.table)

# Load grid data
alfamart <- fread("data/grid/grid_alfamart_x1_x35.parquet")
print(nrow(alfamart))  # 685318

# Load geometries
geom <- st_read("data/grid/grid_geometry_100m.gpkg", layer = "grid_100m")
print(st_crs(geom))  # EPSG:32748

# Join
alfamart_geo <- merge(geom, alfamart[, .(GRID_ID, x1, x2, ...)], by = "GRID_ID")
```

---

## 3. Explore Predictor Distributions

```python
# Summary statistics
print(alfamart[["x1", "x3", "x7", "x8"]].describe())

# Check missing values
print(alfamart[["x1", "x2", "x3"]].isnull().sum())

# Distribution of target
print(alfamart["target_presence"].value_counts())
# Expected: 0 → 681,686, 1 → 3,632

# Administrative breakdown
print(alfamart["WADMKK"].value_counts().head())
```

---

## 4. Understand the Spatial Split

The development–holdout split is **block-disjoint**: no 1 × 1 km block appears in both partitions.

```python
# Load split
split = pd.read_csv("data/partition/development_holdout_split.csv")

# Merge with grid
alfamart_split = alfamart.merge(split, on="BLOCK_ID", how="left")

# Separate
dev = alfamart_split[alfamart_split["partition"] == "development"]
hold = alfamart_split[alfamart_split["partition"] == "holdout"]

print("Development:")
print(f"  Rows: {len(dev)}")
print(f"  Outlets (target=1): {dev['target_presence'].sum()}")
print(f"  Blocks: {dev['BLOCK_ID'].nunique()}")

print("Holdout:")
print(f"  Rows: {len(hold)}")
print(f"  Outlets (target=1): {hold['target_presence'].sum()}")
print(f"  Blocks: {hold['BLOCK_ID'].nunique()}")

# Verify zero overlap
dev_blocks = set(dev["BLOCK_ID"])
hold_blocks = set(hold["BLOCK_ID"])
assert dev_blocks & hold_blocks == set(), "Block overlap detected!"
```

**Expected (Alfamart):**
```
Development: 548,111 rows, 2,904 outlets, 5,822 blocks
Holdout: 137,207 rows, 728 outlets, 1,456 blocks
```

---

## 5. Examine Sentiment Data

Sentiment features (X27–X35) are outlet-level aggregations **before** spatial propagation to grids.

```python
# Load outlet-level sentiment
sentiment = pd.read_csv("data/sentiment/outlet_features_alfamart_x27_x35.csv")

print(sentiment.shape)  # (3947, 13) for Alfamart
print(sentiment.columns)

# Explore
print(sentiment[["n_reviews", "n_reviews_recent_12m", "x27", "x31"]].describe())

# Outlets with reviews
outlets_reviewed = sentiment[sentiment["n_reviews"] > 0]
print(f"Outlets with ≥1 review: {len(outlets_reviewed)}")  # 3,642 for Alfamart

# Mean rating distribution
print(sentiment["x31"].describe())
# Note: x31 is mean star rating; zero may mean no reviews in recent 12m

# Sentiment polarity ranges
print(sentiment[["x27", "x28", "x29", "x30"]].describe())
# Range [−1, 1]: negative, neutral, positive
# Zero may mean neutral or no reviews mentioning aspect
```

---

## 6. Inspect Candidate Locations

The candidate GeoPackage files contain the Top 10% scored locations with SHAP explanations.

```python
# Load candidates
candidates = gpd.read_file(
    "data/candidates/candidates_alfamart_xgboost_top1_top5_top10.gpkg",
    layer="alfamart_xgboost_candidates"
)

print(candidates.shape)  # (62322, 20+) for Alfamart Top 10% (XGBoost)
print(candidates.crs)  # EPSG:4326

# Check tiers
print(candidates[["REC_LEVEL"]].value_counts())
# Expected: TOP1 → 6,233, TOP5 → 24,928, TOP10 → 31,161

# Score distribution
print(candidates["PRED_PROBA"].describe())

# Distance to nearest existing outlet
print(candidates["DIST_EXIST_M"].describe())

# Top drivers for first candidate
c = candidates.iloc[0]
print(f"Top 7 drivers (by abs SHAP):")
for i in range(1, 8):
    feat = c[f"TOP{i}_FEAT"]
    val = c[f"TOP{i}_XVAL"]
    shap = c[f"TOP{i}_SHAP"]
    direction = c[f"TOP{i}_DIR"]
    print(f"  {i}. {feat:20} = {val:8.2f}, SHAP = {shap:7.4f} ({direction})")

# Filter Top 1% only
top1 = candidates[candidates["CAND_TOP1"] == 1]
print(f"Top 1% cells: {len(top1)}")  # 6,233
```

---

## 7. Reproducing Results from the Paper

The paper reports holdout performance metrics. To verify:

1. **Use the shipped `development_holdout_split.csv`** — Do not rebuild from outlet master. Alfamart positive count will differ (3,637 vs 3,632 from cached split).

2. **Use fold-safe feature construction** for X26 and X27–X35:
   - Split development set into 5 spatial folds by BLOCK_ID
   - Rebuild X26 and X27–X35 using **training-fold outlets only**
   - Leave-one-grid-out for positive training cells
   - Never let validation outlets feed training features

3. **Verify candidate counts** match:

| Brand | XGBoost Top 1% | GeoXGBoost Top 1% |
|---|---|---|
| Alfamart | 6,233 | 6,233 |
| Indomaret | 6,259 | 6,259 |

If counts match, data integrity is confirmed.

---

## 8. Common Questions

### Q: Why is the Alfamart count 3,632 and not 3,637?

**A:** The cached `development_holdout_split.csv` and grid data reflect an experimental outlet master from the time of model development. The current outlet master has 5 additional Alfamart locations not in the original analysis. **To match published results exactly, use the shipped data (3,632).**

### Q: What does zero mean in X27–X30 or X32–X35?

**A:** Zero is ambiguous:
- Neutral sentiment observed for that aspect
- No review mentioning that aspect (e.g., no reviews mention stock, so X27=0)
- Too few dated reviews to compute change (e.g., only old reviews, so X32=0)

Check `n_reviews` and `n_reviews_recent_12m` in the outlet-level CSV to distinguish. Gridded features do not preserve that detail.

### Q: Can I use PRED_PROBA as a success probability?

**A:** No. `PRED_PROBA` is a relative spatial index of how closely a cell matches the feature signature of existing outlets. It is **not** calibrated to predict success probability, revenue, or footfall. Use it as a screening surface to narrow a large search space. Pair every candidate with field verification before finalising a site.

### Q: Why are some grids not in the candidates file?

**A:** Candidate eligibility requires:
1. `target_presence == 0` (no existing outlet in cell)
2. Centroid ≥250 m from nearest same-brand outlet (250 m screening rule)

The 250 m rule is a screening convenience, **not** a cannibalisation estimate. It does not model parcel boundaries, road crossings, or catchment overlap.

### Q: How do I compare XGBoost and GeoXGBoost?

**A:** Both scored the same eligible pool and ranked by percentile. The selected cells differ. Check:
- `SHAP_KIND` column: `direct_tree_shap_xgboost` vs `surrogate_shap_for_geoxgboost`
- Never pool direct and surrogate SHAP values in the same comparison
- See published paper for performance metrics

### Q: What coordinate system should I use?

**A:** 
- **Grid and geometries:** EPSG:32748 (UTM 48S) — distances in metres
- **Candidates:** EPSG:4326 (WGS 84) — for web display
- **Sentiment outlets:** EPSG:4326 — decimal degrees

Use `to_crs()` in geopandas to reproject as needed.

---

## 9. Limitations & Disclaimers

- **Not a probability.** PRED_PROBA is a spatial index, not a calibrated success probability.
- **Not a valuation.** Scores do not estimate revenue, footfall, or profit.
- **Not a substitute for site survey.** Field verification, parcel availability, zoning checks, and financial feasibility analysis are essential before any real siting decision.
- **Data drift.** POI and review data change continuously. A rebuild months later will not match byte-for-byte.
- **No liability.** The authors and Bina Nusantara University accept no liability for commercial decisions made on this data.

---

## 10. Citation & Access

**Cite this dataset:**

```bibtex
@dataset{ritelai2024,
  author = {Budi Carto},
  title = {RitelAI: Retail Location Suitability Assessment for Jabodetabek},
  year = {2024},
  url = {https://github.com/budi-carto/ritelai-jabodetabek},
  doi = {10.5281/zenodo.XXXXX}
}
```

**Published paper:**  
Budi Carto et al. (2024). RitelAI: Machine Learning–Based Retail Suitability Assessment for Jabodetabek. *IAENG Transactions on Engineering Sciences*.

**Repository:** https://github.com/budi-carto/ritelai-jabodetabek

---

**Questions?** Open an issue or contact the maintainers.
