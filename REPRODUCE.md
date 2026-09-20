# Reproduction Guide

Every number in the paper can be regenerated from the files in this repository.
This guide goes from a clean checkout to the headline holdout table.

---

## 0. Environment

Python 3.11 or newer.

```bash
git clone https://github.com/budi-carto/ritelai-jabodetabek.git
cd ritelai-jabodetabek
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Conda alternative:

```bash
conda env create -f environment.yml
conda activate ritelai
```

Key pinned versions are in `requirements.txt`. `geoxgboost` and `shap` are the two
packages most likely to shift behaviour between releases, so both are pinned exactly.

Fixed seeds are used throughout: base `RANDOM_STATE = 42`, with deterministic offsets per
brand, algorithm and stage. Tree ensembles are reproducible; kernel density and
neighbour queries are deterministic given the same inputs.

---

## 1. Verify the data

```bash
python scripts/verify_checksums.py
```

Expected output: every file in `data/` matches the SHA-256 recorded in
`data/README.md`. Stop here if anything mismatches — downstream numbers will drift.

---

## 2. Rebuild the partition

The cached block-disjoint split is shipped so the paper reproduces exactly.

```python
import pandas as pd

for brand in ("alfamart", "indomaret"):
    grid  = pd.read_parquet(f"data/grid/grid_{brand}_x1_x35.parquet")
    split = pd.read_csv("data/partition/development_holdout_split.csv")
    grid  = grid.merge(split, on="BLOCK_ID", how="left")

    dev  = grid[grid["partition"] == "development"]
    hold = grid[grid["partition"] == "holdout"]

    print(brand,
          len(dev),  int(dev["target_presence"].sum()),
          len(hold), int(hold["target_presence"].sum()),
          dev["BLOCK_ID"].nunique(), hold["BLOCK_ID"].nunique())
