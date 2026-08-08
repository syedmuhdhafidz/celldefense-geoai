# CellDefense GeoAI Synthetic Dataset Card

## 1. Dataset purpose

This dataset supports the development and demonstration of CellDefense
GeoAI, a decision-support prototype for identifying and mapping suspicious
base-station measurement anomalies.

The dataset is designed to test whether geographically corroborated radio
measurements are inconsistent with the expected location and behaviour of a
reported base station. It must not be used to claim that an IMSI catcher,
rogue base station or malicious actor has been confirmed.

## 2. Dataset status

| Item | Description |
| --- | --- |
| Dataset type | Fully synthetic RF drive-test observations |
| Real subscriber data | None |
| Real telecommunications infrastructure | None |
| Intended use | Hackathon research, model development and prototype demonstration |
| Prohibited interpretation | Confirmation of a rogue base station or identification of a person |
| Geographic context | Fictional routes and stations within a Cyberjaya-area bounding box |
| Coordinate reference system | WGS 84 (`EPSG:4326`) |
| Projected analysis system | WGS 84 / UTM zone 47N (`EPSG:32647`) |

## 3. Why synthetic data is the primary dataset

Public internet-performance datasets such as Measurement Lab do not provide
the serving-cell radio measurements required by this use case. In
particular, they do not provide RSRP, RSRQ, SINR, serving-cell identity,
neighbour-cell counts or handover events.

Open public cell-location databases may provide approximate tower or cell
locations, but they do not provide a verified regulator-grade inventory and
do not contain the complete time-aligned RF measurements required by the
prototype.

For these reasons, the current prototype uses explicitly labelled synthetic
drive-test observations. This makes the assumptions inspectable and avoids
misrepresenting unrelated internet-performance data as mobile radio data.

## 4. Geographic coverage

| Property | Value |
| --- | --- |
| Area of interest | Cyberjaya-area synthetic study zone, Malaysia |
| Minimum latitude | 2.89 |
| Maximum latitude | 2.97 |
| Minimum longitude | 101.62 |
| Maximum longitude | 101.70 |
| Synthetic routes | 3 |
| Synthetic reference stations | 8 |
| LTE reference stations | 4 |
| NR reference stations | 4 |

All routes and base-station locations are fictional. Their coordinates do
not represent verified telecommunications infrastructure.

## 5. Time coverage

| Dataset | Start time | End time | Time zone |
| --- | --- | --- | --- |
| Baseline observations | 1 August 2026, 08:00:00 | 1 August 2026, 09:09:59 | Malaysia Time (`UTC+08:00`) |
| Scenario observations | 1 August 2026, 08:00:00 | 1 August 2026, 09:09:59 | Malaysia Time (`UTC+08:00`) |
| Injected anomaly window | 1 August 2026, 08:35:30 | 1 August 2026, 08:36:59 | Malaysia Time (`UTC+08:00`) |

The timestamps are synthetic and do not describe an actual event.

## 6. Dataset size and resolution

| Property | Value |
| --- | --- |
| Observations per route | 600 |
| Total observations | 1,800 |
| Temporal sampling interval | 1 second |
| Baseline scenario observations | 1,710 |
| Injected anomaly observations | 90 |
| Injected anomaly proportion | 5% |
| Geometry type | Point observations sampled along synthetic line routes |

Spatial spacing is determined by interpolation along each fictional route.
It represents simulated drive-test sampling rather than the accuracy or
resolution of a real measurement device.

## 7. Observation variables

| Variable | Type | Unit or values | Purpose |
| --- | --- | --- | --- |
| `observation_id` | String | Unique identifier | Observation traceability |
| `timestamp` | Datetime | Malaysia Time | Temporal analysis |
| `latitude` | Float | Decimal degrees | Observation location |
| `longitude` | Float | Decimal degrees | Observation location |
| `route_id` | String | Synthetic route identifier | Collection-route context |
| `sensor_id` | String | Synthetic sensor identifier | Measurement-source context |
| `operator_id` | String | Synthetic operator identifier | Network context |
| `rat` | Category | `LTE` or `NR` | Radio access technology |
| `cell_id` | String | Synthetic cell identifier | Reported serving-cell identity |
| `pci` | Integer | Synthetic physical cell identity | Radio configuration context |
| `arfcn` | Integer | Synthetic channel number | Frequency-channel context |
| `rsrp_dbm` | Float | dBm | Reference signal received power |
| `rsrq_db` | Float | dB | Reference signal received quality |
| `sinr_db` | Float | dB | Signal-to-interference-plus-noise ratio |
| `ping_ms` | Float | Milliseconds | Simulated network latency |
| `handover_event` | Boolean | `True` or `False` | Simulated serving-cell transition |
| `neighbour_count` | Integer | Count | Number of observed neighbouring cells |
| `scenario` | Category | `baseline` or `cloned_cell` | Synthetic scenario label |
| `is_anomaly` | Boolean | `True` or `False` | Synthetic evaluation label |

