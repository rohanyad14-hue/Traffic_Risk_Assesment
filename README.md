# Traffic Accident Analysis & Visualization
**Visual Analytics Lab — Review 1 Prototype**  
**Authors:** Saranya Dalal [26MML0007], Divya Pujari [26MML0009], Rohan Yadav [26MML0020]  
**Faculty Guide:** Dr. Manikandan K (SCOPE)

---

## 🎯 Executive Overview & Research Problem
Traffic accidents result from interacting temporal, environmental, and spatial factors. Traditional accident analyses focus predominantly on **raw frequency (counts)**. However, frequency-based models significantly misrepresent true hazard levels:
- High-volume corridors (motorways, urban interchanges) register high incident counts consisting mostly of minor low-speed shunts, appearing deceptively dangerous.
- Low-volume rural or unlit curves register few total crashes, but produce catastrophic, fatal outcomes.

> **Central Claim (Slide 9):**  
> *"One-eighth the crashes. Twelve times the risk. Low frequency masks high severity."*

This prototype delivers an end-to-end, reproducible data pipeline and an interactive visual analytics dashboard that computes **exposure-adjusted severity risk** using published injury-cost weights.

---

## 🌐 Data Sources & Direct Download Links

The pipeline operates on **100% empirical, official government datasets** from the UK Department for Transport (DfT) and Bengaluru Traffic Police (BTP), supplemented by Open-Meteo and OpenStreetMap:

