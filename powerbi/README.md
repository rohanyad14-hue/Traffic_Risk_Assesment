# Power BI version of the dashboard

`TrafficAccidentAnalysis.pbip` is a Power BI Project with the same 7 sections as the Streamlit app:
Core (frequency vs severity), WHEN?, WHERE? (maps), UNDER WHAT CONDITIONS?, ML & what-if simulator,
India transferability case, and Pipeline architecture. The Study Context, road class and suppression
slicers are synced across pages, like the dashboard sidebar.

## Open it
1. Open `TrafficAccidentAnalysis.pbip` in Power BI Desktop (2026 release or later).
2. Click **Refresh** (or "Refresh now" on the yellow banner). Data loads from `powerbi/data/*.csv`.

If you move the project folder, go to **Transform data > Edit parameters** and set `DataFolder` to the
full path of the `data` folder, ending with a backslash. Then refresh.

## Rebuild after changing the pipeline
```powershell
python run_pipeline.py
python powerbi/build_powerbi_report.py   # close Power BI Desktop first
```
The builder exports the cubes to CSV, renders the two basemaps (Esri Dark Gray Canvas tiles) and writes
the TMDL model and PBIR report. Maps are scatter charts over those basemaps, so they need no Azure Maps setting.
