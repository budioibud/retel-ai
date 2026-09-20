# Data Dictionary — Predictors X1–X35

Every predictor is stored as a `float64` column named `x1` … `x35` in
`data/grid/grid_{brand}_x1_x35.parquet`, one value per 100 × 100 m cell.

All distance and density operations were performed in **EPSG:32748**
(WGS 84 / UTM zone 48S), so distances are in metres and densities in metric units.

Conventions used in the "Construction" column:

- **Raster → grid**: zonal mean of raster pixels falling inside the cell.
- **Polygon → grid**: rasterised, then dominant class or binary indicator.
- **Line → grid**: total length inside the cell divided by cell area.
- **Point → distance**: Euclidean distance from the cell centroid to the nearest feature.
- **Point → KDE**: kernel density estimate rasterised and rescaled to a 0–1 index.

---

## X1–X2 · Physical and land conditions

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X1 | Elevation | DEMNAS (BIG) | Raster → grid, mean elevation in metres | Shared |
| X2 | Land-use type | Land use / RBI 1:10,000 (BIG) | Polygon → grid, dominant class coded built-up vs non-built-up | Shared |

> X1 is elevation, not slope. A high-elevation cell can still be flat. Slope is not
> a feature in this study, so no claim about terrain steepness can be made from X1
> alone. Verify slope from a DEM before finalising any site.

## X3–X6 · Accessibility and transport

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X3 | Road-network density | OpenStreetMap, road lines | Line → grid, km per km² | Shared |
| X4 | Distance to nearest main road | OpenStreetMap, primary/secondary roads | Point/line → distance, metres | Shared |
| X5 | Distance to nearest station entrance | OpenStreetMap / POI, station entrances | Point → distance, metres | Shared |
| X6 | Distance to nearest bus stop | OpenStreetMap / POI, bus stops | Point → distance, metres | Shared |

## X7–X9 · Economic activity and demography

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X7 | Nighttime light intensity | VIIRS Nighttime Lights | Raster → grid, mean radiance | Shared |
| X8 | Population density | WorldPop population raster | Raster → grid, persons per cell | Shared |
| X9 | Land-value / rent proxy | ATR/BPN Zona Nilai Tanah (WMS) | WMS RGB → raster class, used as a rent proxy | Shared |

> X7 is used as an activity proxy, consistent with established use of nighttime light
> in urban–rural characterisation. X9 is a zonal land-value class, not a market rent quote.

## X10–X12 · Market demand

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X10 | Distance to nearest mall | Google Maps POI | Point → distance, metres | Shared |
| X11 | Distance to nearest office building | Google Maps POI | Point → distance, metres | Shared |
| X12 | Distance to nearest university | Google Maps POI | Point → distance, metres | Shared |

## X13–X23 · Functional zoning and points of interest

All eleven are kernel density indices rescaled to 0–1.

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X13 | Transport facilities | OpenStreetMap / POI | Point → KDE, 0–1 | Shared |
| X14 | Food services | Google Maps POI | Point → KDE, 0–1 | Shared |
| X15 | Residential areas | Land use (BIG) | Polygon → binary indicator | Shared |
| X16 | Culture, science and education | Google Maps POI | Point → KDE, 0–1 | Shared |
| X17 | Shopping services | Google Maps POI | Point → KDE, 0–1 | Shared |
| X18 | Life services | OpenStreetMap POI | Point → KDE, 0–1 | Shared |
| X19 | Medical facilities | Google Maps POI | Point → KDE, 0–1 | Shared |
| X20 | Tourism sites | Google Maps POI | Point → KDE, 0–1 | Shared |
| X21 | Sport and recreation | Google Maps POI | Point → KDE, 0–1 | Shared |
| X22 | Government institutions | GeoServer / WFS | Point → KDE, 0–1 | Shared |
| X23 | Corporate business | Google Maps POI | Point → KDE, 0–1 | Shared |

## X24–X25 · Competition

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X24 | Distance to nearest competitor | Competitor outlet POI | Point → distance, metres | **Brand-specific** |
| X25 | Competitor density | Competitor outlet POI | Point → KDE, 0–1 | **Brand-specific** |

> "Competitor" means the rival chain: for the Alfamart dataset the competitors are
> Indomaret outlets, and vice versa. X24–X25 are computed once from competitor outlets,
> not from the modelled brand, so they carry no target leakage and need no fold-wise rebuild.

## X26 · Same-brand network context

