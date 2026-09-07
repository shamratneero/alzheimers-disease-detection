# ADNI MCI Progression

Predicting progression from mild cognitive impairment (MCI) to Alzheimer's disease
using data from the Alzheimer's Disease Neuroimaging Initiative (ADNI).

## Project structure

```
adni-mci-progression/
├── data/
│   ├── raw/         # immutable source data (never edited, never committed)
│   ├── interim/     # intermediate, partially cleaned data
│   └── processed/   # final analysis-ready datasets
├── src/             # source code (loading, features, models, evaluation)
├── outputs/         # figures, tables, model artifacts
├── docs/            # notes, protocol, data dictionary
├── README.md
└── .gitignore
```

## Data access

ADNI data is restricted. Request access at https://adni.loni.usc.edu and place the
downloaded files in `data/raw/`. Nothing under `data/` is tracked by git.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

TBD — document the pipeline entry points here as `src/` fills in.
