# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Commands for Development

## Run Scraping Script

```bash
Rscript "Carmax USA.R"
```

This will:
1. Launch Firefox browser via RSelenium
2. Scrape car listings from carmax.com
3. Upload data to Google BigQuery table `nas-autotrader-prd.cars.Carmax`

## Run Analysis

```bash
# Download data from BigQuery and run analysis
bq_table_download("nas-autotrader-prd.cars.Carmax")
Rscript "Carmax Analysis.Rmd"
```

## Verify Scraping Progress

```r
read.csv("carmax_USA.csv")
```

## Verify BigQuery Upload

```r
bq_table_exists("nas-autotrader-prd.cars.Carmax")
bq_table_download("nas-autotrader-prd.cars.Carmax")
```

## Check for Open Ports

```r
library(netstat)
netstat(-ano)
```

## Stop Java Process (for cleanup)

```bash
taskkill /im java.exe /f
```

## Check Chromedriver Versions

```r
binman::list_versions("chromedriver")
```

# Architecture Overview

## Data Flow

```
┌────────────────────────────────────────┐
│                    Used Car Analyser    │
├─────────────────┬───────────────────────┤
│  Scraping Script │  Data Processing     │
│  (Carmax USA.R)  │  ┌──────────────────┐│
│                  │  │ Extract Fields   ││
│                  │  │ year, make, model││
│                  │  │ trim, mileage,   ││
│                  │  │ price            ││
│                  │  └──────────────────┘│
│                  │  ┌──────────────────┐│
│                  │  │ Create Data Frame││
│                  │  │ with make_model  ││
│                  │  │ and gm flags     ││
│                  │  └──────────────────┘│
│                  │  ┌──────────────────┐│
│                  │  │ Transform & Clean││
│                  │  └──────────────────┘│
│                  │  ┌──────────────────┐│
│                  │  │ GM Tagging       ││
│                  │  └──────────────────┘│
│                  │         ▼           │
│                  │  ┌──────────────────┐│
│  ┌───────────────┤  │ BigQuery Upload  ││
│  │ Analysis      │  │ ┌──────────────┐││
│  │ .Rmd          │  │ │ nas-autotrader-│││
│  │               │  │ │ .cars         │││
│  │ - ggplotly plots       │││
│  │ - Mixed-effects models │││
│  │ - Price predictions    │││
│  └───────────────┤  └──────────────┘││
└──────────────────┴───────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `Carmax USA.R` | Primary scraping script using RSelenium; extracts year, make, model, trim, mileage, price; creates make_model composite key and GM boolean flag; uploads to BigQuery |
| `Carmax Analysis.Rmd` | R Markdown analysis notebook; downloads data from BigQuery; generates visualizations with ggplotly; fits mixed-effects models using lme4; produces price predictions |
| `carmax_USA.csv` | Local CSV output containing scraped car listings; intermediate file before BigQuery upload |

## Project Dependencies (R packages)

- **RSelenium** - Browser automation for web scraping (Firefox/Chrome)
- **tidyverse** - Data manipulation (dplyr, tidyr, etc.)
- **rvest** - HTML parsing
- **lme4** - Mixed-effects models for price prediction
- **bigquery** - Google BigQuery integration
- **plotly** - Interactive visualizations
- **wdman** - WebDriver manager
- **netstat** - Port detection
- **binman** - Browser version management

## BigQuery Configuration

- **Dataset**: `nas-autotrader-prd`
- **Tables**:
  - `cars.Carmax` - Main car listings table
  - `cars.SUV_Trims` - SUV trim reference data

## Model List

The scraping script maintains a hardcoded list of supported car models:

- **Trucks/SUVs**: Yukon XL 1500, Yukon, Tahoe, Suburban 1500, Escalade, Escalade ESV, 4Runner, Grand Highlander, Highlander, Land Cruiser, Sequoia
- **Luxury**: LX 570, LX 600, IS 500, LC 500, RC F, LS 460, LS 500
- **Muscle Cars**: Mustang, Challenger, Camaro
- **Ford Trucks**: F150, Silverado 1500, Expedition, Tundra, Maverick, Ranger
- **Chrysler/Stellantis**: Charger, Durango, Aviator, Navigator, Navigator L, Wagoneer, Grand Wagoneer, Expedition Max, Expedition EL, Expedition Max

## Scraping Workflow

1. **Browser Setup**: RSelenium launches Firefox (Chrome also supported) via wdman
2. **Navigation**: Opens carmax.com/cars/ URL with specific model filters
3. **Scrolling**: Automatically scrolls and clicks "see more" buttons to load all listings
4. **Element Extraction**:
   - `.scct--make-model-info--year-make` - Year and make
   - `.scct--make-model-info--model-trim` - Model and trim
   - `.scct--price-miles-info--price` - Price
   - `.scct--sr-only` - Mileage (screen reader text)
5. **Data Cleaning**: Removes special characters, converts to numeric
6. **Enrichment**: Creates composite keys (make_model, car_full) and GM flag
7. **Upload**: Appends data to BigQuery with WRITE_APPEND disposition

## Data Model Fields

| Field | Type | Description |
|-------|------|-------------|
| year | factor | Car model year |
| make | factor | Car manufacturer |
| model | factor | Car model name |
| trim | factor | Trim level |
| mileage | numeric | Vehicle mileage |
| price | numeric | Price in USD |
| platform | string | Source identifier ("carmax") |
| make_model | string | Composite key (make + model) |
| gm | boolean | TRUE if GM-affiliated brand |
| car | string | Full car name (make model trim) |
| car_full | string | Year make model trim |

## Mixed-Effects Model Specification

The analysis uses the following model:

```r
price ~ sqrt(mileage) + make + year + 
      (sqrt(mileage) | model) + 
      (sqrt(mileage) | trim) + 
      (year | model)
```

This model accounts for:
- Fixed effects: mileage (log/sqrt transformed), make, year
- Random effects: mileage influence varies by model and trim; year effects vary by model

## Notes

- Firefox browser required for RSelenium (Chrome also supported via chromedriver)
- Java must be installed (`taskkill /im java.exe /f` for cleanup)
- Driver management handled by RSelenium's `rsDriver()` function
- Data is appended to BigQuery on each run (check existing data before running)
- CSV output is created before BigQuery upload as intermediate storage
