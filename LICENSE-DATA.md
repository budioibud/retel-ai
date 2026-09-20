# Data Licence

The **aggregated data** in this repository — everything under `data/` and `results/` —
is released under the
[Creative Commons Attribution 4.0 International Licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

The **code** — everything under `notebooks/` and `scripts/` — is released separately
under the [MIT Licence](LICENSE).

---

## You are free to

- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, including commercially

## Under the following terms

- **Attribution** — give appropriate credit, provide a link to the licence, and indicate
  if changes were made. Cite the paper and the archived dataset as shown in the
  repository README and `CITATION.cff`.

---

## Third-party sources

The released grid contains **processed predictor values**, not redistributed copies of the
underlying sources. Several of those sources carry their own licences that the CC BY 4.0
grant above does not and cannot override:

| Source | Licence / terms | Status here |
|---|---|---|
| OpenStreetMap (roads, POI) | ODbL 1.0 | Not redistributed. Derived densities and distances only. Attribution: © OpenStreetMap contributors. |
| DEMNAS, RBI, land use (BIG) | Badan Informasi Geospasial terms | Not redistributed. Request from the agency. |
| Zona Nilai Tanah (ATR/BPN) | Agency terms, WMS service | Not redistributed. Derived class values only. |
| WorldPop population | CC BY 4.0 | Not redistributed. Derived zonal values only. |
| VIIRS Nighttime Lights (NOAA/EOG) | Public domain, US Government | Not redistributed. Derived zonal values only. |
| Google Maps POI and reviews | Google Maps Platform Terms of Service | **Not redistributed.** Only aggregated, non-identifying derivatives are released. |

If you rebuild the grid from the original sources rather than using the processed values
here, you are bound by each provider's own terms.

---

## Personal data

No personal data is released. Specifically excluded from this repository:

- raw review text
- reviewer names, display names and profile identifiers
- reviewer profile images
- any record that can be traced to an individual reviewer

What is released instead is outlet-level aggregation: mean polarity per aspect, mean
rating over the most recent twelve months, temporal sentiment change per aspect, and the
number of reviews behind each aggregate. No analysis in this study is conducted at the
level of an individual reviewer.

---

## Disclaimer

The data is provided **as is**, without warranty of any kind. The suitability score is a
relative spatial index derived from historical outlet patterns. It is not a probability,
not a valuation, and not a prediction of commercial success. The authors and Bina
Nusantara University accept no liability for commercial decisions made on the basis of
this material.

Any real siting decision requires field survey, parcel availability and legal status
checks, zoning and permit verification, rent negotiation, access and visibility
assessment, flood-risk and logistics review, and financial feasibility analysis. None of
these are modelled here.
