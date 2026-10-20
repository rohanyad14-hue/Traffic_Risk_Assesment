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

## 📐 Mathematical Formulation (Slide 8 & 9)

### 1. Annual Road Exposure ($E$)
$$\text{exposure\_mvkm} = \frac{\text{AADT} \times \text{length\_km} \times 365}{1,000,000}$$
Where:
- $\text{AADT}$: Annual Average Daily Traffic (vehicles/day)
- $\text{length\_km}$: Segment length in kilometers
- $\text{exposure\_mvkm}$: Million Vehicle-Kilometers per year

### 2. Severity Weighting ($W$)
Based on UK Department for Transport (DfT) / IRC economic injury ratios:
- $\text{Fatal} = 50$
- $\text{Serious} = 10$
- $\text{Slight} = 1$

$$\text{severity\_wt\_sum} = \sum_{i=1}^{N} w_i$$

### 3. Exposure-Adjusted Risk Index ($R$)
$$\text{risk\_per\_mvkm} = \frac{\text{severity\_wt\_sum}}{\text{exposure\_mvkm}}$$

### 4. Suppression Threshold
Segments with $< 3$ crashes or $< 0.20$ MVKM exposure are withheld/flagged to avoid near-zero denominator statistical noise.

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

## 🚀 How to Run the Prototype

### 1. Run the Data Pipeline (Batch Generation & Pre-aggregation)
From the project folder:
```powershell
python run_pipeline.py
```
*Execution takes ~5 seconds and compiles all DuckDB tables, Parquet cubes, and GeoJSON features.*

### 2. Launch the Interactive Dashboard
```powershell
streamlit run app.py
```
*Opens automatically at `http://localhost:8501`.*

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
