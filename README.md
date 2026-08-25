# Used Car Analyser

Exploratory analysis and data enrichment pipeline for vehicle pricing datasets.

## Overview

This project explores vehicle pricing patterns in the US used car market using **3,973 Carmax listings** enriched with engineering specifications via LLM-assisted data enrichment.

## Analysis Summary

A companion notebook (`notebooks/car_data_analysis.ipynb`) answers the question: **what makes a used car a good buy?**

### Key Findings

- **Engineering specs dominate pricing:** SHAP analysis of an XGBoost model (R² = 0.973, RMSE = $2,424) shows **torque** is the #1 price predictor, followed by **mileage**, **year**, **horsepower**, and **acceleration**. What a car *does* matters more than its brand.
- **Brand effects are secondary:** `make` and `model` features rank below reliability ratings and engineering specs. The "badge premium" exists but is smaller than commonly assumed.
- **Depreciation:** A 50,000-mile increase correlates with roughly **30% lower price** (OLS log-linear estimate).
- **Best value identification:** Pareto frontier filtering reduced 3,973 listings to 61 non-dominated options. TOPSIS multi-criteria ranking identified **Ford Mustang**, **Dodge Charger**, and **Toyota Highlander** as top value picks under $35k.

### XGBoost Model

An **XGBRegressor** (300 estimators, max depth 6) was trained to predict Carmax listing prices. Key details:

| Metric | Value |
|--------|-------|
| R² (test) | 0.973 |
| RMSE (test) | $2,424 |

**Top SHAP feature importances:**

1. **Torque** — the single strongest predictor of price
2. **Mileage** — strong negative effect (more miles → lower price)
3. **Year** — older cars priced lower
4. **Horsepower** — positive correlation with price
5. **Acceleration** — faster acceleration → higher price

**Why the high R²?** The model leverages both engineering specs and brand/model identity. Torque, mileage, and year alone explain most of the variance, but adding make/model captures residual brand premiums that specs miss.

**Caveats:**
- The model is reliable for **known** makes and models. Pricing **new or rare trims** it hasn't seen will be less accurate.
- The OLS mileage model (Durbin-Watson = 0.234) has severe autocorrelation — it's a rough elasticity estimate, not a rigorous statistical model.

> The analysis was originally built to help a friend find the best value used car. Results are specific to the Carmax USA dataset and should not be generalised to other markets.

## Tech Stack

| Category | Tools |
|----------|-------|
| Language | Python 3.11 |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Data Processing | pandas, pydantic |
| ML / Modelling | xgboost, shap, scikit-learn |
| Statistics | statsmodels, seaborn |
| LLM | LM Studio (local inference) |
| IDE | VS Code |

## Setup

```bash
# Install dependencies
uv sync
```

## Project Structure

```
.
├── notebooks/
│   └── car_data_analysis.ipynb   # Full analysis: EDA, XGBoost, SHAP, Pareto, TOPSIS
├── src/
│   ├── llm_enrichment.py         # LLM-assisted data enrichment
│   ├── join_llm_data.py          # Merge enriched datasets
│   ├── add_hash.py               # Record deduplication utilities
│   ├── carmax_scraper_jsonld.ipynb   # [archived] legacy data collection
│   └── Carmax USA.R              # [archived] legacy data collection
├── data/
│   ├── carmax_USA.csv            # Raw listings data (git-tracked)
│   ├── carmax_usa_enriched.csv   # Final merged dataset
│   ├── carmax_specifications.csv # Enriched vehicle specifications
│   ├── carmax_telemetry.csv      # Model call metrics
│   └── carmax_USA copy.csv       # Backup copy
├── pyproject.toml                # Dependencies and project metadata
├── uv.lock                       # Locked dependency versions
├── .python-version               # Python version pin (3.11)
└── .gitignore                    # Git ignore rules
```

## Usage

### Analysis

Open the analysis notebook for exploratory data analysis, modelling, and visualisation:

```bash
uv run jupyter notebook notebooks/car_data_analysis.ipynb
```

### Data Enrichment

```bash
uv run python src/llm_enrichment.py
```

Outputs:
- `data/carmax_specifications.csv` — enriched vehicle specifications
- `carmax_errors.csv` — enrichment failure log
- `data/carmax_telemetry.csv` — model call metrics

```bash
uv run python src/join_llm_data.py
```

Outputs:
- `data/carmax_usa_enriched.csv` — merged dataset

## Data Files

| File | Description | In Git? |
|------|-------------|---------|
| `data/carmax_USA.csv` | Vehicle listings dataset | ✅ (tracked) |
| `data/carmax_specifications.csv` | Enriched specs | ❌ (large) |
| `data/carmax_telemetry.csv` | Model call logs | ❌ (large) |
| `data/carmax_usa_enriched.csv` | Final merged dataset | ❌ (large) |

Large CSV files are excluded from git. Run the enrichment pipeline to regenerate.

## Notes

- LLM enrichment requires LM Studio running locally
- Python 3.11 is pinned — use `uv python install 3.11` if needed