# CellDefense GeoAI Project Brief

## Project title (TBC)

**CellDefense GeoAI: Spatio-Temporal Triage of Suspicious Base-Station Measurements**.

## Theme

Cybersecurity with GeoAI-enabled telecommunications infrastructure
monitoring.

## Executive summary

The original concept has been narrowed into a focused
decision-support problem:

> Identify geographically and temporally corroborated mobile-radio
> measurements that are inconsistent with a reported base-station identity,
> assign an explainable threat score, and prioritise compact areas for
> authorised technical investigation.

The prototype does not confirm a rogue base station. It identifies suspicious
measurement patterns that require further verification.

## 1. Focused real-world problem

### Problem statement

Telecommunications monitoring teams may encounter unusual radio observations
caused by:

- legitimate network optimisation;
- maintenance or configuration changes;
- device measurement error;
- propagation conditions;
- interference;
- incomplete reference data; or
- suspicious transmitters presenting an existing cell identity.

Reviewing every unusual observation individually is inefficient and can
produce excessive false alarms.

CellDefense GeoAI addresses this by combining anomaly detection with
cell-aware spatio-temporal corroboration. Isolated unusual readings remain
available for audit, while dense groups of geographically and temporally
consistent alerts are promoted into investigation areas.

### Decision question

> Which compact geographic areas contain enough mutually corroborating
> radio-measurement anomalies to justify further authorised RF investigation?

### Why the problem matters

NIST’s Mobile Threat Catalogue identifies several cellular threats involving
rogue base stations, including device tracking, downgrade attacks, disruption
of emergency calls and incomplete attachment procedures. These references
establish rogue base stations as a legitimate mobile-security concern, but
they do not imply that RF performance measurements alone can confirm one.

CellDefense therefore maintains a strict boundary between:

- detecting measurement inconsistency; and
- confirming malicious equipment or intent.

References:

- [NIST Mobile Threat Catalogue: cellular threats](https://pages.nist.gov/mobile-threat-catalogue/cellular.html)
- [NIST CEL-2: Device and Identity Tracking via Rogue Base Station](https://pages.nist.gov/mobile-threat-catalogue/cellular-threats/CEL-2.html)
- [NIST CEL-3: Downgrade Attacks via Rogue Base Station](https://pages.nist.gov/mobile-threat-catalogue/cellular-threats/CEL-3.html)
- [NIST assessment of IMSI-catcher threats](https://www.nist.gov/speech-testimony/bolstering-data-privacy-and-mobile-security-assessment-imsi-catcher-threats)

## 2. Stakeholders and roles

| Stakeholder | Operational role | Prototype value |
| --- | --- | --- |
| MCMC spectrum-monitoring personnel | Review suspicious radio observations and coordinate authorised investigation | Prioritised areas, evidence summaries and reduced alert overload |
| MCMC enforcement personnel | Conduct lawful follow-up after technical validation | Geographic investigation zone and supporting access-plan demonstration |
| Mobile-network RF engineers | Review serving-cell configuration, propagation and neighbour relationships | Signal residuals, reported-cell distance and neighbour evidence |
| Mobile-network security teams | Correlate RF anomalies with operator security and operational records | Threat scores and time-bounded clusters |
| Data and GeoAI analysts | Maintain models, thresholds, data quality and evaluation | Reproducible pipeline, diagnostics and benchmark outputs |
| Governance and privacy reviewers | Review collection authority, data minimisation, access and retention | Explicit exclusions, limitations and audit-friendly outputs |

### Team responsibilities

| Team member | Primary responsibility |
| --- | --- |
| Syed Hafidz | Architecture, data design, synthetic generator and integration support |
| Yaseen Ayatullah | GeoAI feature engineering, anomaly modelling and evaluation |
| Harizah Husna | Dashboard, investigation workflow and supporting response-planning interface |
| All members | Testing, documentation, ethical review and final pitch |

Responsibilities may overlap during integration and presentation preparation.

## 3. Area of interest and spatial context

| Property | Definition |
| --- | --- |
| Study context | Fictional Cyberjaya-area pilot |
| Latitude extent | 2.89–2.97 |
| Longitude extent | 101.62–101.70 |
| Approximate area | Approximately 8 km by 8 km |
| Geographic CRS | WGS 84 (`EPSG:4326`) |
| Analysis CRS | WGS 84 / UTM zone 47N (`EPSG:32647`) |
| Synthetic routes | 3 |
| Synthetic stations | 8 |
| Infrastructure status | Entirely fictional |

Cyberjaya provides a recognisable Malaysian urban and technology context.
The selected coordinates do not represent verified telecommunications
infrastructure.

## 4. Dataset inventory

### Primary dataset

| Property | Value |
| --- | --- |
| Source | Reproducible CellDefense synthetic generator |
| Location coverage | Fictional routes within the Cyberjaya-area bounding box |
| Time period | 1 August 2026, 08:00:00–09:09:59 Malaysia Time |
| Temporal resolution | One observation per second |
| Spatial resolution | Point samples interpolated along three fictional routes |
| Observation count | 1,800 |
| Reference stations | 8 fictional LTE and NR stations |
| Scenario observations | 90 cloned-cell-style geographic inconsistencies |
| Scenario proportion | 5% |
| Ground-truth use | Evaluation only, never supplied to the anomaly model |

### Main variables

- latitude and longitude;
- timestamp;
- serving-cell identity;
- radio access technology;
- PCI and ARFCN;
- RSRP;
- RSRQ;
- SINR;
- simulated ping latency;
- neighbour-cell count; and
- handover event.

See [the dataset card](dataset_card.md) and
[the data dictionary](data_dictionary.md).

### Why M-Lab is excluded

M-Lab measures internet performance but does not provide the serving-cell RF
variables required by this project, such as:

- RSRP;
- RSRQ;
- SINR;
- reported serving-cell identity;
- neighbour-cell count; and
- handover events.

Therefore, M-Lab are not presented as the source of the prototype’s RF
measurements.

### Open cell-location data

Open cell-location databases may later be evaluated as supporting contextual
sources. They must not be presented as complete or regulator-verified
infrastructure inventories. Licensing, age, positional accuracy and
completeness must be reviewed before use.

### Primary limitations

- All current measurements are synthetic.
- The propagation model is simplified.
- Buildings, terrain, antenna patterns and beamforming are not fully modelled.
- Only one cloned-cell-style scenario has been evaluated.
- Synthetic labels are cleaner than labels expected from real investigations.
- The fictional reference inventory is complete and internally consistent.

## 5. GeoAI intelligence

The prototype performs analysis rather than merely displaying points on a
map.

### Geographic feature engineering

For each observation, it calculates:

1. Distance to the reported reference-cell location.
2. Expected RSRP at that distance.
3. Measured-minus-expected RSRP residual.
4. Absolute RSRP residual.
5. Whether the reported cell exists in the reference inventory.
6. A signal-distance inconsistency feature.

The signal-distance feature increases when a measurement is both:

- substantially stronger than expected; and
- geographically distant from the reported cell.

### Machine-learning anomaly detection

An unsupervised Isolation Forest is trained using an independently generated
baseline dataset.

Model inputs:

- neighbour-cell count;
- handover-event indicator;
- known-cell indicator;
- RSRP residual;
- absolute RSRP residual; and
- signal-distance inconsistency.

The model produces:

- a point-level anomaly prediction; and
- a normalised threat score from 0 to 100.

### Spatio-temporal corroboration

Predicted point alerts are processed using cell-aware DBSCAN.

Two observations can become neighbours only when they are:

- associated with the same reported cell identity;
- within 200 metres; and
- within a 120-second temporal neighbourhood.

At least five observations are required to establish density.

This prevents:

- different reported cells from contaminating one cluster;
- events separated substantially in time from being merged; and
- isolated point alerts from automatically becoming investigation areas.

### Site prioritisation

Investigation clusters are ranked by:

1. maximum threat score; then
2. number of corroborated observations.

The resulting `priority_rank` is distinct from the internal DBSCAN cluster
identifier.

### Supporting access planning

For each priority area, the prototype:

1. finds the nearest fictional drive route;
2. projects an access point onto that route;
3. compares route distance from both endpoints; and
4. selects the shorter endpoint-to-access path.

This demonstrates how a prioritised site could feed a response workflow.
It is not real road navigation.

## 6. Prototype outputs

The working Streamlit prototype provides five views:

### Investigation map

- Synthetic drive routes.
- Fictional LTE and NR reference stations.
- Isolated point alerts.
- Corroborated priority alerts.
- A 200-metre investigation zone.
- Geographic inconsistency with the reported station.
- A supporting fictional access route.

### Priority queue

- Explicit priority rank.
- Reported cell identity.
- Observation count.
- Mean and maximum threat scores.
- Cluster centroid.
- Start and end time.

### Response plan

- Selected fictional route.
- Selected staging endpoint.
- Route distance.
- Off-route distance.
- Staging and access coordinates.

### Threat evidence

- Normal 1st–99th percentile range.
- Suspicious-cluster median.
- Human-readable interpretation.
- Synthetic benchmark metrics.

### Governance and limitations

- Privacy exclusions.
- Appropriate-use boundaries.
- Technical limitations.
- Authorised-validation requirements.

## 7. Technology stack

| Layer | Current technology |
| --- | --- |
| Programming language | Python 3.13 |
| Tabular processing | pandas and NumPy |
| Geospatial processing | GeoPandas and Shapely |
| Machine learning | scikit-learn |
| Coordinate transformations | pyproj through GeoPandas |
| Static visualisation | Matplotlib |
| Interactive mapping | Folium and streamlit-folium |
| Dashboard | Streamlit |
| Model persistence | joblib |
| Data formats | Parquet, CSV, JSON and WKT |
| Testing | pytest |
| Version control | Git |

PostgreSQL/PostGIS is unnecessary for the present 1,800-observation MVP.
It becomes relevant if a future pilot requires multi-user access, larger
histories, spatial indexing and operational data governance.

## 8. Ethics, privacy, quality and sustainability

### Data minimisation

The current prototype stores no:

- IMSI;
- IMEI;
- MSISDN;
- subscriber name;
- subscriber account;
- message or call content;
- network payload;
- browsing history; or
- real device identifier.

### Claim boundary

The prototype may state:

> Measurements in this area are geographically and temporally inconsistent
> with the learned synthetic baseline and should be investigated.

It must not state:

> An IMSI catcher has been detected.

### Human oversight

Every investigation area requires human review. Model and cluster outputs
must not automatically trigger enforcement action.

### Field activity

Future measurements must be:

- authorised;
- passive unless separate lawful authority permits otherwise;
- collected with calibrated equipment;
- access-controlled;
- retained only as necessary; and
- reviewed under applicable Malaysian privacy, communications and
  cybersecurity requirements.

### Sustainability

The MVP uses a small unsupervised model and compact tabular dataset rather
than computationally expensive deep learning. Reproducible generation also
avoids repeatedly storing large duplicate datasets.

## 9. Measurable value and expected impact

### Current synthetic benchmark

| Metric | Result |
| --- | ---: |
| Point precision | 86.5% |
| Point recall | 100.0% |
| Point F1 score | 92.8% |
| Point false-positive rate | 0.82% |
| True-positive point alerts | 90 |
| False-positive point alerts | 14 |
| Corroborated investigation areas | 1 |
| Alerts in the investigation cluster | 90 |
| Isolated alerts not escalated | 14 |
| Investigation-cluster anomaly fraction | 100.0% |

### Operational value hypothesis

The prototype is designed to:

- reduce the number of isolated alerts escalated for field investigation;
- focus analyst attention on compact, evidence-supported areas;
- provide transparent reasons for prioritisation;
- make anomaly results geographically inspectable; and
- create a reproducible hand-off from analysis to authorised assessment.

### Pilot KPIs

A future authorised pilot should measure:

| KPI | Purpose |
| --- | --- |
| Point-level precision and recall | Evaluate detector accuracy |
| Cluster-level precision and recall | Evaluate operational investigation areas |
| False investigation areas per collection hour | Estimate analyst and field workload |
| Median time from ingestion to prioritisation | Measure operational timeliness |
| Analyst acceptance or rejection rate | Assess decision usefulness |
| Stability across devices, routes and days | Measure generalisability |
| Performance under legitimate network changes | Measure false-alert resilience |
| Percentage of alerts with complete explanations | Measure transparency |
| Compute time and memory per observation batch | Measure scalability |

No real-world target should be claimed until authorised pilot data exists.

## 10. ASEAN strategic alignment

### ASEAN Digital Masterplan 2030

The ASEAN Digital Masterplan 2030 establishes regional direction for
2026–2030 and includes:

- Desired Outcome 1: seamless and inclusive digital infrastructure;
- Desired Outcome 4: a resilient, secured and trusted digital ecosystem; and
- Desired Outcome 7: sustainable, green and AI-driven digital
  transformation.

CellDefense aligns most directly with Desired Outcome 4 by demonstrating
cybersecurity risk triage for telecommunications infrastructure. Its
privacy-by-design controls and explicit AI limitations also support trusted
and responsible digital transformation.

The Masterplan stresses cybersecurity capability, earlier threat detection,
coordinated incident response, privacy, AI assurance and evidence-based pilot
initiatives.

Reference:

- [ASEAN Digital Masterplan 2030](https://asean.org/book/asean-digital-masterplan-2030/)
- ADM 2030 PDF: Desired Outcome 4 on PDF page 16; responsible AI
  oversight on PDF pages 18 and 53; outcome metrics on PDF page 64.

### AEC Strategic Plan 2026–2030

Relevant strategic measures include:

- Measure 3.1.8: strengthen online safety and cybersecurity;
- Measure 3.11.1: establish secure and resilient digital infrastructure
  within ASEAN; and
- Measure 6.2.2: enhance the resilience of ICT infrastructure and
  connectivity in rural areas.

CellDefense supports these objectives as an early-stage monitoring and
decision-support concept for resilient telecommunications infrastructure.

References:

- AEC Strategic Plan 2026–2030 PDF: PDF pages 35–36, 45 and 61.
- [Bangko Sentral ng Pilipinas overview of the AEC Strategic Plan 2026–2030](https://www.bsp.gov.ph/Pages/AboutTheBank/WhoWeAre/MandateFunctionsAndResponsibilities/InternationalEconomicCooperation/InternationalEconomicCooperationASEAN.aspx?ID=1515)

## 11. Bootcamp-method alignment

The “From GeoAI Insights to Impact” module from Bootcamp 2 - Advance GeoAI, Day 3, emphasises that:

- an MVP should provide an inspectable interactive evidence interface;
- results should distinguish what can and cannot be claimed;
- evidence should focus stakeholder attention rather than replace decisions;
- a prototype becomes operational only after pilot validation, official data
  integration, field assessment and implementation planning.

CellDefense implements these principles through:

- an interactive map and evidence table;
- clear statement of claim boundaries;
- a ranked shortlist rather than an automated enforcement conclusion;
- a governance and limitations view; and
- an explicit validation roadmap.

Reference:

- Bootcamp 2 - Advance GeoAI, Day 3,
  `Module 7_AD1003_Session 7_From GeoAI Insights to Impact.pdf` slides 3–7.

## 12. Practical roadmap

### Completed MVP

- Synthetic reference network and drive routes.
- Reproducible baseline generator.
- Cloned-cell-style scenario injector.
- Geographic feature engineering.
- Isolation Forest anomaly detector.
- Threat-score normalisation.
- Cell-aware spatio-temporal DBSCAN.
- Investigation-area ranking.
- Feature diagnostics.
- Static maps.
- Interactive dashboard.
- Supporting fictional access planning.
- Automated tests and one-command pipeline.

### Checklist

1. Conduct threshold-sensitivity experiments.
2. Test at least one benign network-change scenario.
3. Add a model and method card.
4. Record a reproducible demonstration.
5. Prepare a concise pitch deck.
6. Validate the claim boundary and stakeholder workflow.
7. Confirm that every chart labels the data as synthetic.

### Future validation

1. Obtain governance and legal approval.
2. Define a data-sharing arrangement with an operator or regulator.
3. Collect authorised passive measurements using calibrated equipment.
4. Integrate a verified reference-cell inventory.
5. Validate across different days, routes, devices and network conditions.
6. Test controlled benign and suspicious scenarios.
7. Review false investigation areas with RF engineers.
8. Replace fictional routing with an authorised road-network source.
9. Define operational ownership, monitoring and model-update procedures.

## Final pitch statement

> "CellDefense GeoAI does not claim to detect an IMSI catcher. It uses
> geospatially engineered radio features, unsupervised anomaly detection and
> cell-aware spatio-temporal corroboration to transform noisy point alerts
> into explainable, ranked areas for authorised technical investigation."