| Code | Name | Source | Construction | Scope |
|---|---|---|---|---|
| X26 | Count of same-brand outlets within 500 m | Brand outlet master | Point count inside a 500 m radius of the cell centroid | **Brand-specific, fold-dependent** |

> X26 is deliberately **not** called retail agglomeration. X24–X25 already carry
> competitor structure, and a high X26 can mean concentrated demand, established
> network coverage, saturation, or cannibalisation at the same time. Its sign is
> context-dependent and it did not improve Average Precision consistently.
>
> **Leakage note.** X26 is derived from the outlets that define the target, so it is
> rebuilt inside every fold using training-region outlets only, with leave-one-grid-out
> applied to positive training cells.

## X27–X35 · Consumer rating and sentiment

Derived from deduplicated public Google Maps reviews, aggregated per outlet, then
propagated to every grid cell within 500 m and averaged where influence areas overlap.

| Code | Name | Construction | Scope |
|---|---|---|---|
| X27 | Mean stock sentiment | Mean review polarity among reviews mentioning stock | **Brand-specific, fold-dependent** |
| X28 | Mean queue / cashier sentiment | Mean polarity among reviews mentioning queues or cashiers | idem |
| X29 | Mean price sentiment | Mean polarity among reviews mentioning price | idem |
| X30 | Mean service sentiment | Mean polarity among reviews mentioning service | idem |
| X31 | Mean rating, last 12 months | Mean star rating over the most recent 12 months, falling back to all valid ratings when none is recent | idem |
| X32 | Stock sentiment change | Mean of newer chronological half minus older half, stock reviews | idem |
| X33 | Queue sentiment change | idem, queue reviews | idem |
| X34 | Price sentiment change | idem, price reviews | idem |
| X35 | Service sentiment change | idem, service reviews | idem |

**Polarity coding.** The selected brand-specific transformer maps each review to
−1 (negative), 0 (neutral) or +1 (positive). Aspect mentions are detected with
transparent keyword dictionaries; a review mentioning several aspects contributes its
review-level polarity to each of them, which means mixed sentiment inside one review
cannot be resolved.

**Zero is ambiguous.** In X27–X30 and X32–X35, a zero may mean neutral sentiment,
no review mentioning that aspect, or too few dated reviews to compute a change. These
three cases are not distinguished in the released features. Do not read zero as
observed neutrality.

**Coverage is uneven.** Grids carrying at least one sentiment signal:

| Urban class | Alfamart | Indomaret |
|---|---|---|
| High urban character | 69.43% | 58.13% |
| Transition zone | 16.96% | 12.46% |
| Low urban character | 0.71% | 0.44% |

Over 99% of low-urban grids receive no sentiment signal from nearby outlets, so in those
areas the models rely almost entirely on the spatial predictors.

---

## Feature groups used in the explainability analysis

| Group | Features |
|---|---|
| Physical / land conditions | X1–X2 |
| Accessibility / transport | X3–X6 |
| Economic activity / demography | X7–X9 |
| Market demand | X10–X12 |
| Functional zoning / POI | X13–X23 |
| Competition | X24–X25 |
| Same-brand network | X26 |
| Sentiment / rating | X27–X35 |

---

## Static versus dynamic features

| Class | Features | Handling |
|---|---|---|
| **Static** | X1–X25 | Computed once over the whole grid. Missing values imputed with training-fold medians. |
| **Dynamic** | X26–X35 | Rebuilt inside every training/validation split from training-region outlets only, with leave-one-grid-out on positive training cells. |

This split is the core of the leakage-aware design. Computing X26–X35 once, before
splitting, would let a validation outlet reveal itself through its own count and its own
reviews.

---

## Source acquisition notes

To rebuild the grid from scratch rather than using the released processed values:

| Source | Access | Notes |
|---|---|---|
| DEMNAS | https://tanahair.indonesia.go.id | National DEM, requires registration |
| RBI / land use 1:10,000 | BIG | Agency request |
| OpenStreetMap | Geofabrik Indonesia extract | ODbL; record the extract date |
| VIIRS Nighttime Lights | NOAA / Earth Observation Group | Annual composite |
| WorldPop | https://www.worldpop.org | Indonesia population raster |
| ZNT land value | ATR/BPN WMS | Served as RGB tiles; class recovered by colour mapping |
| Google Maps POI and reviews | Places API and browser automation | Subject to platform terms; only aggregates are redistributed |
| Administrative boundaries | BIG / GeoServer WFS | Province, regency/city, district, village |

Record the acquisition date for every layer. POI and review data drift continuously, so a
rebuild performed later will not reproduce the released grid byte for byte.
