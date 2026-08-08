# CellDefense GeoAI

CellDefense GeoAI is a GeoAI decision-support prototype for identifying and mapping suspicious base-station anomalies.

## Problem

Telecommunications monitoring teams may receive anomalous radio observations caused by legitimate network changes, equipment faults, measurement errors, interference, or suspicious transmitters. Manually reviewing every observation is inefficient.

CellDefense GeoAI will aggregate simulated geolocated radio observations, learn expected local network behaviour, identify spatially corroborated anomalies, and prioritise compact areas for further investigation.

## Pilot Area

The prototype will model an approximately 8 km by 8 km pilot area in Cyberjaya, Sepang, Selangor.

## Primary Users

- MCMC spectrum monitoring and enforcement personnel
- Mobile network security and operations teams
- Authorised field investigation personnel

## MVP Outputs

The prototype will produce:

1. A map of normal and anomalous radio observations.
2. Spatial clusters of corroborated anomalies.
3. An explainable investigation-priority score from 0 to 100.
4. Reason codes explaining why an area was prioritised.
5. A supporting road route to selected investigation areas.

## Detection Scope

The prototype will analyse:

- Unusual received signal strength patterns
- Geographically inconsistent cell identities
- Short-lived or apparently moving base stations
- Abnormal neighbour-cell relationships
- Unusual handover behaviour
- Spatial and temporal corroboration across observations

## Non-Goals

The prototype will not:

- Confirm the presence of an IMSI catcher
- Identify the operator of a suspicious transmitter
- Detect RF jamming
- Diagnose every mobile-network hardware fault
- Collect IMSI, IMEI, MSISDN, message content, or subscriber identity
- Transmit, spoof, jam, or interfere with cellular signals

A high score means that an area should be investigated. It is not proof that a rogue base station exists.

## Data Strategy

The primary dataset will be a reproducible synthetic RF drive-test dataset generated over Cyberjaya roads.

Supporting data may include:

- OpenStreetMap roads and buildings
- An appropriately licensed OpenCellID snapshot
- Public synthetic rogue-base-station research datasets for comparison

M-Lab, packet captures, and application traffic datasets will not be used as sources of RSRP, RSRQ, SINR, cell identity, or handover measurements.

## Ethics and Privacy

The prototype will use synthetic or appropriately anonymised observations. It will not store subscriber identifiers or communications content. Any future real-world measurements must be passively collected using authorised equipment and handled according to applicable privacy, telecommunications, and cybersecurity requirements.

## Current Status

Project scaffolding and environment setup.