The `scenario` and `is_anomaly` fields are retained only for controlled
benchmark evaluation. They are not supplied as inputs to the anomaly model.

## 8. Engineered GeoAI variables

| Variable | Unit or values | Description |
| --- | --- | --- |
| `known_cell` | `0` or `1` | Whether the reported cell exists in the synthetic reference inventory |
| `distance_to_reported_cell_m` | Metres | Haversine distance between the observation and reported cell location |
| `expected_rsrp_dbm` | dBm | Expected RSRP from the simplified distance-based propagation model |
| `rsrp_residual_db` | dB | Measured RSRP minus expected RSRP |
| `absolute_rsrp_residual_db` | dB | Absolute magnitude of the RSRP residual |
| `handover_event_int` | `0` or `1` | Numeric representation of the handover event |
| `signal_distance_inconsistency` | Derived score | Positive RSRP residual weighted by logarithmic distance from the reported cell |

Raw absolute signal strength and distance remain available for explanation,
but they are not directly supplied to the anomaly detector. This reduces
false alerts caused by legitimate observations close to a reference station.

## 9. Synthetic anomaly design

The current scenario simulates a cloned-cell-style geographic inconsistency:

- Observations report the identity of `cell-001`.
- Measurements occur approximately 4.85 kilometres from the fictional
  registered location of `cell-001`.
- The received signal is much stronger than expected at that distance.
- The simulated neighbour count is unusually low.
- Ninety consecutive observations are modified.
- The anomaly occupies a geographically dense section of
  `route-west-east`.

The scenario demonstrates suspicious measurement behaviour only. It does
not reproduce the full protocol behaviour of an IMSI catcher.

## 10. Training and evaluation split

The anomaly detector is trained only on an independently generated synthetic
baseline dataset.

| Dataset role | Random seed | Observations | Anomaly injection |
| --- | ---: | ---: | --- |
| Baseline training dataset | 2026 | 1,800 | None |
| Scenario evaluation baseline | 3030 | 1,800 | Before injection |
| Anomaly injection process | 4040 | 90 modified rows | Cloned-cell-style inconsistency |

Using different random seeds prevents the evaluation dataset from being an
identical copy of the training dataset.

## 11. Current benchmark results

| Metric | Result |
| --- | ---: |
| Point-level precision | 0.8654 |
| Point-level recall | 1.0000 |
| Point-level F1 score | 0.9278 |
| Point-level false-positive rate | 0.0082 |
| True-positive point alerts | 90 |
| False-positive point alerts | 14 |
| Corroborated investigation clusters | 1 |
| True anomaly fraction in the investigation cluster | 1.0000 |
| Isolated alerts not escalated | 14 |

These results measure performance on one synthetic scenario. They do not
establish expected performance in a live telecommunications environment.

## 12. Data quality limitations

- The propagation model is simplified.
- Terrain, buildings, vegetation and indoor penetration are not modelled.
- Antenna height, azimuth, tilt, beamforming and transmission scheduling are
  not modelled in full.
- Device calibration error and vendor-specific measurement behaviour are
  simplified.
- Mobility speed and road conditions are not modelled explicitly.
- Only one injected suspicious-behaviour pattern is currently evaluated.
- Synthetic class labels are exact and therefore cleaner than labels
  expected from real investigations.
- The fictional reference inventory is complete, unlike many real-world
  open cell-location datasets.

## 13. Privacy, security and ethical controls

The dataset contains no:

- IMSI;
- IMEI;
- MSISDN or telephone number;
- subscriber name or account identifier;
- communications content;
- payload;
- browsing history;
- real device identifier; or
- real base-station location.

Any future real-world pilot should apply data minimisation, access controls,
retention limits, device and operator authorisation, and applicable Malaysian
privacy and communications requirements.

## 14. Appropriate use

Appropriate uses include:

- testing geospatial feature engineering;
- benchmarking unsupervised anomaly detection;
- demonstrating spatio-temporal alert corroboration;
- developing investigation-priority maps;
- evaluating human-readable threat explanations; and
- hackathon demonstrations and educational research.

## 15. Inappropriate use

The dataset and prototype must not be used to:

- claim that a real base station is malicious;
- identify or track a subscriber;
- intercept communications;
- locate a person;
- conduct unauthorised active radio transmission;
- replace regulator, operator or law-enforcement verification; or
- report synthetic coordinates as genuine infrastructure.

## 16. Path to real-world validation

A responsible validation programme would require:

1. Authorised passive drive-test measurements from calibrated equipment.
2. A verified reference inventory supplied or validated by an operator or
   regulator.
3. Known benign maintenance and coverage-change periods.
4. Controlled test-lab anomaly scenarios.
5. Independent geographic and temporal test areas.
6. Human review by RF engineering and cybersecurity specialists.
7. Documented false-positive and false-negative analysis.
8. Privacy, retention and access-control review before collection.
