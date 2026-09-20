# Data Dictionary — Predictors X1–X35

Complete definition of all 35 spatial predictors in the RitelAI dataset. All operations performed in **EPSG:32748** (WGS 84 / UTM zone 48S).

---

## X1–X2 · Physical and Land Conditions

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X1 | Elevation | DEMNAS (BIG) | Raster → grid zonal mean, metres | High-elevation ≠ steep; verify slope from DEM for site decisions |
| X2 | Land-use type | Land use / RBI 1:10,000 (BIG) | Polygon → rasterised, dominant class (built-up vs non) | Binary: 0 = non-built, 1 = built-up |

---

## X3–X6 · Accessibility and Transport

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X3 | Road-network density | OpenStreetMap | Line → grid, km per km² | Higher = better connectivity |
| X4 | Distance to main road | OSM primary/secondary roads | Euclidean distance from centroid, metres | Closer = better access |
| X5 | Distance to station | OSM/POI station entrances | Euclidean distance, metres | Transit access proxy |
| X6 | Distance to bus stop | OSM/POI bus stops | Euclidean distance, metres | Transit access proxy |

---

## X7–X9 · Economic Activity and Demography

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X7 | Nighttime light intensity | VIIRS Nighttime Lights (NOAA/EOG) | Raster → zonal mean radiance | Economic activity proxy |
| X8 | Population density | WorldPop raster | Raster → zonal sum, persons per cell | Demand proxy |
| X9 | Land-value proxy | ATR/BPN Zona Nilai Tanah (WMS) | WMS RGB → class (1–5) | Rent/commercial value proxy |

---

## X10–X12 · Market Demand

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X10 | Distance to mall | Google Maps POI | Euclidean distance, metres | Shopping centre proximity |
| X11 | Distance to office | Google Maps POI | Euclidean distance, metres | Office worker concentration |
| X12 | Distance to university | Google Maps POI | Euclidean distance, metres | Student population proxy |

---

## X13–X23 · Functional Zoning and Points of Interest

All are kernel density estimates rescaled to [0, 1].

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X13 | Transport facilities | OSM POI | KDE, 0–1 | Stations, terminals, hubs |
| X14 | Food services | Google Maps | KDE, 0–1 | Restaurants, cafes |
| X15 | Residential areas | Land use (BIG) | Binary: 1 if residential | Foot traffic source |
| X16 | Culture, science, education | Google Maps | KDE, 0–1 | Museums, libraries, schools |
| X17 | Shopping services | Google Maps | KDE, 0–1 | Retail, boutiques |
| X18 | Life services | OSM POI | KDE, 0–1 | Hair salons, laundry, etc. |
| X19 | Medical facilities | Google Maps | KDE, 0–1 | Clinics, hospitals |
| X20 | Tourism sites | Google Maps | KDE, 0–1 | Attractions, hotels |
| X21 | Sport and recreation | Google Maps | KDE, 0–1 | Gyms, parks |
| X22 | Government institutions | GeoServer WFS | KDE, 0–1 | Offices, agencies |
| X23 | Corporate business | Google Maps | KDE, 0–1 | Office parks, business centres |

---

## X24–X25 · Competition

| Code | Name | Source | Construction | Notes |
|---|---|---|---|---|
| X24 | Distance to competitor | Competitor outlet POI | Euclidean distance, metres | **Brand-specific**: Indomaret for Alfamart model, vice versa |
| X25 | Competitor density | Competitor outlet POI | KDE, 0–1 | **Brand-specific**, same definition |

> For Alfamart model: competitors = Indomaret outlets (and vice versa). No target leakage; computed once from competitor network, not from modelled brand.

---

## X26 · Same-Brand Network Context

| Code | Name | Construction | Notes |
|---|---|---|---|
| X26 | Same-brand outlets within 500 m | Point count inside radius | **Brand-specific, fold-dependent**: Rebuilt inside every fold using training-region outlets only. Leave-one-grid-out applied to positive training cells. High value may indicate concentration, saturation, or cannibalisation. Sign is context-dependent. |

**Leakage handling:** X26 derived from target outlets, so must be rebuilt inside cross-validation using training blocks only. Validation outlets never contribute to training-grid features.

---

## X27–X35 · Consumer Rating and Sentiment

Derived from deduplicated public Google Maps reviews, aggregated per outlet, then **propagated to every grid cell within 500 m** and averaged where influence areas overlap.