| Dataset | Provider / Source | Format & Coverage | Direct Link / Download |
| :--- | :--- | :--- | :--- |
| **UK Road Safety Collisions (2022)** | UK Department for Transport (DfT) | CSV (105k+ crash events across Great Britain) | 🔗 [Download Collisions 2022 CSV](https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-collision-2022.csv)<br>📄 [data.gov.uk Portal](https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data) |
| **UK Road Safety Vehicles (2022)** | UK Department for Transport (DfT) | CSV (198k+ vehicle & casualty link records) | 🔗 [Download Vehicles 2022 CSV](https://data.dft.gov.uk/road-accidents-safety-data/dft-road-casualty-statistics-vehicle-2022.csv)<br>📄 [data.gov.uk Portal](https://www.data.gov.uk/dataset/cb7ae6f0-4be6-4935-9277-47e5ce24a11f/road-safety-data) |
| **UK National Traffic Counts (AADF)** | UK DfT Road Traffic Statistics | ZIP / CSV (22,000+ national count points with AADT & segment lengths) | 🔗 [Download AADF ZIP Archive](https://storage.googleapis.com/dft-statistics/road-traffic/downloads/data-gov-uk/dft_traffic_counts_aadf.zip)<br>📄 [DfT Traffic Downloads Portal](https://roadtraffic.dft.gov.uk/downloads) |
| **Bengaluru Traffic Police Crash Statistics** | Bengaluru Traffic Police (BTP) & Karnataka Open Data | CSV (Station-wise fatal & non-fatal collision records 2020–2024) | 🔗 [BTP Official Portal](https://btp.gov.in/)<br>📄 [Open City Karnataka Road Safety Portal](https://opencity.in/tag/bengaluru-traffic-police/) |
| **Historical Weather Data** | Open-Meteo Archive API | Hourly REST / JSON (Precipitation, visibility, wind speed, surface temp) | 🔗 [Open-Meteo Weather API](https://open-meteo.com/en/docs/historical-weather-api) |
| **Road Network Hierarchy & Geometry** | OpenStreetMap (OSM) / Ordnance Survey | Vector / GeoJSON (Classifications, lane counts, speed limits) | 🔗 [OSM Highway Standards](https://wiki.openstreetmap.org/wiki/Key:highway) |

### Documentation & Guidance References
- [UK DfT Road Safety Statistics Guidance & Methodology](https://www.gov.uk/government/collections/road-accidents-and-safety-statistics)
- [UK DfT Traffic Counts Documentation & AADF Methodology](https://roadtraffic.dft.gov.uk/about)
- [IRC & DfT Economic Valuation of Road Accidents / Valuation Ratios](https://www.gov.uk/government/publications/reported-road-casualties-great-britain-annual-report-2022/reported-road-casualties-great-britain-2022-overview)

---

## 📐 Mathematical Formulation (Slide 8 & 9)

### 1. Annual Road Exposure ($E$)
$$\text{exposure\_mvkm} = \frac{\text{AADT} \times \text{length\_km} \times 365}{1,000,000}$$
Where:
- $\text{AADT}$: Annual Average Daily Traffic (vehicles/day from DfT AADF counts)
- $\text{length\_km}$: Segment link length in kilometers
- $\text{exposure\_mvkm}$: Million Vehicle-Kilometers per year

### 2. Severity Weighting ($W$)
Based on UK Department for Transport (DfT) / IRC economic injury valuation ratios:
- $\text{Fatal} = 50$
- $\text{Serious} = 10$
- $\text{Slight} = 1$

$$\text{severity\_wt\_sum} = \sum_{i=1}^{N} w_i$$

### 3. Exposure-Adjusted Risk Index ($R$)
$$\text{risk\_per\_mvkm} = \frac{\text{severity\_wt\_sum}}{\text{exposure\_mvkm}}$$

### 4. Suppression Threshold
Segments with $< 3$ crashes or $< 0.20$ MVKM exposure are withheld or flagged to prevent statistical noise from near-zero denominators.

---

## 🔬 Benchmark Case Study Validation (Slide 9)

| Segment ID | Road Description | Crash Count ($N$) | Severity Sum | Exposure (MVKM) | Exposure Risk ($R$) | Raw Count Rank | Exposure Risk Rank | Interpretation |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **SEG-0417** | M25 Orbital Interchange | **47** | 186 | **27.1** | **6.86** | #142 (Looks High Risk) | #152 (Ranks Very Safe) | High count, high traffic; low-speed shunts |
| **SEG-1902** | B4009 Chiltern Ridge Curve | **6** | 211 | **2.5** | **84.4** | #159 (Neglected & Hidden) | **#2 (Deadly Trap!)** | **1/8th the crashes, 12x the risk!** |

---

## 🏗️ Pipeline Architecture (Slide 10)

```
[01 Ingest]       -> Python + requests: UK STATS19 records, OSM road segments, AADT volumes, Open-Meteo
        │
[02 Preprocess]   -> Geocoding validation, quality imputation flags, temporal features (24h circadian)
        │
[03 Features]     -> DfT severity weights (Fatal=50, Serious=10, Slight=1), weather hostility index
        │
[04 Exposure]     -> Grain shift to Road Segment: computes exposure_mvkm, risk_per_mvkm, 4-quadrants
        │
[05 Cubes]        -> DuckDB columnar SQL engine pre-aggregates cubes (Parquet + GeoJSON)
        │
[06 Dashboard]    -> Streamlit (app.py) + PyDeck 3D + Plotly: sub-second interactive slicing
```

---

## 📁 Repository Directory Structure

```text
TrafficAccidentAnalysis/
├── .gitignore                   # Ignores large raw CSV/ZIP files, DuckDB tables, and caches
├── README.md                    # Project documentation & data catalog links
├── requirements.txt             # Python dependencies (Streamlit, DuckDB, PyDeck, Plotly)
├── run_pipeline.py              # Master pipeline orchestrator (CLI)
├── app.py                       # Interactive Streamlit Visual Analytics Dashboard
├── run.bat / run.sh             # One-click startup scripts (Windows / Linux)
├── pipeline/
│   ├── download_real_data.py    # Automated downloader for official UK DfT datasets
│   ├── ingest_real_data.py      # Real DfT STATS19 & BTP ingestion & conformation
│   ├── 01_data_generation_and_ingest.py  # Synthetic benchmark mode generator
│   ├── 02_preprocessing_and_features.py  # Cleansing, circadian slots & severity weights
│   ├── 03_exposure_and_risk_modeling.py  # Exposure calculation & 4-quadrant classification
│   └── 04_aggregate_cubes_duckdb.py      # DuckDB analytical cube pre-aggregation
├── data/
│   ├── real_raw/                # Downloaded raw CSV/ZIP datasets (auto-populated or manual)
│   │   ├── btp_*_station_wise.csv        # Bengaluru Traffic Police station crash stats
│   │   ├── dft_collisions_2022.csv       # (Ignored from git, auto-downloaded)
│   │   ├── dft_vehicles_2022.csv         # (Ignored from git, auto-downloaded)
│   │   └── dft_traffic_counts_aadf.csv   # (Ignored from git, auto-downloaded)
│   ├── raw/                     # Immutable conformed parquet tables
│   ├── processed/               # Cleaned crash & segment tables with exposure metrics
│   ├── cubes/                   # Pre-aggregated DuckDB parquet cubes & GeoJSON
│   └── traffic_analytics.duckdb # DuckDB analytical database
├── powerbi/                     # Power BI Desktop PBIP report project
│   ├── TrafficAccidentAnalysis.pbip
│   └── build_powerbi_report.py  # Power BI report generator
├── report/                      # Presentation slides, talking points & technical reports
└── report_figures/              # Publication figures and charts
```

---

## 🚀 How to Run the Pipeline & Dashboard

### 1. Installation & Environment Setup
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Download Data & Execute the Pipeline
The pipeline features an automated downloader. On first run, it fetches the official UK DfT datasets if they are not already present in `data/real_raw/`:
```powershell
python run_pipeline.py
```
*(Execution takes ~6.2 seconds and compiles all DuckDB tables, Parquet cubes, and GeoJSON features.)*

To download datasets separately:
```powershell
python pipeline/download_real_data.py
```

To run in synthetic benchmark prototype mode:
```powershell
python run_pipeline.py --synthetic
```

### 3. Launch the Streamlit Analytics Dashboard
```powershell
streamlit run app.py
```
*Opens automatically in your browser at `http://localhost:8501`.*

### 4. Open or Rebuild the Power BI Dashboard
Open [`powerbi/TrafficAccidentAnalysis.pbip`](file:///c:/Users/Rohan/Downloads/TrafficAccidentAnalysis/powerbi/TrafficAccidentAnalysis.pbip) in Power BI Desktop, or rebuild via:
```powershell
python powerbi/build_powerbi_report.py
```

---

## 📊 Dashboard Modules & Research Questions

1. **🎯 Core Contribution: Frequency vs. Severity Matrix**
   - Side-by-side verification of SEG-0417 vs SEG-1902.
   - Interactive 4-Quadrant Scatter Plot separating *Severe Congested* (Q1), *Deadly Traps* (Q2), *Safe Roads* (Q3), and *Fender-Benders* (Q4).
2. **⏰ WHEN? (Temporal & Circadian Patterns - RQ 1)**
   - 24-hour circadian dual-axis risk curve (Traffic volume vs. Fatality share %).
   - 168-cell Day-of-Week × Hour heatmap matrix.
3. **🗺️ WHERE? (Spatial 3D Risk Map - RQ 2)**
   - 3D geospatial road segment visualization with PyDeck / Mapbox.
   - Switchable layers: Raw Frequency Hotspots vs. Exposure-Adjusted Risk.
   - Leaderboard showing dramatic rank shifts ($\Delta$ rank jumps).
4. **🌧️ UNDER WHAT CONDITIONS? (Environmental Drivers - RQ 3)**
   - Severe outcome rates across rain, snow, fog, and unlit night conditions.
   - Vulnerable Road User (VRU) mortality across speed limits.
5. **🤖 ML Hotspot & Severity Simulator**
   - Feature importances from Random Forest classifier.
   - Real-time interactive "What-If" policy sandbox for roadway safety engineers.
6. **🇮🇳 India Transferability Case (Slide 7)**
   - Mixed-traffic evaluation on Bengaluru corridors (Outer Ring Road, Hosur Expressway, Kanakapura Highway).
   - Highlighting 55%+ two-wheeler modal share and FASTag structural volume proxies.
7. **⚙️ Pipeline Architecture & Review 1 Docs (Slide 6 & 10)**
   - Reproducible batch workflow explanation and CSV dataset export.

---

## 🔒 Version Control & Data Management (.gitignore)

The repository uses `.gitignore` to keep large binary datasets and dynamic caches out of version control while maintaining full reproducibility:
- **Ignored**: Large raw government files (`dft_*.csv`, `dft_*.zip`, ~190 MB), DuckDB binary stores (`*.duckdb`), pipeline cubes, and temporary HTML visualization dumps.
- **Tracked**: Full Python pipeline scripts, Streamlit frontend, Power BI TMDL/PBIR models, benchmark seed files (`btp_*_station_wise.csv`), and `.gitkeep` markers for directory scaffolding.
- Anyone cloning the repository can immediately reproduce all data cubes by running `python run_pipeline.py`.
