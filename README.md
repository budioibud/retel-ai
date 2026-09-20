# RitelAI: Explainable GeoAI for Retail Site Recommendation in Greater Jakarta

RitelAI is a spatial decision-support dataset and model-output repository for identifying and interpreting candidate retail locations for **Alfamart** and **Indomaret** across **Greater Jakarta (Jabodetabek: Jakarta, Bogor, Depok, Tangerang, and Bekasi)**.

The study uses a uniform **100 × 100 m grid**, geospatial predictors, same-brand outlet-network context, and review-derived consumer sentiment features. It compares **XGBoost** and **GeoXGBoost** under spatially blocked, leakage-aware evaluation and publishes full-grid prediction outputs together with model-comparison layers.

> **Important:** RitelAI produces **relative location-ranking scores** for preliminary screening. It does **not** predict profitability, revenue, store survival, or commercial success, and it does not replace field survey, parcel availability checks, legal/zoning review, technical assessment, or financial feasibility analysis.

**Associated manuscript:**  
*RitelAI: Integrating Geospatial Data and Consumer Sentiment for Retail Store Location Recommendation in Greater Jakarta*  
Prepared for submission to the **IAENG International Journal of Computer Science (IJCS)**.

---

## Repository Contents

The dataset release uses the following files under `data/`:

| File | Description |
|---|---|
| `full_grid_xgboost_x1_x35_alfamart.gpkg` | Full-grid XGBoost output for Alfamart using X1–X35 |
| `full_grid_geoxgboost_x1_x35_alfamart.gpkg` | Full-grid GeoXGBoost output for Alfamart using X1–X35 |
| `full_grid_xgboost_x1_x35_indomaret.gpkg` | Full-grid XGBoost output for Indomaret using X1–X35 |
| `full_grid_geoxgboost_x1_x35_indomaret.gpkg` | Full-grid GeoXGBoost output for Indomaret using X1–X35 |
| `alfamart_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg` | Spatial comparison of Alfamart XGBoost and GeoXGBoost outputs |
| `indomaret_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg` | Spatial comparison of Indomaret XGBoost and GeoXGBoost outputs |
| `01_clean_review_alfamart.csv` | Cleaned Alfamart review corpus used in the sentiment workflow |
| `01_clean_review_indomaret.csv` | Cleaned Indomaret review corpus used in the sentiment workflow |
| `07_dataset_retail_aggregated_X27_X35_JOINED_FINAL_alfamart.csv` | Final outlet-level Alfamart rating/sentiment features X27–X35 |
| `07_dataset_retail_aggregated_X27_X35_JOINED_FINAL_indomaret.csv` | Final outlet-level Indomaret rating/sentiment features X27–X35 |

Predictor definitions are documented in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).

---

## Quick Start

```python
from pathlib import Path
import pandas as pd
import geopandas as gpd

DATA = Path("data")

# Full-grid prediction outputs
alfa_xgb = gpd.read_file(DATA / "full_grid_xgboost_x1_x35_alfamart.gpkg")
alfa_gxgb = gpd.read_file(DATA / "full_grid_geoxgboost_x1_x35_alfamart.gpkg")
indo_xgb = gpd.read_file(DATA / "full_grid_xgboost_x1_x35_indomaret.gpkg")
indo_gxgb = gpd.read_file(DATA / "full_grid_geoxgboost_x1_x35_indomaret.gpkg")

# Model-comparison layers
alfa_comparison = gpd.read_file(DATA / "alfamart_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg")
indo_comparison = gpd.read_file(DATA / "indomaret_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg")

# Cleaned review corpora
reviews_alfa = pd.read_csv(DATA / "01_clean_review_alfamart.csv")
reviews_indo = pd.read_csv(DATA / "01_clean_review_indomaret.csv")

# Final aggregated sentiment/rating features
sentiment_alfa = pd.read_csv(DATA / "07_dataset_retail_aggregated_X27_X35_JOINED_FINAL_alfamart.csv")
sentiment_indo = pd.read_csv(DATA / "07_dataset_retail_aggregated_X27_X35_JOINED_FINAL_indomaret.csv")

print(alfa_xgb.shape)
print(alfa_xgb.columns.tolist())
```

To inspect GeoPackage layers before loading:

```python
import geopandas as gpd
print(gpd.list_layers("data/full_grid_xgboost_x1_x35_alfamart.gpkg"))
```

---

## Study Design

The study contains **685,318 grid cells**, each measuring **100 × 100 m**.

The empirical target is **presence–background**:

- `1` = the grid contains at least one mapped outlet of the modeled brand;
- `0` = background grid.

| Brand | Total grids | Positive grids | Prevalence |
|---|---:|---:|---:|
| Alfamart | 685,318 | 3,632 | 0.530% |
| Indomaret | 685,318 | 3,481 | 0.508% |

The target represents the spatial pattern of the historical outlet network. It does **not** distinguish profitable from underperforming stores, and background cells are not verified commercial failures.

---

## Predictor Groups

RitelAI uses **35 predictors (X1–X35)**:

| Range | Predictor group |
|---|---|
| X1–X2 | Physical environment and land use |
| X3–X6 | Accessibility and transport |
| X7–X9 | Economic and demographic proxies |
| X10–X12 | Market-demand proxies |
| X13–X23 | Functional-area / POI variables |
| X24–X25 | Competitor structure |
| X26 | Same-brand outlet count within 500 m |
| X27–X35 | Consumer rating and sentiment features |

**X26** is interpreted as same-brand network context rather than a universally beneficial agglomeration variable because it can encode demand concentration, network coverage, saturation, or possible cannibalization.

The review-derived features are:

| Feature | Description |
|---|---|
| X27 | Mean stock-related sentiment |
| X28 | Mean queue/cashier-related sentiment |
| X29 | Mean price-related sentiment |
| X30 | Mean service-related sentiment |
| X31 | Mean rating in the most recent 12 months, with fallback to all valid ratings |
| X32 | Change in stock sentiment |
| X33 | Change in queue sentiment |
| X34 | Change in price sentiment |
| X35 | Change in service sentiment |

Temporal sentiment change is computed as the mean polarity of the newer chronological half minus that of the older chronological half for aspect-specific reviews.

A zero value in X27–X30 or X32–X35 may represent neutral sentiment, no review mentioning the aspect, or insufficient temporal evidence. It should not automatically be interpreted as observed neutrality.

---

## Review Corpus

After duplicate removal:

| Brand | Deduplicated reviews | Outlets linked to reviews |
|---|---:|---:|
| Alfamart | 118,604 | 3,642 |
| Indomaret | 74,437 | 3,621 |

For sentiment-model development, up to 1,500 non-empty reviews per brand were manually labeled into negative, neutral, and positive classes using stratified rating groups.

Selected sentiment models:

- **Alfamart:** fine-tuned IndoBERT
- **Indomaret:** fine-tuned IndoRoBERTa

Model-family selection was based on **validation macro-F1**. The held-out test set was used only after model selection.

---

## Spatial Validation and Leakage Control

The grid is grouped into **7,278 non-overlapping 1 × 1 km spatial blocks**.

| Partition | Blocks | Alfamart grids | Alfamart positives | Indomaret grids | Indomaret positives |
|---|---:|---:|---:|---:|---:|
| Development | 5,822 | 548,111 | 2,904 | 548,272 | 2,785 |
| Untouched spatial holdout | 1,456 | 137,207 | 728 | 137,046 | 696 |

Dynamic predictors **X26–X35** are reconstructed within each spatial split. For positive training grids, leave-one-grid-out logic removes the query grid's own target-brand outlet information before constructing dynamic features.

---

## Model Development and Evaluation

Two models are compared:

- **XGBoost** — global gradient-boosted tree model
- **GeoXGBoost** — spatially local/global gradient-boosted model

The complete **X1–X35** configuration is optimized separately for each brand–algorithm combination using **Optuna** with five-fold spatial cross-validation on the development set.

### Metric roles

- **Average Precision (AP)** is the **Optuna tuning objective**.
- **Recall@Top-K** is the **primary final screening metric** on the untouched spatial holdout.
- **Precision@Top-K** is a complementary measure of positive concentration within the screened subset.
- **ROC-AUC** is a complementary discrimination metric.

For the final screening interpretation, **Recall@5%** measures the proportion of all positive holdout grids recovered within the highest-ranked 5% of evaluation grids.

---

## Candidate Ranking