| Code | Name | Construction | Scope |
|---|---|---|---|
| X27 | Mean stock sentiment | Mean review polarity [−1, 1] for reviews mentioning stock | Brand-specific, fold-dependent |
| X28 | Mean queue/cashier sentiment | Mean polarity for queue/cashier reviews | Brand-specific, fold-dependent |
| X29 | Mean price sentiment | Mean polarity for price reviews | Brand-specific, fold-dependent |
| X30 | Mean service sentiment | Mean polarity for service reviews | Brand-specific, fold-dependent |
| X31 | Mean rating, last 12 months | Mean star rating (most recent 12m, fallback all valid) | Brand-specific, fold-dependent |
| X32 | Stock sentiment change | Newer half mean − older half mean, stock reviews | Brand-specific, fold-dependent |
| X33 | Queue sentiment change | Newer half − older half, queue reviews | Brand-specific, fold-dependent |
| X34 | Price sentiment change | Newer half − older half, price reviews | Brand-specific, fold-dependent |
| X35 | Service sentiment change | Newer half − older half, service reviews | Brand-specific, fold-dependent |

**Polarity coding:** Transformer model (IndoBERT or IndoRoBERTa, fine-tuned on brand-specific reviews) maps each review to −1 (negative), 0 (neutral), or +1 (positive). Aspect mentions detected via keyword dictionaries; a review mentioning multiple aspects contributes its review polarity to each.

**Zero is ambiguous** in X27–X30 and X32–X35:
- May mean neutral sentiment observed
- May mean no review mentioning that aspect
- May mean too few dated reviews to compute change

Distinguish using `n_reviews` and `n_reviews_recent_12m` columns in outlet-level CSV files (not in gridded features).

**Coverage by urban class:**

| Urban character | Alfamart (% grids with signal) | Indomaret (% grids with signal) |
|---|---|---|
| High urban | 69.43% | 58.13% |
| Transition | 16.96% | 12.46% |
| Low urban | 0.71% | 0.44% |

Over 99% of low-urban grids receive no sentiment signal from nearby outlets; models rely on spatial predictors there.

---

## Feature Group Summary

| Group | Features | Type | Handling |
|---|---|---|---|
| Physical / land | X1–X2 | Static | Computed once; missing → training-fold median |
| Accessibility / transport | X3–X6 | Static | idem |
| Economic / demographic | X7–X9 | Static | idem |
| Market demand | X10–X12 | Static | idem |
| Functional zoning / POI | X13–X23 | Static | idem |
| Competition | X24–X25 | Static | Computed once; no fold-wise rebuild (no target leakage) |
| Same-brand network | X26 | **Dynamic** | **Rebuilt inside every fold** from training outlets only |
| Sentiment / rating | X27–X35 | **Dynamic** | **Rebuilt inside every fold** from training outlets only |

**Static (X1–X25)** computed once over the whole grid. Missing values imputed with training-fold medians during feature construction.

**Dynamic (X26–X35)** rebuilt for each training/validation split to prevent leakage. Validation outlets never feed training-grid features.

---

## Coordinate Systems

All distances and density operations in **EPSG:32748** (WGS 84 / UTM zone 48S):
- Distances in metres
- Densities in metric units (per km² or per cell)

Candidate layers reprojected to **EPSG:4326** for web display and GeoPackage files.

---

## Source Access

To rebuild from original sources (not using released processed values):

| Source | Access | Notes |
|---|---|---|
| DEMNAS | https://tanahair.indonesia.go.id | National DEM, requires registration |
| RBI / land use 1:10,000 | BIG (Badan Informasi Geospasial) | Agency request |
| OpenStreetMap | Geofabrik Indonesia | Record extract date (ODbL 1.0) |
| VIIRS Nighttime Lights | NOAA / Earth Observation Group | Annual composite, public domain |
| WorldPop | https://www.worldpop.org | CC BY 4.0; Indonesia population raster |
| Zona Nilai Tanah (ZNT) | ATR/BPN WMS | Served as RGB tiles; class via colour mapping |
| Google Maps POI & reviews | Places API + browser automation | Subject to Google Maps Platform ToS; only aggregates released |
| Administrative boundaries | BIG / GeoServer WFS | Province, regency, district, village |

**Important:** POI and review data drift continuously. A rebuild months or years later will not match byte-for-byte.

---

## How the predictors feed the models

1. **X1–X25 (static):** Used as-is in every fold
2. **X26 (same-brand count):** Rebuilt per fold using training-region outlets only; leave-one-grid-out for positive training cells
3. **X27–X35 (sentiment):** Rebuilt per fold using training-region outlets and their reviews only; aggregation includes leave-one-grid-out

This fold-aware design ensures validation metrics reflect generalization to unseen locations and time periods, not internal memorisation.
