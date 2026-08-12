# Artificial Intelligence Disclosure

## Purpose

This document discloses how artificial intelligence and AI-assisted tools were used in the development of CellDefense GeoAI.

CellDefense GeoAI was developed with AI assistance. The project team remains responsible for the final system design, source code, data, testing, interpretation, documentation and presentation claims.

## AI and Machine Learning Used in the Prototype

The prototype contains the following machine-learning and spatial-analysis components:

### Isolation Forest

Scikit-learn's unsupervised Isolation Forest is trained on synthetic baseline radio-frequency observations.

It is used to:

- learn the statistical pattern of the synthetic baseline;
- identify unusual point-level measurements;
- produce an anomaly score that is normalised into an investigation-priority score from 0 to 100.

The resulting score is not a calibrated probability and is not proof of malicious activity.

### Spatio-Temporal DBSCAN

A cell-aware DBSCAN clustering process corroborates point alerts using:

- geographic proximity;
- temporal proximity;
- reported cell identity;
- a minimum number of supporting observations.

DBSCAN is used to separate spatially and temporally corroborated investigation areas from isolated point alerts.

It does not classify a transmitter as malicious or confirm the presence of an IMSI catcher.

## Generative-AI and AI-Assisted Development Tools

### OpenAI ChatGPT and Codex

OpenAI ChatGPT and Codex were used as development-assistance tools for:

- project ideation and scope refinement;
- research synthesis and dataset assessment;
- code drafting and code review;
- feature-engineering guidance;
- debugging and error diagnosis;
- automated-test drafting and interpretation;
- dashboard wording and responsible-use safeguards;
- technical documentation;
- presentation planning and reference visual generation.

AI-generated or AI-suggested code was reviewed, modified and tested by the project team before being retained.

### Google Stitch

Google Stitch was used to generate interface design concepts and visual references for the Streamlit dashboard.

The team reviewed these concepts and manually adapted suitable elements to the working dashboard. Google Stitch did not generate or deploy the final operational Streamlit application.

## Data Generation and Processing

The current prototype uses reproducible synthetic RF drive-test observations and fictional reference base stations.

AI assistance was used when designing and reviewing parts of the synthetic-data generation and processing workflow. The implemented generation logic is contained in the repository and can be inspected, rerun and tested.

The prototype does not process:

- IMSI;
- IMEI;
- MSISDN;
- subscriber identity;
- communications content;
- message payloads;
- verified live mobile-network infrastructure data.

## Visual and Presentation Materials

AI tools assisted with:

- dashboard design exploration;
- presentation structure and wording;
- reference slide-layout mock-ups;
- visual annotation recommendations.

Final presentation materials were selected, edited and assembled by the project team. Any AI-generated reference visual used directly in a final submission will be identified as AI-generated or AI-assisted.

## Human Review and Validation

AI-assisted outputs were not accepted automatically.

The project team:

- selected the problem definition and project scope;
- selected the final algorithms and model parameters;
- reviewed and modified suggested source code;
- inspected generated synthetic data;
- verified dashboard outputs;
- ran the automated test suite;
- reviewed ethical, privacy and claim-boundary language;
- approved the final documentation and presentation.

At the time of this disclosure, the repository test suite contains 46 passing automated tests.

Passing tests establish consistency with the implemented synthetic prototype requirements. They do not establish real-world telecommunications accuracy.

## Claim Boundaries

CellDefense GeoAI is a decision-support prototype.

It identifies suspicious measurement inconsistencies and prioritises areas for authorised technical investigation. It does not:

- confirm an IMSI catcher or rogue base station;
- determine malicious intent;
- identify the operator of a transmitter;
- provide a calibrated probability of malicious activity;
- replace authorised technical investigation;
- provide a route suitable for real navigation or deployment.

All reported model-performance results apply only to the controlled synthetic benchmark scenario.

## Accountability

The project team accepts responsibility for:

- the final source code;
- the selected methodology;
- the synthetic data design;
- the reported results;
- the dashboard;
- the documentation;
- the presentation;
- all interpretations and claims made about the prototype.

AI-tool outputs should not be interpreted as independent verification or endorsement of the project.