Candidate eligibility is applied **after full-grid scoring**.

A grid is eligible when:

1. it is a background grid (`target = 0`); and
2. its centroid is at least **250 m** from the nearest existing outlet of the same brand.

The 250 m rule is a screening exclusion distance, **not** an estimated cannibalization threshold.

Eligible grids are ranked into exact nested percentile tiers:

- **Top 1%**
- **Top 5%**
- **Top 10%**

These tiers are relative rankings, not absolute feasibility classes.

| Brand | Top 1% | Top 5% | Top 10% |
|---|---:|---:|---:|
| Alfamart | 6,233 | 31,161 | 62,322 |
| Indomaret | 6,259 | 31,295 | 62,589 |

Tier sizes are the same for XGBoost and GeoXGBoost within each brand because the same eligible-grid pool is used. The selected **locations** differ between algorithms.

---

## Model Comparison Outputs

The comparison GeoPackages are intended for spatial agreement analysis:

```text
data/alfamart_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg
data/indomaret_xgboost_vs_geoxgboost_x1_x35_comparison.gpkg
```

They support comparison of grids selected by both models, XGBoost only, or GeoXGBoost only. This is useful for studying **recommendation morphology and spatial agreement**, which are conceptually different from predictive performance.

---

## Explainability

- **XGBoost:** direct TreeSHAP.
- **GeoXGBoost:** validated XGBoost surrogate followed by surrogate SHAP.

Direct XGBoost SHAP values and GeoXGBoost surrogate SHAP values should therefore not be treated as identical explanation objects.

---

## Understanding the Model Score

The model score is a **relative ranking score** describing similarity to feature patterns associated with the observed outlet network.

It is **not**:

- a probability that a new store will open;
- a probability of commercial success;
- a revenue, sales, footfall, or profit forecast;
- a parcel-level feasibility result;
- a replacement for field survey and business due diligence.

Recommended grids should be followed by field verification, parcel availability assessment, zoning/legal review, access and visibility checks, rent assessment, flood-risk review, logistics assessment, and financial feasibility analysis.

---

## Coordinate Reference Systems

The modeling workflow primarily uses **EPSG:32748 (WGS 84 / UTM zone 48S)** for metric spatial analysis. Exported or web-facing layers may use **EPSG:4326**.

Always verify the CRS stored in each GeoPackage before computing distances or buffers:

```python
import geopandas as gpd

gdf = gpd.read_file("data/full_grid_xgboost_x1_x35_alfamart.gpkg")
print(gdf.crs)
```

---

## Documentation

- [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) — definitions and construction of X1–X35
- [`REPRODUCE.md`](REPRODUCE.md) — methodology and reproduction notes
- [`data/README.md`](data/README.md) — data-directory documentation
- [`CITATION.cff`](CITATION.cff) — citation metadata
- [`LICENSE`](LICENSE) — repository code license
- [`LICENSE-DATA.md`](LICENSE-DATA.md) — data licensing and third-party attribution notes

---

## Citation

Until the journal article and archival DOI are finalized, please cite the repository as:

```bibtex
@dataset{nugroho2026ritelai,
  author    = {Budi Prasetyo Nugroho and Alexander Agung Santoso Gunawan},
  title     = {RitelAI: Integrating Geospatial Data and Consumer Sentiment for Retail Store Location Recommendation in Greater Jakarta},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/budioibud/ritel-ai}
}
```

After a Zenodo DOI is issued, replace this citation with the archived dataset DOI.

---

## Licensing and Third-Party Data

Repository code and original documentation are covered by the licenses provided in this repository.

Third-party source data and review-derived content remain subject to their original providers' licenses and terms. Do **not** assume that every third-party-derived record can automatically be relicensed under the repository's general data license.

Before publicly redistributing cleaned review text or other source-derived records, verify the applicable provider terms and redistribution rights.

See [`LICENSE-DATA.md`](LICENSE-DATA.md) for the intended attribution and licensing structure.

---

## Contact

**Budi Prasetyo Nugroho**  
Email: `budioibud@gmail.com`

---

## Disclaimer

The repository is provided for research and spatial decision-support purposes. The authors accept no liability for commercial siting decisions made from these outputs.

**Last updated:** 2026-09-20  
**Repository:** https://github.com/budioibud/ritel-ai