```

Expected:

```
alfamart  548111 2904 137207 728 5822 1456
indomaret 548272 2785 137046 696 5822 1456
```

Block overlap must be zero:

```python
assert set(dev["BLOCK_ID"]) & set(hold["BLOCK_ID"]) == set()
```

> **If you rebuild the target from an outlet master instead of using this file**, the
> Alfamart positive count comes out as 3,637 rather than 3,632, because the outlet
> master was updated after the partition was cached. Use the shipped partition to match
> the paper. Indomaret is unaffected.

---

## 3. Sentiment models

`notebooks/1_sentiment_alfamart.ipynb` and `notebooks/2_sentiment_indomaret.ipynb`.

Both notebooks cache their fine-tuned checkpoints. On a fresh run they will fine-tune;
on a rerun they reuse the cache and skip training. Expected selection results:

| Brand | Model family | Setting | Validation accuracy | Validation macro-F1 |
|---|---|---|---|---|
| Alfamart | IndoBERT | Ready-made | 0.7422 | 0.6646 |
| Alfamart | IndoBERT | Fine-tuned **(selected)** | 0.8622 | 0.8152 |
| Alfamart | IndoRoBERTa | Ready-made | 0.7467 | 0.6963 |
| Alfamart | IndoRoBERTa | Fine-tuned | 0.8311 | 0.7663 |
| Indomaret | IndoBERT | Ready-made | 0.6800 | 0.6372 |
| Indomaret | IndoBERT | Fine-tuned | 0.7778 | 0.7675 |
| Indomaret | IndoRoBERTa | Ready-made | 0.7111 | 0.6811 |
| Indomaret | IndoRoBERTa | Fine-tuned **(selected)** | 0.8489 | 0.8455 |

One-time test evaluation of the selected family only:

| Brand | Accuracy | Macro-precision | Macro-recall | Macro-F1 |
|---|---|---|---|---|
| Alfamart | 0.8133 | 0.7606 | 0.7452 | 0.7497 |
| Indomaret | 0.8311 | 0.8307 | 0.8280 | 0.8278 |

**The test set is opened once.** Model-family selection uses validation macro-F1, with
validation accuracy only as a tie-breaker. Do not re-select on the test set.

Inference then runs over the full deduplicated corpora: 118,604 Alfamart reviews across
3,642 outlets, 74,437 Indomaret reviews across 3,621 outlets. Outlet-level aggregation
yields 3,947 Alfamart and 3,754 Indomaret records; spatial preprocessing retains 3,898
and 3,718 outlets with valid coordinates.

Running these notebooks is optional for reproducing the location models — their output
is already shipped as `data/sentiment/outlet_features_{brand}_x27_x35.csv`.

---

## 4. Fold-safe feature construction

This is the step that makes the evaluation defensible. It must not be shortcut.

For every training/validation split:

1. Partition the development set into five spatial folds by `BLOCK_ID`
   (`GroupKFold`, never a random row split).
2. Draw the shared class-rebalanced sample: at most 2,000 rows, roughly 40% positive.
   The same sample feeds both algorithms so the comparison is paired.
3. Rebuild X26 and X27–X35 for validation grids using **only** target-brand outlets
   located in training blocks.
4. For positive training grids, apply leave-one-grid-out: drop the outlet or outlets
   sitting inside the query grid before constructing its own dynamic features.
5. Impute X1–X25 with training-fold medians.

X24–X25 derive from competitor outlets, not the modelled brand, so they are computed
once and reused.

A correct implementation satisfies:

```python
# no validation-region outlet may contribute to any training-grid feature
assert source_outlet_blocks.issubset(training_blocks)
# a positive training grid never counts itself
assert x26_train[positive_mask].min() >= 0
```

---

## 5. Paired feature benchmark

`scripts/baseline_compare_xgboost_geoxgboost.py`

Three cumulative scenarios under identical folds, targets, samples and class-balancing:
X1–X25, X1–X26, X1–X35.

| Brand | Algorithm | X1–X25 | X1–X26 | X1–X35 | Δ from X26 | Δ from X27–X35 |
|---|---|---|---|---|---|---|
| Alfamart | XGBoost | 0.048773 | 0.048901 | 0.049387 | +0.000128 | +0.000487 |
| Alfamart | GeoXGBoost | 0.026491 | 0.025946 | 0.026132 | −0.000545 | +0.000186 |
| Indomaret | XGBoost | 0.049373 | 0.049361 | 0.051131 | −0.000012 | +0.001769 |
| Indomaret | GeoXGBoost | 0.025995 | 0.025961 | 0.026004 | −0.000034 | +0.000042 |

X26 does not help consistently. X27–X35 adds a small positive increment in all four
combinations.

> These are **pre-optimisation sensitivity references**. The Indomaret baseline was not
> recomputed after the review corpus was expanded from hundreds to thousands of outlets,
> so the deltas should not be read as a refreshed matched effect estimate.

---

## 6. Optuna search

`notebooks/3_optuna_xgboost_geoxgboost_x1_x35.ipynb`

Four independent studies, one per brand–algorithm pair. Objective: Average Precision
over concatenated five-fold inner spatial out-of-fold predictions on the development set.
Each study runs until 20 **valid** trials (COMPLETE + PRUNED); failed trials do not count.

| Brand | Algorithm | Valid | Completed | Pruned | Best trial | Best inner OOF AP |
|---|---|---|---|---|---|---|
| Alfamart | XGBoost | 20 | 18 | 2 | 15 | 0.054749 |
| Alfamart | GeoXGBoost | 20 | 18 | 2 | 16 | 0.043182 |
| Indomaret | XGBoost | 20 | 12 | 8 | 14 | 0.055375 |
| Indomaret | GeoXGBoost | 20 | 17 | 3 | 17 | 0.044687 |

Both GeoXGBoost studies selected an adaptive kernel, bandwidth 240, spatial weights
disabled. The study database is shipped, so `optuna.load_study` reproduces these without
re-running the search.

GeoXGBoost is far more expensive than XGBoost — hours per completed trial against
fractions of a minute. Budget accordingly, or load the shipped study.

---

## 7. Untouched holdout evaluation

`notebooks/4_holdout_topk_evaluation.ipynb`

The holdout is opened once, after tuning and model selection are complete.

| Brand | Algorithm | AP | ROC-AUC | Precision@5% | Recall@5% |
|---|---|---|---|---|---|
| Alfamart | XGBoost | 0.049913 | 0.914025 | 0.052325 | 0.491781 |
| Alfamart | GeoXGBoost | 0.044429 | 0.905022 | 0.045912 | 0.431507 |
| Indomaret | XGBoost | 0.053683 | 0.919591 | 0.052532 | 0.517241 |
| Indomaret | GeoXGBoost | 0.044996 | 0.903668 | 0.045382 | 0.446839 |

Recall across screening budgets:

| Brand | Algorithm | Recall@1% | Recall@5% | Recall@10% |
|---|---|---|---|---|
| Alfamart | XGBoost | 14.11% | 49.18% | 70.14% |
| Alfamart | GeoXGBoost | 11.64% | 43.15% | 68.08% |
| Indomaret | XGBoost | 15.09% | 51.72% | 71.70% |
| Indomaret | GeoXGBoost | 12.36% | 44.68% | 66.81% |

> **Caching caveat.** The deployment stage caches its exported artefacts. If a study is
> re-optimised but the deployment cache is not invalidated, exported layers can carry
> stale `HOLDOUT_AP` and `HOLDOUT_AUC` attributes from the previous run. Set
> `FORCE_REBUILD = True` (or delete the deployment cache) after any re-optimisation, and
> confirm that the exported attributes match the table above before publishing layers.

---

## 8. Candidate deployment

After full-grid scoring, and only then, apply the candidate filter: keep cells with
`target_presence == 0` whose centroid is at least 250 m from an existing same-brand
outlet. Rank the eligible pool and flag exact nested percentile tiers.

| Brand | Eligible | Top 1% | Top 5% | Top 10% |
|---|---|---|---|---|
| Alfamart | 623,220 | 6,233 | 31,161 | 62,322 |
| Indomaret | 625,928 | 6,259 | 31,295 | 62,589 |

The 250 m rule is a screening convenience that stops the list being dominated by adjacent
cells. It is **not** an estimate of cannibalisation distance, and it models neither parcel
boundaries nor road crossings nor catchment overlap.

Nesting must hold:

```python
assert (top1 <= top5).all() and (top5 <= top10).all()
```

---

## 9. Explainability

XGBoost is explained with direct TreeSHAP. GeoXGBoost combines global and local
ensembles, so direct TreeSHAP does not apply to the fitted structure; an XGBoost
regressor is trained to approximate its score surface and only then explained. Those
attributions are labelled **surrogate SHAP** everywhere and are never pooled with direct
values. Fidelity statistics are written to `results/surrogate_quality.csv`; the acceptance
threshold is R² ≥ 0.70 on held-out rows.

Each candidate stores its seven strongest absolute local contributions with signed
direction.

Sentiment appearing among the seven strongest local drivers, Top 10% tier:

| Brand | Algorithm | Sentiment in top 7 | X26 in top 7 | Most frequent sentiment feature |
|---|---|---|---|---|
| Alfamart | XGBoost | 18.842% | 9.339% | X32, stock sentiment change |
| Alfamart | GeoXGBoost | 2.492% | 0.000% | X32, stock sentiment change |
| Indomaret | XGBoost | 18.300% | 1.106% | X32, stock sentiment change |
| Indomaret | GeoXGBoost | 4.269% | 2.329% | X35, service sentiment change |

---

## 10. Post-hoc urban context

The urban-character proxy reproduces the sampling score used during model development and
splits it at quartiles. It is a descriptive aid, **not** an official BPS urban–rural
classification, and nothing in the modelling depends on it.

Top 10% composition:

| Brand | Algorithm | Low urban | Transition | High urban |
|---|---|---|---|---|
| Alfamart | XGBoost | 0.18% | 27.66% | 72.16% |
| Alfamart | GeoXGBoost | 0.26% | 23.71% | 76.04% |
| Indomaret | XGBoost | 0.19% | 28.48% | 71.33% |
| Indomaret | GeoXGBoost | 0.14% | 24.48% | 75.39% |

Spatial coherence of the Top 10% surfaces:

| Brand | Algorithm | Mean adjacent neighbours | Isolated cells | Components per 1,000 |
|---|---|---|---|---|
| Alfamart | XGBoost | 4.831 | 1.271% | 49.116 |
| Alfamart | GeoXGBoost | 5.014 | 0.961% | 39.392 |
| Indomaret | XGBoost | 4.712 | 1.007% | 39.512 |
| Indomaret | GeoXGBoost | 4.836 | 1.184% | 42.851 |

GeoXGBoost is more coherent for Alfamart on all four indicators. For Indomaret the
evidence is mixed: slightly higher adjacency is offset by more isolated cells and more
components. Recommendation morphology is therefore brand- and location-dependent, not a
fixed property of either algorithm. Coherence describes shape, not accuracy — the holdout
still favours XGBoost for both brands.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Alfamart positives = 3,637 not 3,632 | Target rebuilt from the outlet master instead of the shipped partition | Use `data/partition/development_holdout_split.csv` |
| Holdout AP differs in the third decimal | Dynamic features rebuilt outside the fold | Re-check step 4; validation outlets must never feed training features |
| Holdout AP much higher than reported | Row-level split instead of block-level | Split on `BLOCK_ID`, never on row index |
| Exported layers carry old AP values | Deployment cache not invalidated after re-optimisation | Set `FORCE_REBUILD = True` and re-export |
| GeoXGBoost runs for hours | Expected; local models are fitted per training point | Load the shipped study, or reduce the trial budget |
| Surrogate R² below 0.70 | Surrogate under-fitted | Raise `SURROGATE_TRAIN_N`; do not report SHAP below the threshold |
| `shap` additivity error | Version drift | Install the pinned `shap` version |

---

## What reproduction does and does not establish

Reproducing these numbers shows the pipeline is deterministic and the reported metrics are
faithful to the data. It does not establish that a high-ranked grid is a profitable store
site. The target is presence–background: it records where the chain has historically
opened, not where it has succeeded. Treat the output as a screening surface that narrows a
very large metropolitan search space, and pair every candidate with field verification.
