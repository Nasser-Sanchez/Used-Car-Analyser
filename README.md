# Used Car Analyser

Exploratory analysis and data enrichment pipeline for vehicle pricing datasets.

## Overview

This project explores vehicle pricing patterns through data enrichment and statistical modelling. It combines:

- **Python** — Data processing, LLM-assisted enrichment, and statistical analysis
- **Jupyter Notebooks** — Interactive exploration and visualization
- **Google BigQuery** — Cloud data storage and querying

## Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.11 |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Data Processing | pandas, pydantic |
| Analysis | seaborn, shap, statsmodels |
| LLM | LM Studio (local inference) |
| Cloud | Google BigQuery |
| IDE | VS Code |

## Setup

```bash
# Install dependencies
uv sync
```

## Project Structure

```
.
├── src/
│   ├── car_data_analysis.ipynb     # Exploratory analysis and modelling
│   ├── llm_enrichment.py           # LLM-assisted data enrichment
│   ├── join_llm_data.py            # Merge datasets
│   ├── add_hash.py                 # Record deduplication utilities
│   ├── carmax_scraper_jsonld.ipynb # [archived] legacy data collection
│   └── Carmax USA.R                # [archived] legacy data collection
├── data/                             # Raw and processed data (not in git)
├── pyproject.toml                    # Dependencies and project metadata
├── uv.lock                           # Locked dependency versions
└── .python-version                   # Python version pin (3.11)
```

## Usage

### Analysis

Open the analysis notebook for exploratory data analysis and modelling:

```bash
uv run jupyter notebook src/car_data_analysis.ipynb
```

### Data Enrichment

```bash
uv run python src/llm_enrichment.py
```

Outputs:
- `carmax_specifications.csv` — enriched vehicle specifications
- `carmax_errors.csv` — enrichment failure log
- `carmax_telemetry.csv` — model call metrics

```bash
uv run python src/join_llm_data.py
```

Outputs:
- `carmax_usa_enriched.csv` — merged dataset

## Data Files

| File | Description | In Git? |
|------|-------------|---------|
| `carmax_USA.csv` | Vehicle listings dataset | ✅ (tracked) |
| `carmax_specifications.csv` | Enriched specs | ❌ (large) |
| `carmax_telemetry.csv` | Model call logs | ❌ (large) |
| `carmax_errors.csv` | Enrichment errors | ❌ (small) |
| `carmax_usa_enriched.csv` | Final merged dataset | ❌ (large) |

Large CSV files are excluded from git. Re-run the enrichment pipeline to regenerate.

## Notes

- LLM enrichment requires LM Studio running locally
- BigQuery integration needs `GOOGLE_APPLICATION_CREDENTIALS` or gcloud auth configured
- Python 3.11 is pinned — use `uv python install 3.11` if needed
