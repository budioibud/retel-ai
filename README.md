# RitelAI — Geospatial Data and Consumer Sentiment for Retail Store Location Recommendation in Greater Jakarta

[![Data License: CC BY 4.0](https://img.shields.io/badge/data%20license-CC%20BY%204.0-blue.svg)](LICENSE-DATA.md)
[![Code License: MIT](https://img.shields.io/badge/code%20license-MIT-green.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.0000000.svg)](https://doi.org/10.5281/zenodo.0000000)

Replication package for:

> B. P. Nugroho and A. A. S. Gunawan, "RitelAI: Integrating geospatial data and consumer sentiment for retail store location recommendation in Greater Jakarta," *IAENG International Journal of Computer Science*, forthcoming.

RitelAI is an explainable GeoAI framework that screens candidate locations for Alfamart and Indomaret minimarkets across the Greater Jakarta metropolitan region (Jabodetabek). It combines 25 external geospatial predictors, one same-brand network predictor, and nine features derived from Google Maps consumer reviews on a uniform 100 × 100 m grid, then compares a global model (XGBoost) against a spatially local model (Geographical-XGBoost) under a leakage-aware spatial evaluation design.

**Interactive WebGIS:** https://www.geoairitel.budi-carto.my.id

---

## What this repository is for

The recommendation score produced here is a **relative spatial suitability index**, not a calibrated probability and not a forecast of commercial success. It measures how closely a grid cell resembles the feature signature of the existing outlet network. Every candidate still requires field survey, parcel availability checks, zoning verification, and technical and financial feasibility assessment before any decision is made.

---

## Study design at a glance

| Item | Value |
|---|---|
| Study area | Jabodetabek (Jakarta, Bogor, Depok, Tangerang, Bekasi) |
| Spatial unit | 100 × 100 m grid, 685,318 cells |
| Projected CRS | EPSG:32748 (WGS 84 / UTM zone 48S) |
| Spatial blocks | 7,278 blocks of 1 × 1 km |
| Target | Presence–background (1 = grid contains a mapped outlet) |
| Positive prevalence | Alfamart 0.530%, Indomaret 0.508% |
| Predictors | 35 (X1–X25 external, X26 same-brand network, X27–X35 review-derived) |
| Development / holdout | 5,822 blocks / 1,456 blocks, zero block overlap |
| Inner validation | 5-fold spatial GroupKFold on the development set |
| Tuning | Optuna, 20 valid trials per study, objective = out-of-fold Average Precision |
| Primary reporting metric | Recall@5% on the untouched spatial holdout |

### Fixed experimental target

All experiments run on a **cached block-disjoint partition**. Its fixed target counts are:

| Brand | Positives | Development | Holdout | Dev grids | Holdout grids |
|---|---|---|---|---|---|
| Alfamart | 3,632 | 2,904 | 728 | 548,111 | 137,207 |
| Indomaret | 3,481 | 2,785 | 696 | 548,272 | 137,046 |

> **Note for people re-running the pipeline.** Rebuilding the target from the current outlet master yields **3,637** positive Alfamart grids (prevalence 0.005307) rather than 3,632 (prevalence 0.005300). The difference of five grids comes from outlet-master updates made after the partition was cached. The cached partition is shipped in this repository so that every number in the paper reproduces exactly. Indomaret is unaffected (3,481 either way).

---

## Headline results — untouched spatial holdout

Evaluated once, after all tuning and model selection were complete.

| Brand | Algorithm | AP | ROC-AUC | Precision@5% | Recall@5% |
|---|---|---|---|---|---|
| Alfamart | XGBoost | **0.049913** | **0.914025** | **0.052325** | **0.491781** |
| Alfamart | GeoXGBoost | 0.044429 | 0.905022 | 0.045912 | 0.431507 |
| Indomaret | XGBoost | **0.053683** | **0.919591** | **0.052532** | **0.517241** |
| Indomaret | GeoXGBoost | 0.044996 | 0.903668 | 0.045382 | 0.446839 |

XGBoost leads on every metric for both brands: relative AP advantage of 12.34% (Alfamart) and 19.31% (Indomaret). At a five-percent screening budget it recovers roughly half of the historically positive holdout grids, against a base prevalence near 0.5%.

Recall at the other screening budgets:

| Brand | Algorithm | Recall@1% | Recall@5% | Recall@10% |
|---|---|---|---|---|
| Alfamart | XGBoost | 14.11% | 49.18% | 70.14% |
| Alfamart | GeoXGBoost | 11.64% | 43.15% | 68.08% |
| Indomaret | XGBoost | 15.09% | 51.72% | 71.70% |
| Indomaret | GeoXGBoost | 12.36% | 44.68% | 66.81% |

### Tuning summary

| Brand | Algorithm | Valid trials | Completed | Pruned | Best trial | Inner spatial OOF AP |
|---|---|---|---|---|---|---|
| Alfamart | XGBoost | 20 | 18 | 2 | 15 | 0.054749 |
| Alfamart | GeoXGBoost | 20 | 18 | 2 | 16 | 0.043182 |
| Indomaret | XGBoost | 20 | 12 | 8 | 14 | 0.055375 |
| Indomaret | GeoXGBoost | 20 | 17 | 3 | 17 | 0.044687 |

Both GeoXGBoost studies selected an adaptive kernel with bandwidth 240 and disabled the optional spatial weights.

### Candidate layers

After removing existing-outlet grids and cells whose centroid lies within 250 m of a same-brand outlet:

| Brand | Eligible grids | Top 1% | Top 5% | Top 10% |
|---|---|---|---|---|
| Alfamart | 623,220 | 6,233 | 31,161 | 62,322 |
| Indomaret | 625,928 | 6,259 | 31,295 | 62,589 |

Tier sizes are percentiles of the same eligible-grid pool within each brand, so both algorithms return the same count at a given tier while selecting different cells.

---

## Leakage control

Two leakage paths matter in this problem, and both are handled explicitly.

**Spatial dependence.** Neighbouring 100 m grids share roads, land use and activity. Splitting at row level lets nearly identical cells land in both training and testing. Every split here is made at the level of 1 × 1 km blocks, and the final holdout is an untouched set of blocks that is opened exactly once.

**Target-defining features.** X26 and X27–X35 are derived from the very outlets that define the target. Computing them before splitting would leak the label. Instead:

- inside every training/validation split, the dynamic features of validation grids are rebuilt using **only** target-brand outlets located in the training region;
- for positive training grids, leave-one-grid-out logic removes the outlet or outlets sitting in the query grid before its own dynamic features are constructed;
- X24–X25 depend on competitor outlets rather than the modelled brand, so they are computed once.

The same rule is applied when the deployment model is refitted.

---

## Repository structure

```
ritelai-jabodetabek/
├── README.md
├── DATA_DICTIONARY.md          # definition, source and construction of X1–X35
├── REPRODUCE.md                # step-by-step replication guide
├── CITATION.cff
├── LICENSE                     # MIT, applies to code
├── LICENSE-DATA.md             # CC BY 4.0, applies to aggregated data
├── requirements.txt
├── environment.yml
│
├── data/
│   ├── README.md               # file-by-file description and checksums
│   ├── grid/
│   │   ├── grid_alfamart_x1_x35.parquet
│   │   ├── grid_indomaret_x1_x35.parquet
│   │   └── grid_geometry_100m.gpkg          # GRID_ID → polygon, EPSG:32748
│   ├── sentiment/
│   │   ├── outlet_features_alfamart_x27_x35.csv
│   │   └── outlet_features_indomaret_x27_x35.csv
│   ├── partition/
│   │   ├── spatial_blocks_1km.csv           # GRID_ID → BLOCK_ID
│   │   └── development_holdout_split.csv    # BLOCK_ID → development | holdout
│   └── candidates/
│       ├── candidates_alfamart_xgboost_top1_top5_top10.gpkg
│       ├── candidates_alfamart_geoxgboost_top1_top5_top10.gpkg
│       ├── candidates_indomaret_xgboost_top1_top5_top10.gpkg
│       └── candidates_indomaret_geoxgboost_top1_top5_top10.gpkg
│
├── notebooks/
│   ├── 1_sentiment_alfamart.ipynb
│   ├── 2_sentiment_indomaret.ipynb
│   ├── 3_optuna_xgboost_geoxgboost_x1_x35.ipynb
│   └── 4_holdout_topk_evaluation.ipynb
│
├── scripts/
│   ├── baseline_compare_xgboost_geoxgboost.py
│   └── optuna_best_available_compare.py
│
└── results/
    ├── holdout_metrics.csv                  # the headline table above
    ├── study_convergence_summary.csv
    ├── best_hyperparameters.csv
    ├── surrogate_quality.csv
    ├── global_shap_importance_*.csv
    └── urban_context_top10_composition.csv
```

---

## Data files

### `data/grid/grid_{brand}_x1_x35.parquet`

One row per grid cell, 685,318 rows per brand.

| Column | Type | Description |
|---|---|---|
| `GRID_ID` | int64 | Unique cell identifier, joins to `grid_geometry_100m.gpkg` |
| `centroid_x`, `centroid_y` | float64 | Cell centroid in EPSG:32748, metres |
| `BLOCK_ID` | int64 | 1 × 1 km spatial block, joins to `data/partition/` |
| `x1` … `x35` | float64 | Predictors, see `DATA_DICTIONARY.md` |
| `target_presence` | int8 | 1 if the cell contains at least one mapped outlet of this brand |
| `WADMPR`, `WADMKK`, `WADMKC`, `WADMKD` | string | Province, regency/city, district, village |

X24–X26 and X27–X35 are brand-specific. X1–X23 are identical across the two brand files.

### `data/sentiment/outlet_features_{brand}_x27_x35.csv`

Outlet-level aggregated review features, before they are propagated to grids within a 500 m radius.

| Column | Description |
|---|---|
| `outlet_id` | Anonymised outlet key |
| `latitude`, `longitude` | Outlet coordinates, EPSG:4326 |
| `n_reviews` | Number of deduplicated reviews behind the aggregation |
| `x27` … `x30` | Mean review-level polarity among reviews mentioning stock, queue/cashier, price, service |
| `x31` | Mean rating over the most recent 12 months, falling back to all valid ratings |
| `x32` … `x35` | Newer-half minus older-half mean sentiment, per aspect |

**Zero is ambiguous by construction.** A zero in X27–X30 or X32–X35 may mean neutral sentiment, no review mentioning that aspect, or too few dated reviews to compute a change. The three cases are not distinguished in the released features and should not be read as observed neutrality. Preserving explicit missingness indicators is listed as future work in the paper.

### `data/candidates/*.gpkg`

Top 10% candidate cells, with Top 1% and Top 5% nested inside as flags.

| Column | Description |
|---|---|
| `GRID_ID`, `BRAND`, `ALGORITHM` | Identity |
| `PRED_PROBA` | Relative suitability score in [0, 1] — **not a probability** |
| `PERCENTILE` | Percentile within the eligible-grid pool of this brand |
| `CAND_TOP1`, `CAND_TOP5`, `CAND_TOP10` | Nested tier flags |
| `DIST_EXIST_M` | Distance to the nearest existing same-brand outlet, metres |
| `TOP1_FEAT` … `TOP7_FEAT` | The seven strongest local SHAP drivers, ranked by absolute contribution |
| `TOP1_SHAP` … `TOP7_SHAP` | Signed SHAP value of each driver |
| `TOP1_DIR` … `TOP7_DIR` | Direction: raises or lowers the score |
| `WADMKK` | Regency/city, for administrative filtering |

For XGBoost these are direct TreeSHAP values. For GeoXGBoost they are **surrogate** SHAP values, produced by an XGBoost regressor trained to approximate the GeoXGBoost score surface; fidelity statistics are reported in `results/surrogate_quality.csv`. Surrogate attributions describe the surrogate's behaviour, not the internal local ensembles, and the two are never pooled.

---

## What is not released, and why

| Not included | Reason | How to obtain |
|---|---|---|
| Raw Google Maps review text, reviewer names, profile identifiers and images | Personal data and platform terms | Not redistributable; only aggregated non-identifying derivatives are released |
| OpenStreetMap road and POI extracts | ODbL, share-alike | Download from the provider; `DATA_DICTIONARY.md` records the extraction date and query |
| BIG land use and RBI layers, ATR/BPN land-value WMS | Agency licensing | Request from the agency; the processing step is documented per predictor |
| WorldPop population, VIIRS nighttime light | Redistribution not required | Free download links in `DATA_DICTIONARY.md` |
| Outlet coordinate master | Commercial third-party POI data | The aggregated target and features are released instead |

Every predictor in the released grid is the **processed** value used by the models. That is enough to reproduce every model, metric, table and figure in the paper. Rebuilding the grid from scratch requires the third-party sources above; the recipe for each predictor is in `DATA_DICTIONARY.md`.

---

## Quick start

```bash
git clone https://github.com/budi-carto/ritelai-jabodetabek.git
cd ritelai-jabodetabek
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Reproduce the headline holdout table:

```python
import pandas as pd

grid  = pd.read_parquet("data/grid/grid_alfamart_x1_x35.parquet")
split = pd.read_csv("data/partition/development_holdout_split.csv")

grid = grid.merge(split, on="BLOCK_ID", how="left")
dev  = grid[grid["partition"] == "development"]
hold = grid[grid["partition"] == "holdout"]

print(len(dev), dev["target_presence"].sum())    # 548111 2904
print(len(hold), hold["target_presence"].sum())  # 137207 728
```

Full instructions, including the fold-safe rebuild of X26–X35, are in [`REPRODUCE.md`](REPRODUCE.md).

---

## Sentiment classification

Brand-specific Indonesian transformer models were fine-tuned and selected on **validation** macro-F1; the test set was opened once, for the selected family only.

| Brand | Selected model | Validation accuracy | Validation macro-F1 | Test accuracy | Test macro-F1 |
|---|---|---|---|---|---|
| Alfamart | IndoBERT, fine-tuned | 0.8622 | 0.8152 | 0.8133 | 0.7497 |
| Indomaret | IndoRoBERTa, fine-tuned | 0.8489 | 0.8455 | 0.8311 | 0.8278 |

Base checkpoints: `indobenchmark/indobert-base-p1` and `flax-community/indonesian-roberta-base`. Off-the-shelf baselines: `taufiqdp/indonesian-sentiment` and `w11wo/indonesian-roberta-base-sentiment-classifier`. Fine-tuning used a maximum sequence length of 96 tokens, effective batch size 8, two epochs, learning rate 2 × 10⁻⁵, weight decay 0.01, and warm-up over roughly 10% of update steps.

Labelled reference sets: 1,048 / 225 / 225 for Alfamart and 1,049 / 225 / 225 for Indomaret, stratified 70 / 15 / 15 across low (1–2), middle (3) and high (4–5) rating strata.

Inference corpora after deduplication: 118,604 Alfamart reviews across 3,642 outlets, and 74,437 Indomaret reviews across 3,621 outlets.

---

## Citation

If you use this dataset or code, please cite the paper and the archived release:

```bibtex
@article{nugroho2026ritelai,
  author  = {Nugroho, Budi Prasetyo and Gunawan, Alexander Agung Santoso},
  title   = {{RitelAI}: Integrating Geospatial Data and Consumer Sentiment for
             Retail Store Location Recommendation in Greater Jakarta},
  journal = {IAENG International Journal of Computer Science},
  year    = {2026},
  note    = {Forthcoming}
}

@dataset{nugroho2026ritelai_data,
  author    = {Nugroho, Budi Prasetyo and Gunawan, Alexander Agung Santoso},
  title     = {{RitelAI} replication package: microspatial grid, review-derived
               features and candidate layers for Greater Jakarta},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.0000000}
}
```

See also [`CITATION.cff`](CITATION.cff), which GitHub renders as a "Cite this repository" button.

---

## Licensing

| Component | Licence |
|---|---|
| Code — notebooks, scripts | [MIT](LICENSE) |
| Aggregated data — grid, sentiment features, partition, candidate layers | [CC BY 4.0](LICENSE-DATA.md) |
| Third-party source layers | Their own licences; not redistributed here |

---

## Limitations

Stated plainly, because they bound what the outputs mean.

- The target is presence–background, not performance. Existing outlets may include weak performers; empty cells are not verified failures.
- Review coverage is uneven. Roughly 69% of high-urban Alfamart grids carry at least one sentiment signal, against under 1% of low-urban grids, so sentiment features are far more informative in dense areas.
- Aspect detection uses transparent keyword rules and attaches review-level polarity to every aspect mentioned. It cannot resolve mixed sentiment inside a single review.
- One metropolitan region, two closely related retail formats, one block design. Dependence can still cross adjacent block boundaries.
- The optimisation budget was 20 valid trials per study and does not demonstrate global optimality.
- Geographical-XGBoost was introduced for spatially local regression; its use for imbalanced classification here should be validated on further benchmarks.
- GeoXGBoost explanations are surrogate-based, never direct SHAP.

---

## Contact

Budi Prasetyo Nugroho — Master of Computer Science Program, BINUS Graduate Program, Bina Nusantara University, Jakarta, Indonesia — budi.nugroho001@binus.ac.id

Alexander Agung Santoso Gunawan — School of Computer Science, Bina Nusantara University, Jakarta, Indonesia — aagung@binus.edu
