"""
Builds the Power BI version of the Streamlit dashboard as a Power BI Project (PBIP):
    powerbi/data/*.csv                         (tables exported from data/cubes)
    powerbi/TrafficAccidentAnalysis.SemanticModel   (TMDL: tables, relationships, DAX measures)
    powerbi/TrafficAccidentAnalysis.Report          (PBIR: 7 pages mirroring the dashboard tabs)
    powerbi/TrafficAccidentAnalysis.pbip            (open this in Power BI Desktop, then Refresh)

Run after the pipeline:   python powerbi/build_powerbi_report.py
Power BI Desktop must be closed while this runs (it rewrites the project folders).
"""

import io
import json
import math
import os
import shutil
import urllib.request
import uuid

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUBES = os.path.join(ROOT, "data", "cubes")
OUT = os.path.join(ROOT, "powerbi")
DATA = os.path.join(OUT, "data")
ASSETS = os.path.join(OUT, "assets")
NAME = "TrafficAccidentAnalysis"
REPORT = os.path.join(OUT, f"{NAME}.Report")
MODEL = os.path.join(OUT, f"{NAME}.SemanticModel")

UK = "UK STATS19 Network"
IN = "India Bengaluru Corridors"

SCHEMA = {
    "vc": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json",
    "page": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
    "pages": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "report": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.3.0/schema.json",
    "version": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "platform": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "pbir": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "pbism": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "pbip": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
}

# Dashboard palette (matches app.py)
C = {
    "page": "#0B1120", "card": "#131C31", "border": "#26324A", "alt": "#1E293B", "text": "#F1F5F9",
    "text2": "#94A3B8", "grid": "#1E293B", "sky": "#38BDF8", "indigo": "#818CF8", "rose": "#F43F5E",
    "green": "#10B981", "orange": "#F97316", "slate": "#64748B", "purple": "#C084FC",
}
QUAD_COLOURS = {
    "Q1: High Frequency - High Severity (Severe Congested)": "#F97316",
    "Q2: Low Frequency - High Severity (Deadly Trap - Primary Focus)": "#F43F5E",
    "Q3: Low Frequency - Low Severity (Safe Segment)": "#10B981",
    "Q4: High Frequency - Low Severity (Fender-Benders)": "#38BDF8",
    "Suppressed (Low Sample Noise)": "#64748B",
}
FONT, FONT_B = "Segoe UI", "Segoe UI Semibold"


def new_id():
    return str(uuid.uuid4())


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


# =============================================================================
# 1. DATA EXPORT
# =============================================================================
def benchmark_ids(df, ctx):
    """Same benchmark pair the Streamlit app shows for each study context."""
    if ctx == UK:
        return "SEG-0417", "SEG-1902"
    safe = df.sort_values(["rank_shift", "crash_n"], ascending=[True, False]).iloc[0]["segment_id"]
    trap = df.sort_values(["rank_shift", "risk_per_mvkm"], ascending=[False, False]).iloc[0]["segment_id"]
    return safe, trap


def export_segments(df, ctx):
    safe, trap = benchmark_ids(df, ctx)
    out = pd.DataFrame({
        "Study Context": ctx,
        "Segment ID": df["segment_id"],
        "Road Name": df["road_name"],
        "Road Class": df["road_class"],
        # nullable types so the CSV holds "70" (not "70.0") and blanks where a context lacks the field
        "Speed Limit (mph)": (df["speed_limit_mph"] if "speed_limit_mph" in df else pd.Series(pd.NA, index=df.index)).astype("Int64"),
        "Length km": df["length_km"],
        "AADT": df["aadt"],
        "Two-Wheeler Share": (df["two_wheeler_pct"] if "two_wheeler_pct" in df else pd.Series(np.nan, index=df.index)).astype(float),
        "Lighting": df["lighting_quality"] if "lighting_quality" in df else "Not recorded",
        "Curvature Risk": df["curvature_risk"] if "curvature_risk" in df else "Not recorded",
        "Mid Lat": ((df["start_lat"] + df["end_lat"]) / 2).round(6),
        "Mid Lon": ((df["start_lon"] + df["end_lon"]) / 2).round(6),
        "Crashes": df["crash_n"].astype(int),
        "Severity Weight Sum": df["severity_wt_sum"].astype(int),
        "Fatal": df["fatal_count"].astype(int),
        "Serious": df["serious_count"].astype(int),
        "Slight": df["slight_count"].astype(int),
        "Night Crashes": df["night_crash_count"].astype(int),
        "VRU Crashes": df["vulnerable_user_crash_count"].astype(int),
        "Exposure MVKM": df["exposure_mvkm"],
        "Risk per MVKM": df["risk_per_mvkm"],
        "Suppression": np.where(df["is_suppressed"], "Suppressed (low sample)", "Reported"),
        "Raw Count Rank": df["rank_raw_count"].astype(int),
        "Exposure Risk Rank": df["rank_exposure_risk"].astype(int),
        "Rank Shift": df["rank_shift"].astype(int),
        "Quadrant": df["quadrant"],
        "Is Benchmark": df["segment_id"].isin([safe, trap]).astype(int),
        "Benchmark Role": np.select(
            [df["segment_id"] == safe, df["segment_id"] == trap],
            ["High count, ranks safe", "Hidden high risk"], default="Other"),
    })
    out["Map Y"] = out["Mid Lat"].map(merc_y).round(8)
    return out


def export_data():
    os.makedirs(DATA, exist_ok=True)
    rd = lambda f: pd.read_parquet(os.path.join(CUBES, f))
    uk_segs, in_segs = rd("cube_segments_spatial.parquet"), rd("cube_india_segments_spatial.parquet")

    tables = {}
    tables["StudyContext"] = pd.DataFrame({"Study Context": [UK, IN], "Context Order": [1, 2]})
    tables["Segments"] = pd.concat([export_segments(uk_segs, UK), export_segments(in_segs, IN)], ignore_index=True)

    hourly = []
    for ctx, f in [(UK, "cube_circadian_hourly.parquet"), (IN, "cube_india_circadian_hourly.parquet")]:
        d = rd(f)
        hourly.append(pd.DataFrame({
            "Study Context": ctx, "Hour": d["hour"].astype(int), "Crashes": d["crash_count"].astype(int),
            "Fatal": d["fatal_count"].astype(int), "Serious": d["serious_count"].astype(int),
            "VRU Crashes": (d["vulnerable_pct"] * d["crash_count"] / 100).round().astype(int),
            "Mean Severity Weight": d["mean_severity_wt"],
        }))
    tables["Hourly"] = pd.concat(hourly, ignore_index=True)

    heat = []
    for ctx, f in [(UK, "cube_temporal_heatmap.parquet"), (IN, "cube_india_temporal_heatmap.parquet")]:
        d = rd(f)
        heat.append(pd.DataFrame({
            "Study Context": ctx, "Day": d["day_of_week"], "Day Order": d["dow_num"].astype(int) + 1,
            "Hour": d["hour"].astype(int), "Crashes": d["total_crashes"].astype(int),
            "Fatal": d["fatal_crashes"].astype(int), "Serious": d["serious_crashes"].astype(int),
            "Slight": d["slight_crashes"].astype(int), "Avg Severity Weight": d["avg_severity_weight"],
        }))
    tables["Heatmap"] = pd.concat(heat, ignore_index=True)

    env = rd("cube_environmental_matrix.parquet")
    tables["Environment"] = pd.DataFrame({
        "Study Context": UK, "Weather": env["weather_condition"], "Road Surface": env["road_surface_condition"],
        "Lighting Condition": env["light_condition"], "Crashes": env["crash_volume"].astype(int),
        "Fatal": env["fatal_count"].astype(int), "Serious": env["serious_count"].astype(int),
        "Mean Severity Weight": env["mean_severity_wt"],
    })

    vu, vi = rd("cube_vehicle_vulnerability.parquet"), rd("cube_india_vehicle_vulnerability.parquet")
    class_order = {c: i for i, c in enumerate(sorted(vi["road_class"].unique()), start=101)}
    tables["Vehicle"] = pd.concat([
        pd.DataFrame({"Study Context": UK, "Vehicle Mode": vu["primary_vehicle"],
                      "Speed Limit or Corridor": vu["speed_limit_mph"].astype(int).astype(str) + " mph",
                      "Group Order": vu["speed_limit_mph"].astype(int), "Crashes": vu["crash_count"].astype(int),
                      "Fatal": vu["fatal_count"].astype(int), "Serious": vu["serious_count"].astype(int)}),
        pd.DataFrame({"Study Context": IN, "Vehicle Mode": vi["primary_vehicle"],
                      "Speed Limit or Corridor": vi["road_class"], "Group Order": vi["road_class"].map(class_order),
                      "Crashes": vi["crash_count"].astype(int), "Fatal": vi["fatal_count"].astype(int),
                      "Serious": vi["serious_count"].astype(int)}),
    ], ignore_index=True)

    with open(os.path.join(CUBES, "cube_ml_risk_weights.json")) as f:
        ml = json.load(f)
    tables["Features"] = pd.DataFrame({
        "Feature": [k.replace("_", " ").title().replace("Aadt", "AADT").replace("Mph", "(mph)")
                    for k in ml["feature_importances"]],
        "Importance": list(ml["feature_importances"].values()),
    })

    # What-if simulator option tables (same inputs and defaults as the Streamlit simulator)
    tables["SimSpeed"] = pd.DataFrame({"Speed Limit (mph)": [20, 30, 40, 50, 60, 70]})
    tables["SimTime"] = pd.DataFrame({"Time of Day": ["Daylight", "Dark Night"], "Time Order": [1, 2]})
    tables["SimLighting"] = pd.DataFrame({"Lighting Infrastructure": ["Lit by Streetlights", "Unlit (Zero Lighting)"], "Lighting Order": [1, 2]})
    tables["SimWeather"] = pd.DataFrame({"Weather Condition": ["Clear / Fine", "Heavy Rain / Storm", "Dense Fog / Ice"], "Weather Order": [1, 2, 3]})
    tables["SimRoadUser"] = pd.DataFrame({"Road User": ["Vulnerable (Motorcycle / Bicycle)", "Car / Other Vehicle"], "Road User Order": [1, 2]})

    for name, df in tables.items():
        df.to_csv(os.path.join(DATA, f"{name}.csv"), index=False, encoding="utf-8")
    print(f"data: {len(tables)} CSV tables -> {DATA}")
    return tables, uk_segs, in_segs


# =============================================================================
# 2. BASEMAPS (scatter-chart maps work offline and need no Azure Maps tenant setting)
# =============================================================================
def build_basemap(segs, fname, width_px, height_px):
    lats = pd.concat([segs["start_lat"], segs["end_lat"]])
    lons = pd.concat([segs["start_lon"], segs["end_lon"]])
    pad_lon = (lons.max() - lons.min()) * 0.06 + 0.01
    pad_lat = (lats.max() - lats.min()) * 0.06 + 0.01
    lon0, lon1 = lons.min() - pad_lon, lons.max() + pad_lon
    my0, my1 = merc_y(lats.min() - pad_lat), merc_y(lats.max() + pad_lat)
    aspect = width_px / height_px
    w, h = math.radians(lon1 - lon0), my1 - my0
    if w / h < aspect:
        d = (aspect * h - w) / 2
        lon0, lon1 = lon0 - math.degrees(d), lon1 + math.degrees(d)
    else:
        d = (w / aspect - h) / 2
        my0, my1 = my0 - d, my1 + d

    zoom = int(np.clip(math.ceil(math.log2(width_px * 360 / (256 * (lon1 - lon0)))), 3, 15))
    n = 2 ** zoom
    px = lambda lon: (lon + 180) / 360 * n * 256
    py = lambda my: (1 - my / math.pi) / 2 * n * 256
    x0, x1, y0, y1 = px(lon0), px(lon1), py(my1), py(my0)
    tx0, tx1, ty0, ty1 = int(x0 // 256), int(x1 // 256), int(y0 // 256), int(y1 // 256)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256), (11, 17, 32))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{zoom}/{ty}/{tx}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "TrafficAccidentAnalysis-PowerBI-builder"})
                tile = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
                canvas.paste(tile, ((tx - tx0) * 256, (ty - ty0) * 256))
            except Exception as exc:  # keep going; a missing tile just stays dark
                print("  tile failed", url, exc)
    img = canvas.crop((round(x0 - tx0 * 256), round(y0 - ty0 * 256), round(x1 - tx0 * 256), round(y1 - ty0 * 256)))
    img = img.resize((width_px, height_px), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = Image.blend(img, Image.new("RGB", img.size, (11, 17, 32)), 0.35)  # tint towards the report navy

    # Draw every road segment as a thin line; the scatter dots (coloured by quadrant) sit on the midpoints.
    draw = ImageDraw.Draw(img)
    to_xy = lambda lon, lat: ((lon - lon0) / (lon1 - lon0) * width_px, (my1 - merc_y(lat)) / (my1 - my0) * height_px)
    for _, s in segs.iterrows():
        draw.line([to_xy(s["start_lon"], s["start_lat"]), to_xy(s["end_lon"], s["end_lat"])],
                  fill=(186, 198, 216), width=3)
    os.makedirs(ASSETS, exist_ok=True)
    img.save(os.path.join(ASSETS, fname), optimize=True)
    return {"lon_min": lon0, "lon_max": lon1, "y_min": my0, "y_max": my1}


# =============================================================================
# 3. SEMANTIC MODEL (TMDL)
# =============================================================================
M_TABLE = "_Measures"
SORT_BY = {
    ("StudyContext", "Study Context"): "Context Order",
    ("Heatmap", "Day"): "Day Order",
    ("Vehicle", "Speed Limit or Corridor"): "Group Order",
    ("SimTime", "Time of Day"): "Time Order",
    ("SimLighting", "Lighting Infrastructure"): "Lighting Order",
    ("SimWeather", "Weather Condition"): "Weather Order",
    ("SimRoadUser", "Road User"): "Road User Order",
}
HIDDEN = {"Context Order", "Day Order", "Group Order", "Time Order", "Lighting Order", "Weather Order",
          "Road User Order", "Map Y", "Is Benchmark"}
FORMATS = {"Two-Wheeler Share": "0%", "Risk per MVKM": "0.00", "Exposure MVKM": "#,0.00", "Length km": "0.000",
           "Mid Lat": "0.0000", "Mid Lon": "0.0000", "Importance": "0.0000", "Rank Shift": "+#,0;-#,0;0",
           "Speed Limit (mph)": "0", "Hour": "0"}


def tq(name):
    """Quote a TMDL object name when it has characters outside [A-Za-z0-9_]."""
    return f"'{name}'" if not all(ch.isalnum() or ch == "_" for ch in name) else name


def col_kind(series):
    if pd.api.types.is_integer_dtype(series):
        return "int64"
    if pd.api.types.is_float_dtype(series):
        return "double"
    return "string"


def table_tmdl(name, df):
    L = [f"table {name}", f"\tlineageTag: {new_id()}", ""]
    mtypes = []
    for c in df.columns:
        kind = col_kind(df[c])
        L += [f"\tcolumn {tq(c)}", f"\t\tdataType: {kind}"]
        if c in HIDDEN:
            L.append("\t\tisHidden")
        if c in FORMATS:
            L.append(f"\t\tformatString: {FORMATS[c]}")
        elif kind == "int64":
            L.append("\t\tformatString: #,0")
        L += [f"\t\tlineageTag: {new_id()}", "\t\tsummarizeBy: none"]
        if (name, c) in SORT_BY:
            L.append(f"\t\tsortByColumn: {tq(SORT_BY[(name, c)])}")
        L += [f"\t\tsourceColumn: {c}", "", "\t\tannotation SummarizationSetBy = User", ""]
        mtypes.append('{"%s", %s}' % (c, {"int64": "Int64.Type", "double": "type number", "string": "type text"}[kind]))
    L += [
        f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
        f'\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "{name}.csv"),[Delimiter=",", Columns={len(df.columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\t\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f'\t\t\t\t    Typed = Table.TransformColumnTypes(Headers,{{{", ".join(mtypes)}}}, "en-US")',
        "\t\t\t\tin", "\t\t\t\t    Typed", "", "\tannotation PBI_ResultType = Table", "",
    ]
    return "\n".join(L)


MEASURES = []


def M(name, dax, fmt="", folder="Segments"):
    MEASURES.append((name, dax, fmt, folder))


def define_measures():
    seg_filters = "REMOVEFILTERS(Segments[Road Class]), REMOVEFILTERS(Segments[Suppression])"
    # --- Core KPIs (segment grain)
    M("Total Crashes", "SUM(Segments[Crashes])", "#,0")
    M("Network Exposure (MVKM)", "SUM(Segments[Exposure MVKM])", "#,0.0")
    M("Lethal Trap Segments", 'COALESCE(CALCULATE(COUNTROWS(Segments), LEFT(Segments[Quadrant], 2) = "Q2"), 0)', "#,0")
    M("Total Fatalities", "SUM(Segments[Fatal])", "#,0")
    M("Total Serious Injuries", "SUM(Segments[Serious])", "#,0")
    M("Mean Exposure Risk", "AVERAGE(Segments[Risk per MVKM])", "0.0")
    M("Segment Count", "COUNTROWS(Segments)", "#,0")
    M("Fatality Share %", "DIVIDE([Total Fatalities], [Total Crashes])", "0.0%")
    M("Mean Exposure per Segment", "AVERAGE(Segments[Exposure MVKM])", "#,0.00")
    M("Raw Incidents", "SUM(Hourly[Crashes])", "#,0", "Temporal")
    M("Raw Incidents Label", 'FORMAT([Raw Incidents], "#,0") & " raw incidents"', "", "Labels")
    M("Exposure Label", '"Million vehicle-km (MVKM)"', "", "Labels")
    M("Trap Label", '"Low count, severe risk"', "", "Labels")
    M("Fatal Label", '"Weight: 50x per DfT"', "", "Labels")
    M("Risk Label", '"Severity weight / MVKM"', "", "Labels")
    M("Raw Rank", "MIN(Segments[Raw Count Rank])", "#,0")
    M("Risk Rank", "MIN(Segments[Exposure Risk Rank])", "#,0")
    M("Rank Shift", "SUM(Segments[Rank Shift])", "+#,0;-#,0;0")
    # --- Benchmark pair (unaffected by road-class / suppression filters, like the dashboard cards)
    bench = lambda expr: f"IF(MAX(Segments[Is Benchmark]) = 1, CALCULATE({expr}, {seg_filters}))"
    M("Bench Crashes", bench("[Total Crashes]"), "#,0", "Benchmark")
    M("Bench Raw Rank", bench("[Raw Rank]"), "#,0", "Benchmark")
    M("Bench Exposure", bench("[Network Exposure (MVKM)]"), "#,0.00", "Benchmark")
    M("Bench Risk", bench("[Mean Exposure Risk]"), "0.00", "Benchmark")
    M("Bench Risk Rank", bench("[Risk Rank]"), "#,0", "Benchmark")
    M("Bench AADT", bench("SUM(Segments[AADT])"), "#,0", "Benchmark")
    M("Benchmark Headline",
      "VAR tc = CALCULATE([Total Crashes], Segments[Benchmark Role] = \"Hidden high risk\", " + seg_filters + ") "
      "VAR sc = CALCULATE([Total Crashes], Segments[Benchmark Role] = \"High count, ranks safe\", " + seg_filters + ") "
      "VAR tr = CALCULATE([Mean Exposure Risk], Segments[Benchmark Role] = \"Hidden high risk\", " + seg_filters + ") "
      "VAR sr = CALCULATE([Mean Exposure Risk], Segments[Benchmark Role] = \"High count, ranks safe\", " + seg_filters + ") "
      "RETURN IF(HASONEVALUE('StudyContext'[Study Context]), "
      "FORMAT(DIVIDE(tc, sc), \"0.00\") & \"x the crashes  ·  \" & FORMAT(DIVIDE(tr, sr), \"0.0\") & \"x the risk\", "
      "\"Select one study context\")", "", "Benchmark")
    # --- Temporal
    M("Hourly Crashes", "SUM(Hourly[Crashes])", "#,0", "Temporal")
    M("Hourly Fatality Rate", "DIVIDE(SUM(Hourly[Fatal]), SUM(Hourly[Crashes]))", "0.0%", "Temporal")
    M("Night Fatality Rate", "CALCULATE([Hourly Fatality Rate], Hourly[Hour] < 6 || Hourly[Hour] > 19)", "0.0%", "Temporal")
    M("Day Fatality Rate", "CALCULATE([Hourly Fatality Rate], Hourly[Hour] >= 6 && Hourly[Hour] <= 19)", "0.0%", "Temporal")
    M("Night vs Day Label", '"vs " & FORMAT([Day Fatality Rate], "0.0%") & " by day (06:00-19:59)"', "", "Labels")
    M("Peak Volume Hour", 'VAR t = TOPN(1, VALUES(Hourly[Hour]), [Hourly Crashes], DESC) RETURN FORMAT(MAXX(t, Hourly[Hour]), "00") & ":00"', "", "Temporal")
    M("Peak Volume Label", 'VAR t = TOPN(1, VALUES(Hourly[Hour]), [Hourly Crashes], DESC) RETURN FORMAT(MAXX(t, [Hourly Crashes]), "#,0") & " crashes in that hour"', "", "Labels")
    M("Most Lethal Hour", 'VAR t = TOPN(1, VALUES(Hourly[Hour]), [Hourly Fatality Rate], DESC) RETURN FORMAT(MAXX(t, Hourly[Hour]), "00") & ":00"', "", "Temporal")
    M("Most Lethal Label", 'VAR t = TOPN(1, VALUES(Hourly[Hour]), [Hourly Fatality Rate], DESC) RETURN "fatality share " & FORMAT(MAXX(t, [Hourly Fatality Rate]), "0.0%")', "", "Labels")
    M("VRU Share", "DIVIDE(SUM(Hourly[VRU Crashes]), SUM(Hourly[Crashes]))", "0%", "Temporal")
    M("VRU Label", '"two-wheelers, cyclists & pedestrians"', "", "Labels")
    M("Severe Outcome Rate", "DIVIDE(SUM(Heatmap[Fatal]) + SUM(Heatmap[Serious]), SUM(Heatmap[Crashes]))", "0%", "Temporal")
    M("Heatmap Colour",
      "VAR v = [Severe Outcome Rate] "
      "VAR hmGrid = ALLSELECTED(Heatmap[Day], Heatmap[Day Order], Heatmap[Hour]) "
      "VAR mn = MINX(hmGrid, [Severe Outcome Rate]) VAR mx = MAXX(hmGrid, [Severe Outcome Rate]) "
      "VAR t = DIVIDE(v - mn, mx - mn) "
      'RETURN IF(ISBLANK(v), BLANK(), SWITCH(TRUE(), t < 0.15, "#1B0C41", t < 0.3, "#4A0C6B", t < 0.45, "#781C6D", '
      't < 0.6, "#A52C60", t < 0.75, "#CF4446", t < 0.9, "#ED6925", "#FBB61A"))', "", "Temporal")
    # --- Environment & vehicles
    M("Env Crashes", "SUM(Environment[Crashes])", "#,0", "Conditions")
    M("Severe Outcome %", "DIVIDE(SUM(Environment[Fatal]) + SUM(Environment[Serious]), SUM(Environment[Crashes]))", "0.0%", "Conditions")
    M("Env Fatality Rate", "DIVIDE(SUM(Environment[Fatal]), SUM(Environment[Crashes]))", "0.0%", "Conditions")
    M("Env Mean Severity Weight", "DIVIDE(SUMX(Environment, Environment[Mean Severity Weight] * Environment[Crashes]), SUM(Environment[Crashes]))", "0.00", "Conditions")
    M("Vehicle Severe Rate", "DIVIDE(SUM(Vehicle[Fatal]) + SUM(Vehicle[Serious]), SUM(Vehicle[Crashes]))", "0.0%", "Conditions")
    M("Conditions Note",
      'IF(SELECTEDVALUE(StudyContext[Study Context]) = "' + IN + '", '
      '"The Bengaluru feed has no weather, surface or lighting fields, so the environmental charts are UK-only. The vehicle chart below shows corridor types.", '
      '"Vehicle chart groups UK crashes by posted speed limit. Switch Study Context to see Bengaluru corridor types.")', "", "Labels")
    # --- Maps (each map is pinned to its own study context)
    for ctx, tag in [(UK, "UK"), (IN, "India")]:
        M(f"{tag} Map X", f'CALCULATE(AVERAGE(Segments[Mid Lon]), KEEPFILTERS(Segments[Study Context] = "{ctx}"))', "0.0000", "Map")
        M(f"{tag} Map Y", f'CALCULATE(AVERAGE(Segments[Map Y]), KEEPFILTERS(Segments[Study Context] = "{ctx}"))', "0.000000", "Map")
        M(f"{tag} Map Risk", f'CALCULATE([Mean Exposure Risk], KEEPFILTERS(Segments[Study Context] = "{ctx}"))', "0.00", "Map")
    # --- India transferability page
    ind = lambda expr: f'CALCULATE({expr}, KEEPFILTERS(Segments[Study Context] = "{IN}"))'
    M("India Risk", ind("[Mean Exposure Risk]"), "0.00", "India")
    M("India AADT", ind("SUM(Segments[AADT])"), "#,0", "India")
    M("India Length km", ind("SUM(Segments[Length km])"), "0.0", "India")
    M("India Two-Wheeler Share", ind("AVERAGE(Segments[Two-Wheeler Share])"), "0%", "India")
    M("India Crashes", ind("[Total Crashes]"), "#,0", "India")
    M("India Fatalities", ind("[Total Fatalities]"), "#,0", "India")
    M("India VRU Crashes", ind("SUM(Segments[VRU Crashes])"), "#,0", "India")
    M("India Exposure", ind("[Network Exposure (MVKM)]"), "#,0.00", "India")
    # --- ML + what-if simulator (same heuristic and defaults as app.py)
    M("Feature Importance", "SUM(Features[Importance])", "0.0000", "ML")
    M("Simulated Severe Probability",
      "VAR s = SELECTEDVALUE(SimSpeed[Speed Limit (mph)], 60) "
      'VAR night = SELECTEDVALUE(SimTime[Time of Day], "Daylight") = "Dark Night" '
      'VAR unlit = SELECTEDVALUE(SimLighting[Lighting Infrastructure], "Lit by Streetlights") = "Unlit (Zero Lighting)" '
      'VAR w = SELECTEDVALUE(SimWeather[Weather Condition], "Clear / Fine") '
      'VAR vru = SELECTEDVALUE(SimRoadUser[Road User], "Vulnerable (Motorcycle / Bicycle)") = "Vulnerable (Motorcycle / Bicycle)" '
      "VAR r = 0.08 + IF(s >= 60, 0.22, IF(s >= 40, 0.10, 0)) + IF(night, 0.15, 0) + IF(unlit, 0.25, 0) "
      '+ IF(CONTAINSSTRING(w, "Rain"), 0.10, IF(CONTAINSSTRING(w, "Fog"), 0.18, 0)) + IF(vru, 0.20, 0) '
      "RETURN MIN(0.96, MAX(0.04, r))", "0.0%", "ML")
    M("Simulated vs Network", 'VAR d = [Simulated Severe Probability] - 0.25 RETURN FORMAT(d, "+0.0%;-0.0%") & " vs network average (25%)"', "", "ML")
    M("Simulated Rating",
      "VAR p = [Simulated Severe Probability] RETURN SWITCH(TRUE(), "
      'p > 0.5, "HIGH RISK: immediate engineering intervention. Install LED street lighting, automated speed cameras and anti-skid high-friction surfacing.", '
      'p > 0.25, "MODERATE RISK: add advisory electronic speed signs and reflective road studs.", '
      '"LOW RISK: within tolerable network safety thresholds.")', "", "ML")


def measures_tmdl():
    L = [f"table {M_TABLE}", f"\tlineageTag: {new_id()}", ""]
    for name, dax, fmt, folder in MEASURES:
        L.append(f"\tmeasure {tq(name)} = {dax}")
        if fmt:
            L.append(f"\t\tformatString: {fmt}")
        L += [f"\t\tdisplayFolder: {folder}", f"\t\tlineageTag: {new_id()}", ""]
    L += ["\tcolumn Column1", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {new_id()}",
          "\t\tsummarizeBy: none", "\t\tsourceColumn: Column1", "", "\t\tannotation SummarizationSetBy = Automatic", "",
          f"\tpartition {M_TABLE} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
          '\t\t\t\t    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Column1 = _t])',
          "\t\t\t\tin", "\t\t\t\t    Source", "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(L)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write_model(tables):
    shutil.rmtree(MODEL, ignore_errors=True)
    d = os.path.join(MODEL, "definition")
    write_json(os.path.join(MODEL, ".platform"), {"$schema": SCHEMA["platform"], "metadata": {"type": "SemanticModel", "displayName": NAME}, "config": {"version": "2.0", "logicalId": new_id()}})
    write_json(os.path.join(MODEL, "definition.pbism"), {"$schema": SCHEMA["pbism"], "version": "4.0", "settings": {}})
    write_text(os.path.join(d, "database.tmdl"), "database\n\tcompatibilityLevel: 1600\n")
    names = list(tables) + [M_TABLE]
    write_text(os.path.join(d, "model.tmdl"), "\n".join(
        ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US",
         "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
         f"annotation PBI_QueryOrder = {json.dumps(['DataFolder'] + names)}", "",
         "annotation __PBI_TimeIntelligenceEnabled = 0", "", 'annotation PBI_ProTooling = ["DevMode"]', ""]
        + [f"ref table {t}" for t in names] + ["", "ref cultureInfo en-US", ""]))
    data_folder = DATA.rstrip("\\/") + "\\"
    write_text(os.path.join(d, "expressions.tmdl"),
               f'expression DataFolder = "{data_folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
               f"\tlineageTag: {new_id()}\n\n\tannotation PBI_ResultType = Text\n")
    write_text(os.path.join(d, "cultures", "en-US.tmdl"),
               'cultureInfo en-US\n\n\tlinguisticMetadata =\n\t\t\t{"Version":"1.0.0","Language":"en-US"}\n\t\tcontentType: json\n')
    rels = []
    for t in ["Segments", "Hourly", "Heatmap", "Environment", "Vehicle"]:
        rels += [f"relationship {new_id()}", f"\tfromColumn: {t}.'Study Context'", "\ttoColumn: StudyContext.'Study Context'", ""]
    write_text(os.path.join(d, "relationships.tmdl"), "\n".join(rels))
    for name, df in tables.items():
        write_text(os.path.join(d, "tables", f"{name}.tmdl"), table_tmdl(name, df))
    define_measures()
    write_text(os.path.join(d, "tables", f"{M_TABLE}.tmdl"), measures_tmdl())
    print(f"model: {len(tables) + 1} tables, {len(MEASURES)} measures")


# =============================================================================
# 4. REPORT (PBIR)
# =============================================================================
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def s_(text):
    return lit("'" + str(text).replace("'", "''") + "'")


def n_(v, suffix="D"):
    return lit(f"{v}{suffix}")


def b_(v):
    return lit("true" if v else "false")


def colour(hexv):
    return {"solid": {"color": lit(f"'{hexv}'")}}


def col_field(entity, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas_field(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": M_TABLE}}, "Property": prop}}


def col(entity, prop, **extra):
    return {"field": col_field(entity, prop), "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop, **extra}


def meas(prop, **extra):
    return {"field": meas_field(prop), "queryRef": f"{M_TABLE}.{prop}", "nativeQueryRef": prop, **extra}


def resource(item):
    return {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": item}}}


def in_filter(entity, prop, values):
    """Saved slicer selection: entity[prop] IN values (text values quoted, integers as 'L' literals)."""
    lit_value = lambda v: f"{v}L" if isinstance(v, int) else "'" + str(v).replace("'", "''") + "'"
    return {"filter": {
        "Version": 2,
        "From": [{"Name": "s", "Entity": entity, "Type": 0}],
        "Where": [{"Condition": {"In": {
            "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": prop}}],
            "Values": [[{"Literal": {"Value": lit_value(v)}}] for v in values],
        }}}],
    }}


class Page:
    def __init__(self, name, display, height=900):
        self.name, self.display, self.visuals, self.z = name, display, [], 1000
        self.height = height

    def add(self, name, pos, visual, **extra):
        x, y, w, h = pos
        self.z += 1
        self.visuals.append({"$schema": SCHEMA["vc"], "name": name,
                             "position": {"x": x, "y": y, "z": self.z, "width": w, "height": h, "tabOrder": self.z},
                             "visual": visual, **extra})


def chrome(title=None, subtitle=None):
    c = {"background": [{"properties": {"show": b_(True), "color": colour(C["card"]), "transparency": n_(0)}}],
         "border": [{"properties": {"show": b_(True), "color": colour(C["border"]), "radius": n_(12)}}],
         "dropShadow": [{"properties": {"show": b_(False)}}],
         "padding": [{"properties": {"top": n_(8), "bottom": n_(8), "left": n_(12), "right": n_(12)}}]}
    if title:
        c["title"] = [{"properties": {"show": b_(True), "text": s_(title), "fontColor": colour(C["text"]), "fontSize": n_(13),
                                      "bold": b_(True), "fontFamily": s_(FONT_B), "alignment": s_("left")}}]
    else:
        c["title"] = [{"properties": {"show": b_(False)}}]
    if subtitle:
        c["subTitle"] = [{"properties": {"show": b_(True), "text": s_(subtitle), "fontColor": colour(C["text2"]),
                                         "fontSize": n_(10), "fontFamily": s_(FONT)}}]
    return c


BARE = {"background": [{"properties": {"show": b_(False)}}], "border": [{"properties": {"show": b_(False)}}],
        "title": [{"properties": {"show": b_(False)}}], "dropShadow": [{"properties": {"show": b_(False)}}]}


def axes(legend=False, labels=False, legend_pos="Top", cat_extra=None, val_extra=None):
    return {
        "categoryAxis": [{"properties": {"show": b_(True), "labelColor": colour(C["text2"]), "fontSize": n_(10),
                                         "showAxisTitle": b_(True), "titleColor": colour(C["text2"]), "gridlineShow": b_(False),
                                         **(cat_extra or {})}}],
        "valueAxis": [{"properties": {"show": b_(True), "labelColor": colour(C["text2"]), "fontSize": n_(10),
                                      "showAxisTitle": b_(True), "titleColor": colour(C["text2"]), "gridlineShow": b_(True),
                                      "gridlineColor": colour(C["grid"]), "gridlineStyle": s_("dotted"), **(val_extra or {})}}],
        "labels": [{"properties": {"show": b_(labels), "color": colour(C["text"]), "fontSize": n_(9)}}],
        "legend": [{"properties": {"show": b_(legend), "position": s_(legend_pos), "labelColor": colour(C["text"]),
                                   "fontSize": n_(10), "showTitle": b_(False)}}],
    }


def series_colours(entity, prop, mapping):
    return [{"properties": {"fill": colour(hexv)},
             "selector": {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": col_field(entity, prop),
                                                               "Right": {"Literal": {"Value": "'" + k.replace("'", "''") + "'"}}}}}]}}
            for k, hexv in mapping.items()]


def chart(page, name, pos, vtype, roles, title=None, subtitle=None, objects=None, sort=None):
    query = {"queryState": {r: {"projections": p} for r, p in roles.items()}}
    if sort:
        query["sortDefinition"] = {"sort": [{"field": sort[0], "direction": sort[1]}], "isDefaultSort": True}
    page.add(name, pos, {"visualType": vtype, "query": query, "objects": objects or {},
                         "visualContainerObjects": chrome(title, subtitle), "drillFilterOtherVisuals": True})


def kpi(page, name, pos, main, label, ref=None, accent=C["sky"], font_size=22):
    main_ref = f"{M_TABLE}.{main}"
    qs = {"Data": {"projections": [meas(main, displayName=label)]}}
    if ref:
        qs["ReferenceLabels"] = {"projections": [meas(ref)]}
    d = {"id": "default"}
    objects = {
        "outline": [{"properties": {"show": b_(False)}, "selector": d}],
        "divider": [{"properties": {"show": b_(False)}, "selector": d}],
        "fillCustom": [{"properties": {"show": b_(False)}}],
        "shadowCustom": [{"properties": {"show": b_(False)}}],
        "label": [{"properties": {"show": b_(False)}, "selector": d}],
        "value": [{"properties": {"fontSize": n_(font_size), "fontFamily": s_(FONT_B), "fontColor": colour(C["text"]),
                                  "labelDisplayUnits": n_(1)}, "selector": d}],
        "layout": [{"properties": {"paddingUniform": n_(2, "L"), "verticalAlignment": s_("Top")}, "selector": d}],
        "padding": [{"properties": {"paddingIndividual": b_(True), "paddingLeft": n_(10, "L"), "paddingTop": n_(0, "L"),
                                    "paddingBottom": n_(0, "L"), "paddingRight": n_(0, "L")}, "selector": d}],
        "accentBar": [{"properties": {"show": b_(True), "color": colour(accent), "width": n_(4), "position": s_("Left")}, "selector": d}],
    }
    if ref:
        fid = "ref-" + name
        objects["referenceLabel"] = [
            {"properties": {"backgroundShow": b_(False), "paddingUniform": n_(0, "L"), "paddingIndividual": b_(True),
                            "paddingTop": n_(2, "L"), "paddingLeft": n_(10, "L")}, "selector": d},
            {"properties": {"value": {"expr": meas_field(ref)}},
             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 0}}], "metadata": main_ref, "id": fid, "order": 0}}]
        objects["referenceLabelTitle"] = [{"properties": {"show": b_(False)}, "selector": {"metadata": main_ref, "id": fid}}]
        objects["referenceLabelValue"] = [{"properties": {"valueFontColor": colour(accent), "valueFontSize": n_(10),
                                                          "valueBold": b_(True), "valueFontFamily": s_(FONT_B)},
                                           "selector": {"metadata": main_ref, "id": fid}}]
        objects["referenceLabelDetail"] = [{"properties": {"show": b_(False)}, "selector": {"metadata": main_ref, "id": fid}}]
    ch = chrome(label.upper())
    ch["title"][0]["properties"].update({"fontSize": n_(10), "fontColor": colour(C["text2"])})
    page.add(name, pos, {"visualType": "cardVisual", "query": {"queryState": qs}, "objects": objects,
                         "visualContainerObjects": ch, "drillFilterOtherVisuals": True})


def text_card(page, name, pos, measure, title=None, font_size=12, font_colour=None, accent=None):
    """Card that shows a text measure as a sentence (insights / notes that react to slicers)."""
    d = {"id": "default"}
    objects = {
        "outline": [{"properties": {"show": b_(False)}, "selector": d}], "divider": [{"properties": {"show": b_(False)}, "selector": d}],
        "fillCustom": [{"properties": {"show": b_(False)}}], "shadowCustom": [{"properties": {"show": b_(False)}}],
        "label": [{"properties": {"show": b_(False)}, "selector": d}],
        "accentBar": [{"properties": {"show": b_(accent is not None), "color": colour(accent or C["sky"]), "width": n_(4), "position": s_("Left")}, "selector": d}],
        "value": [{"properties": {"fontSize": n_(font_size), "fontFamily": s_(FONT_B), "fontColor": colour(font_colour or C["text"]),
                                  "horizontalAlignment": s_("left")}, "selector": d}],
        "layout": [{"properties": {"paddingUniform": n_(0, "L"), "verticalAlignment": s_("Middle"), "alignment": s_("left")}, "selector": d}],
        "padding": [{"properties": {"paddingUniform": n_(4, "L")}, "selector": d}],
    }
    page.add(name, pos, {"visualType": "cardVisual", "query": {"queryState": {"Data": {"projections": [meas(measure)]}}},
                         "objects": objects, "visualContainerObjects": chrome(title), "drillFilterOtherVisuals": True})


def textbox(page, name, pos, paragraphs, boxed=False):
    """paragraphs: list of lists of (text, size, colour, bold)."""
    paras = [{"horizontalTextAlignment": "left",
              "textRuns": [{"value": t, "textStyle": {"fontFamily": FONT_B if b else FONT, "fontSize": f"{sz}pt", "color": c,
                                                      **({"fontWeight": "bold"} if b else {})}} for (t, sz, c, b) in runs]}
             for runs in paragraphs]
    vco = chrome() if boxed else dict(BARE)
    if boxed:
        vco["padding"] = [{"properties": {"top": n_(10), "bottom": n_(10), "left": n_(14), "right": n_(14)}}]
    page.add(name, pos, {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
                         "visualContainerObjects": vco, "drillFilterOtherVisuals": True})


def slicer(page, name, pos, entity, prop, title, mode="Dropdown", single=False, default=None, sync=None, horizontal=False):
    objects = {
        "data": [{"properties": {"mode": s_(mode)}}],
        "header": [{"properties": {"show": b_(True), "text": s_(title), "fontColor": colour(C["text2"]), "fontSize": n_(10),
                                   "fontFamily": s_(FONT_B)}}],
        "items": [{"properties": {"fontColor": colour(C["text"]), "background": colour(C["alt"]), "fontSize": n_(10),
                                  "fontFamily": s_(FONT_B)}}],
        "selection": [{"properties": {"selectAllCheckboxEnabled": b_(not single), "singleSelect": b_(single),
                                      **({"strictSingleSelect": b_(True)} if single else {})}}],
    }
    general = {}
    if horizontal:
        general["orientation"] = n_(1)
    if default:
        general["filter"] = in_filter(entity, prop, default)
    if general:
        objects["general"] = [{"properties": general}]
    vco = dict(BARE)
    vco["padding"] = [{"properties": {"top": n_(0), "bottom": n_(0), "left": n_(0), "right": n_(0)}}]
    visual = {"visualType": "slicer", "query": {"queryState": {"Values": {"projections": [col(entity, prop, active=True)]}}},
              "objects": objects, "visualContainerObjects": vco, "drillFilterOtherVisuals": True}
    if sync:
        visual["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
    page.add(name, pos, visual)


def table_objects(size=10):
    return {
        "grid": [{"properties": {"gridVertical": b_(False), "gridHorizontal": b_(True), "gridHorizontalColor": colour(C["border"]),
                                 "rowPadding": n_(3, "L"), "outlineColor": colour(C["border"]), "textSize": n_(size)}}],
        "columnHeaders": [{"properties": {"fontColor": colour(C["sky"]), "backColor": colour(C["page"]), "fontSize": n_(size),
                                          "bold": b_(True), "fontFamily": s_(FONT_B), "outline": s_("BottomOnly"), "autoSizeColumnWidth": b_(True)}}],
        "values": [{"properties": {"fontColorPrimary": colour(C["text"]), "backColorPrimary": colour(C["card"]),
                                   "fontColorSecondary": colour(C["text"]), "backColorSecondary": colour(C["alt"]),
                                   "fontSize": n_(size), "fontFamily": s_(FONT)}}],
        "total": [{"properties": {"totals": b_(False)}}],
    }


PAGE_W, PAGE_H, MX = 1600, 900, 24
NAV = (MX, 92, PAGE_W - 2 * MX, 36)


def header(page, title, subtitle):
    textbox(page, "hdrTitle", (MX, 10, 1150, 46), [[(title, 20, C["sky"], True)]])
    textbox(page, "hdrSub", (MX, 54, 1150, 32), [[(subtitle, 10.5, C["text2"], False)]])
    textbox(page, "hdrBadge", (1180, 18, 396, 64), [
        [("Visual Analytics Lab — Review 1", 10, C["text"], True)],
        [("S. Dalal · D. Pujari · R. Yadav  ·  Guide: Dr Manikandan K", 9, C["text2"], False)]])
    page.add("hdrNav", NAV, {"visualType": "pageNavigator", "objects": {
        "shape": [{"properties": {"tileShape": s_("rectangleRounded"), "rectangleRoundedCurve": n_(10, "L")}}],
        "fill": [{"properties": {"show": b_(True), "fillColor": colour(C["alt"]), "transparency": n_(0)}},
                 {"properties": {"fillColor": colour(C["rose"]), "transparency": n_(0)}, "selector": {"id": "selected"}},
                 {"properties": {"fillColor": colour("#334155"), "transparency": n_(0)}, "selector": {"id": "hover"}}],
        "text": [{"properties": {"show": b_(True), "fontColor": colour(C["text"]), "fontSize": n_(10), "bold": b_(True), "fontFamily": s_(FONT_B)}},
                 {"properties": {"fontColor": colour("#FFFFFF")}, "selector": {"id": "selected"}}],
        "outline": [{"properties": {"show": b_(False)}}],
        "layout": [{"properties": {"orientation": n_(2)}}],
        "pages": [{"properties": {"showHiddenPages": b_(False)}}]},
        "visualContainerObjects": BARE, "drillFilterOtherVisuals": True})


def context_filters(page, sync=True, with_suppression=True):
    """The dashboard sidebar: study context, road class, suppression threshold."""
    y = 138
    slicer(page, "fltContext", (MX, y, 520, 52), "StudyContext", "Study Context", "STUDY CONTEXT", mode="Basic",
           single=True, default=[UK] if sync else None, sync="sgContext" if sync else None, horizontal=True)
    slicer(page, "fltRoadClass", (MX + 540, y, 300, 52), "Segments", "Road Class", "ROAD HIERARCHY CLASS", sync="sgRoadClass")
    if with_suppression:
        slicer(page, "fltSuppression", (MX + 860, y, 300, 52), "Segments", "Suppression",
               "SUPPRESSION THRESHOLD (<3 crashes or <0.2 MVKM)", default=["Reported"], sync="sgSuppression")


def build_pages(bounds):
    pages = []
    TOP = 202

    # ---------------- Page 1: Core contribution
    p = Page("p1Core", "Core: Frequency vs Severity", height=1020)
    header(p, "Traffic Accident Analysis & Exposure-Adjusted Visualization",
           "Research gap & core contribution: low frequency masks high severity. Risk = severity-weighted crashes (Fatal 50 · Serious 10 · Slight 1) per million vehicle-km.")
    context_filters(p)
    kw, kg = (PAGE_W - 2 * MX - 4 * 14) // 5, 14
    cards = [("Total Crashes", "Total Crashes Ingested", "Raw Incidents Label", C["sky"]),
             ("Network Exposure (MVKM)", "Network Exposure", "Exposure Label", C["green"]),
             ("Lethal Trap Segments", "Lethal Trap Segments", "Trap Label", C["rose"]),
             ("Total Fatalities", "Total Fatalities", "Fatal Label", C["rose"]),
             ("Mean Exposure Risk", "Mean Exposure Risk", "Risk Label", C["indigo"])]
    for i, (m, lbl, ref, acc) in enumerate(cards):
        kpi(p, f"kpi{i}", (MX + i * (kw + kg), TOP, kw, 116), m, lbl, ref=ref, accent=acc)
    y2 = TOP + 130
    chart(p, "tblBenchmark", (MX, y2, 820, 184), "tableEx", {"Values": [
        col("Segments", "Benchmark Role", displayName="Role"), col("Segments", "Segment ID", displayName="Segment"),
        col("Segments", "Road Name", displayName="Road"), col("Segments", "Road Class", displayName="Class"),
        meas("Bench AADT", displayName="AADT"), meas("Bench Crashes", displayName="Crashes"),
        meas("Bench Raw Rank", displayName="Count rank"), meas("Bench Exposure", displayName="MVKM"),
        meas("Bench Risk", displayName="Risk / MVKM"), meas("Bench Risk Rank", displayName="Risk rank")]},
        title="Benchmark pair: raw count rank vs exposure-adjusted rank",
        subtitle="UK: Slide 9 case study (SEG-0417 vs SEG-1902). India: corridors with the largest rank inversion.",
        objects=table_objects(9.5))
    text_card(p, "cardHeadline", (MX, y2 + 194, 820, 80), "Benchmark Headline", title="HIDDEN HOTSPOT vs BUSY CORRIDOR",
              font_size=15, font_colour=C["rose"], accent=C["rose"])
    chart(p, "tblQuadrants", (MX + 834, y2, PAGE_W - 2 * MX - 834, 274), "tableEx", {"Values": [
        col("Segments", "Quadrant"), meas("Segment Count", displayName="Segments"), meas("Total Crashes", displayName="Crashes"),
        meas("Total Fatalities", displayName="Fatal"), meas("Total Serious Injuries", displayName="Serious"),
        meas("Mean Exposure per Segment", displayName="Mean MVKM"), meas("Mean Exposure Risk", displayName="Mean risk"),
        meas("Fatality Share %", displayName="Fatality share")]},
        title="Intervention prioritisation by risk quadrant", objects=table_objects(9),
        sort=(meas_field("Mean Exposure Risk"), "Descending"))
    y3 = y2 + 288
    chart(p, "scQuadrant", (MX, y3, PAGE_W - 2 * MX, p.height - y3 - 16), "scatterChart", {
        "Category": [col("Segments", "Segment ID", active=True)], "Series": [col("Segments", "Quadrant")],
        "X": [meas("Total Crashes", displayName="Crash count")],
        "Y": [meas("Mean Exposure Risk", displayName="Risk / MVKM")],
        "Size": [meas("Network Exposure (MVKM)", displayName="Exposure (MVKM)")],
        "Tooltips": [col("Segments", "Road Name"), col("Segments", "Road Class"), meas("Raw Rank"), meas("Risk Rank")]},
        title="The frequency vs severity 4-quadrant decision matrix",
        subtitle="X = annual crash count (raw frequency). Y = exposure-adjusted severity risk per MVKM. Bubble size = exposure. Q2 'deadly traps' sit top-left.",
        objects={**axes(legend=True, legend_pos="Top"), "dataPoint": series_colours("Segments", "Quadrant", QUAD_COLOURS),
                 "bubbles": [{"properties": {"bubbleSize": n_(-10, "L")}}], "categoryLabels": [{"properties": {"show": b_(False)}}]})
    pages.append(p)

    # ---------------- Page 2: WHEN?
    p = Page("p2When", "WHEN? Circadian & Temporal", height=980)
    header(p, "Research Question 1: WHEN do accidents happen vs. WHEN are they lethal?",
           "24-hour circadian profile and the 168-cell day-of-week × hour matrix for the selected study context.")
    context_filters(p, with_suppression=False)
    kw = (PAGE_W - 2 * MX - 3 * 14) // 4
    for i, (m, lbl, ref, acc) in enumerate([("Peak Volume Hour", "Peak crash volume", "Peak Volume Label", C["sky"]),
                                             ("Most Lethal Hour", "Most lethal hour", "Most Lethal Label", C["rose"]),
                                             ("Night Fatality Rate", "Night fatality share (20:00-05:59)", "Night vs Day Label", C["orange"]),
                                             ("VRU Share", "Vulnerable road user share", "VRU Label", C["purple"])]):
        kpi(p, f"kpi{i}", (MX + i * (kw + 14), TOP, kw, 116), m, lbl, ref=ref, accent=acc)
    y2 = TOP + 130
    chart(p, "comboHourly", (MX, y2, PAGE_W - 2 * MX, 270), "lineClusteredColumnComboChart", {
        "Category": [col("Hourly", "Hour", active=True)],
        "Y": [meas("Hourly Crashes", displayName="Accident count (volume)")],
        "Y2": [meas("Hourly Fatality Rate", displayName="Fatality share % (lethality)")]},
        title="24-hour circadian risk: crash frequency vs lethality rate",
        subtitle="Bars = crash volume. Line = share of crashes that were fatal.",
        objects={**axes(legend=True, cat_extra={"axisType": s_("Categorical")}),
                 "dataPoint": [{"properties": {"fill": colour(C["sky"])}, "selector": {"metadata": f"{M_TABLE}.Hourly Crashes"}},
                               {"properties": {"fill": colour(C["rose"])}, "selector": {"metadata": f"{M_TABLE}.Hourly Fatality Rate"}}],
                 "lineStyles": [{"properties": {"strokeWidth": n_(3), "showMarker": b_(True), "markerSize": n_(5)}}]},
        sort=(col_field("Hourly", "Hour"), "Ascending"))
    y3 = y2 + 284
    heat_objs = table_objects(9)
    heat_objs["values"] = [
        {"properties": {"fontColorPrimary": colour("#FFFFFF"), "backColorPrimary": colour(C["card"]),
                        "fontColorSecondary": colour("#FFFFFF"), "backColorSecondary": colour(C["card"]),
                        "fontSize": n_(8), "fontFamily": s_(FONT)}},
        {"properties": {"backColor": {"solid": {"color": {"expr": meas_field("Heatmap Colour")}}}},
         "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{M_TABLE}.Severe Outcome Rate"}}]
    heat_objs["subTotals"] = [{"properties": {"rowSubtotals": b_(False), "columnSubtotals": b_(False)}}]
    heat_objs["rowHeaders"] = [{"properties": {"fontColor": colour(C["text"]), "backColor": colour(C["page"]), "fontSize": n_(9)}}]
    chart(p, "mxHeatmap", (MX, y3, PAGE_W - 2 * MX, p.height - y3 - 16), "pivotTable", {
        "Rows": [col("Heatmap", "Day", active=True)], "Columns": [col("Heatmap", "Hour", active=True)],
        "Values": [meas("Severe Outcome Rate", displayName="Severe outcome rate")]},
        title="The 168-cell heatmap matrix (day of week × hour): severe outcome rate (fatal + serious share)",
        subtitle="Colour runs dark purple (lowest) to yellow (highest) within the selected context.", objects=heat_objs)
    pages.append(p)

    # ---------------- Page 3: WHERE?
    p = Page("p3Where", "WHERE? Spatial Hotspots", height=1040)
    header(p, "Research Question 2: WHERE are the True Spatial Hotspots?",
           "Road segments on a basemap, side by side for both study contexts. Dot colour = risk quadrant, dot size = exposure-adjusted risk. Hover for ranks.")
    slicer(p, "fltContext", (MX, 138, 520, 52), "StudyContext", "Study Context", "STUDY CONTEXT (leave empty to show both maps)",
           mode="Basic", single=False, horizontal=True)
    slicer(p, "fltRoadClass", (MX + 540, 138, 300, 52), "Segments", "Road Class", "ROAD HIERARCHY CLASS", sync="sgRoadClass")
    slicer(p, "fltSuppression", (MX + 860, 138, 300, 52), "Segments", "Suppression",
           "SUPPRESSION THRESHOLD (<3 crashes or <0.2 MVKM)", default=["Reported"], sync="sgSuppression")
    map_h = 450
    uk_w, in_w = 930, PAGE_W - 2 * MX - 930 - 14
    for tag, ctx, x, w, img in [("UK", UK, MX, uk_w, "basemap_uk.png"), ("India", IN, MX + uk_w + 14, in_w, "basemap_india.png")]:
        bnd = bounds[tag]
        chart(p, f"map{tag}", (x, TOP, w, map_h), "scatterChart", {
            "Category": [col("Segments", "Segment ID", active=True)], "Series": [col("Segments", "Quadrant")],
            "X": [meas(f"{tag} Map X", displayName="Longitude")], "Y": [meas(f"{tag} Map Y", displayName="Latitude (Mercator)")],
            "Size": [meas(f"{tag} Map Risk", displayName="Risk / MVKM")],
            "Tooltips": [col("Segments", "Road Name"), col("Segments", "Road Class"), meas("Total Crashes"), meas("Raw Rank"),
                         meas("Network Exposure (MVKM)"), meas("Mean Exposure Risk"), meas("Risk Rank"), meas("Rank Shift")]},
            title=f"{ctx}", subtitle="Basemap: Esri Dark Gray Canvas (Esri, HERE, Garmin, © OpenStreetMap contributors)",
            objects={
                "categoryAxis": [{"properties": {"show": b_(False), "start": n_(bnd["lon_min"]), "end": n_(bnd["lon_max"]),
                                                 "showAxisTitle": b_(False), "gridlineShow": b_(False)}}],
                "valueAxis": [{"properties": {"show": b_(False), "start": n_(bnd["y_min"]), "end": n_(bnd["y_max"]),
                                              "showAxisTitle": b_(False), "gridlineShow": b_(False)}}],
                "plotArea": [{"properties": {"transparency": n_(0), "image": {"image": {
                    "name": s_(img), "url": resource(img), "scaling": s_("Fill")}}}}],
                "bubbles": [{"properties": {"bubbleSize": n_(-38 if tag == "UK" else -22, "L")}}],
                "legend": [{"properties": {"show": b_(False)}}],
                "categoryLabels": [{"properties": {"show": b_(False)}}],
                "dataPoint": series_colours("Segments", "Quadrant", QUAD_COLOURS)})
    textbox(p, "mapLegend", (MX, TOP + map_h + 4, PAGE_W - 2 * MX, 34), [[
        ("●", 11, QUAD_COLOURS["Q1: High Frequency - High Severity (Severe Congested)"], True), (" Q1 severe congested    ", 9.5, C["text2"], False),
        ("●", 11, QUAD_COLOURS["Q2: Low Frequency - High Severity (Deadly Trap - Primary Focus)"], True), (" Q2 deadly trap (primary focus)    ", 9.5, C["text2"], False),
        ("●", 11, QUAD_COLOURS["Q3: Low Frequency - Low Severity (Safe Segment)"], True), (" Q3 safe segment    ", 9.5, C["text2"], False),
        ("●", 11, QUAD_COLOURS["Q4: High Frequency - Low Severity (Fender-Benders)"], True), (" Q4 fender-benders    ", 9.5, C["text2"], False),
        ("●", 11, QUAD_COLOURS["Suppressed (Low Sample Noise)"], True), (" suppressed (low sample)    Grey lines = road segments", 9.5, C["text2"], False)]])
    y3 = TOP + map_h + 44
    chart(p, "tblLeaderboard", (MX, y3, PAGE_W - 2 * MX, p.height - y3 - 16), "tableEx", {"Values": [
        col("Segments", "Study Context", displayName="Context"), col("Segments", "Segment ID", displayName="Segment"),
        col("Segments", "Road Name", displayName="Road"), col("Segments", "Road Class", displayName="Class"),
        meas("Total Crashes", displayName="Crashes"), meas("Raw Rank", displayName="Count rank"),
        meas("Network Exposure (MVKM)", displayName="MVKM"), meas("Mean Exposure Risk", displayName="Risk / MVKM"),
        meas("Risk Rank", displayName="Risk rank"), meas("Rank Shift", displayName="Rank shift"), col("Segments", "Quadrant")]},
        title="High-risk segment leaderboard (sorted by exposure-adjusted risk)",
        subtitle="Rank shift = raw-count rank − risk rank. Positive = under-ranked by raw counts (hidden risk). Click a column header to re-sort.",
        objects=table_objects(10), sort=(meas_field("Mean Exposure Risk"), "Descending"))
    pages.append(p)

    # ---------------- Page 4: UNDER WHAT CONDITIONS?
    p = Page("p4Conditions", "UNDER WHAT CONDITIONS?")
    header(p, "Research Question 3: Environmental Hostility & Severity Modulation",
           "Joint impact of weather, road surface and street lighting on severe outcomes, plus vulnerable road users by speed limit or corridor type.")
    context_filters(p, with_suppression=False)
    text_card(p, "cardNote", (MX + 860, 138, PAGE_W - 2 * MX - 860, 52), "Conditions Note", font_size=10, font_colour=C["text2"])
    half = (PAGE_W - 2 * MX - 14) // 2
    chart(p, "barEnv", (MX, TOP, half, 330), "clusteredBarChart", {
        "Category": [col("Environment", "Road Surface", active=True)], "Series": [col("Environment", "Lighting Condition")],
        "Y": [meas("Severe Outcome %", displayName="Fatal & serious outcome share")]},
        title="Severe / fatal outcome % by surface condition & lighting", objects=axes(legend=True),
        sort=(meas_field("Severe Outcome %"), "Descending"))
    chart(p, "colVehicle", (MX + half + 14, TOP, half, 330), "clusteredColumnChart", {
        "Category": [col("Vehicle", "Speed Limit or Corridor", active=True)], "Series": [col("Vehicle", "Vehicle Mode")],
        "Y": [meas("Vehicle Severe Rate", displayName="Severe rate")]},
        title="Vulnerable road users: severe injury rate by speed limit (UK) or corridor type (India) and vehicle mode",
        objects=axes(legend=True), sort=(col_field("Vehicle", "Speed Limit or Corridor"), "Ascending"))
    y3 = TOP + 344
    chart(p, "tblEnv", (MX, y3, PAGE_W - 2 * MX, p.height - y3 - 16), "tableEx", {"Values": [
        col("Environment", "Weather"), col("Environment", "Road Surface"), col("Environment", "Lighting Condition"),
        meas("Env Crashes", displayName="Crashes"), meas("Severe Outcome %", displayName="Severe outcome"),
        meas("Env Fatality Rate", displayName="Fatality rate"), meas("Env Mean Severity Weight", displayName="Mean severity wt")]},
        title="Environmental friction & hostility matrix", objects=table_objects(10),
        sort=(meas_field("Severe Outcome %"), "Descending"))
    pages.append(p)

    # ---------------- Page 5: ML & simulator
    p = Page("p5ML", "ML & What-If Simulator")
    header(p, "Machine Learning Severity Classifier & What-If Policy Simulator",
           "Random Forest trained on the UK STATS19 records (feature importances below). The simulator uses the same scoring as the dashboard sandbox.")
    half = (PAGE_W - 2 * MX - 14) // 2
    chart(p, "barFeatures", (MX, 138, half, PAGE_H - 138 - 16), "clusteredBarChart", {
        "Category": [col("Features", "Feature", active=True)], "Y": [meas("Feature Importance", displayName="Importance weight")]},
        title="Key drivers of severe / fatal accident probability", subtitle="Random Forest feature importances (UK model)",
        objects={**axes(labels=True), "dataPoint": [{"properties": {"fill": colour(C["purple"])}}]},
        sort=(meas_field("Feature Importance"), "Descending"))
    sx = MX + half + 14
    textbox(p, "simIntro", (sx, 134, half, 56), [[("Interactive 'what-if' safety intervention simulator", 13, C["text"], True)],
                                                 [("Tune road characteristics and conditions. Starts at the dashboard defaults (60 mph, daylight, lit, clear, vulnerable user).", 9.5, C["text2"], False)]])
    sw = (half - 14) // 2
    sim = [("SimSpeed", "Speed Limit (mph)", "POSTED SPEED LIMIT (MPH)", 60), ("SimTime", "Time of Day", "TIME OF DAY", "Daylight"),
           ("SimLighting", "Lighting Infrastructure", "LIGHTING INFRASTRUCTURE", "Lit by Streetlights"),
           ("SimWeather", "Weather Condition", "WEATHER CONDITION", "Clear / Fine"),
           ("SimRoadUser", "Road User", "ROAD USER", "Vulnerable (Motorcycle / Bicycle)")]
    for i, (t, c, ttl, dflt) in enumerate(sim):
        slicer(p, f"sim{i}", (sx + (i % 2) * (sw + 14), 196 + (i // 2) * 62, sw, 52), t, c, ttl, single=True, default=[dflt])
    kpi(p, "kpiSim", (sx, 392, half, 120), "Simulated Severe Probability", "Simulated probability of severe / fatal outcome",
        ref="Simulated vs Network", accent=C["rose"], font_size=34)
    text_card(p, "cardRating", (sx, 526, half, 90), "Simulated Rating", title="RECOMMENDATION", font_size=12, accent=C["orange"])
    textbox(p, "simNote", (sx, 630, half, PAGE_H - 630 - 16), [
        [("How the score is built", 11, C["text"], True)],
        [("Base 8%  +22% if limit ≥ 60 mph (+10% if ≥ 40)  +15% dark night  +25% unlit  +10% rain / +18% fog  +20% vulnerable user. Capped to 4%–96%.", 10, C["text2"], False)],
        [("Literature link (Slide 4): XGBoost, SVM and DeepSHAP severity models rank speed, lighting and road-user vulnerability as top drivers.", 10, C["text2"], False)]],
        boxed=True)
    pages.append(p)

    # ---------------- Page 6: India transferability
    p = Page("p6India", "India Transferability Case")
    header(p, "Transferability Case: Indian Urban Corridor (Bengaluru)",
           "Decision point (Slide 7): the UK is the only context where crash records and official AADT are both open and joinable. Build there, then use an Indian city as the transferability case.")
    w1 = 900
    chart(p, "barIndia", (MX, 138, w1, 380), "clusteredBarChart", {
        "Category": [col("Segments", "Road Name", active=True)], "Series": [col("Segments", "Road Class")],
        "Y": [meas("India Risk", displayName="Risk per MVKM")]},
        title="Corridor exposure-adjusted risk rankings (Bengaluru)", objects=axes(legend=True, labels=True),
        sort=(meas_field("India Risk"), "Descending"))
    textbox(p, "indiaNotes", (MX + w1 + 14, 138, PAGE_W - 2 * MX - w1 - 14, 380), [
        [("Structural differences vs UK STATS19", 13, C["text"], True)], [(" ", 6, C["text"], False)],
        [("Modal split: ", 10.5, C["sky"], True), ("two-wheelers and auto-rickshaws dominate (62% share vs 16% in the UK).", 10.5, C["text2"], False)],
        [(" ", 6, C["text"], False)],
        [("NHAI FASTag volume proxy: ", 10.5, C["sky"], True), ("highway toll plazas capture freight and passenger cars, but two-wheelers are toll-exempt, so synthetic expansion factors are needed.", 10.5, C["text2"], False)],
        [(" ", 6, C["text"], False)],
        [("Peripheral highway hazards: ", 10.5, C["sky"], True), ("Kanakapura Highway (NH-948) shows low-frequency / high-severity behaviour from unlit stretches and mixed slow/fast traffic conflicts.", 10.5, C["text2"], False)]],
        boxed=True)
    chart(p, "tblIndia", (MX, 532, PAGE_W - 2 * MX, PAGE_H - 532 - 16), "tableEx", {"Values": [
        col("Segments", "Segment ID", displayName="Segment"), col("Segments", "Road Name", displayName="Corridor"),
        col("Segments", "Road Class", displayName="Class"), meas("India Length km", displayName="Length km"),
        meas("India AADT", displayName="AADT"), meas("India Two-Wheeler Share", displayName="Two-wheeler share"),
        meas("India Crashes", displayName="Crashes"), meas("India Fatalities", displayName="Fatal"),
        meas("India VRU Crashes", displayName="VRU crashes"), meas("India Exposure", displayName="MVKM"),
        meas("India Risk", displayName="Risk / MVKM")]},
        title="Bengaluru corridor data", objects=table_objects(10.5), sort=(meas_field("India Risk"), "Descending"))
    pages.append(p)

    # ---------------- Page 7: Pipeline
    p = Page("p7Pipeline", "Pipeline Architecture")
    header(p, "Proposed System Architecture & Batch Pipeline",
           "Batch, reproducible, zero-server pipeline using DuckDB columnar storage and pre-aggregated cubes (Slide 10).")
    stages = [("1. Data ingestion", "Python + Parquet", "UK STATS19, road network (OSM), AADT, Open-Meteo. Immutable raw storage in data/raw/*.parquet."),
              ("2. Preprocessing", "Pandas", "De-duplication, geocoding validation, data-quality flags."),
              ("3. Feature engineering", "Pandas", "Circadian phase (24h), seasonal drift, DfT severity weights: Fatal 50, Serious 10, Slight 1."),
              ("4. Exposure & risk", "DuckDB SQL", "Grain changes to road segment: exposure_mvkm = AADT × length_km × 365 / 1,000,000; risk_per_mvkm = severity_wt_sum / exposure_mvkm."),
              ("5. Cube aggregation", "Parquet + GeoJSON", "Temporal matrix, circadian profile, environmental interactions, 4 quadrants, India context cubes."),
              ("6. Visual layer", "Streamlit app.py + this Power BI report", "Both read the same pre-aggregated cubes. powerbi/build_powerbi_report.py exports them to CSV.")]
    bw = (PAGE_W - 2 * MX - 2 * 14) // 3
    for i, (t, tech, body) in enumerate(stages):
        textbox(p, f"stage{i}", (MX + (i % 3) * (bw + 14), 140 + (i // 3) * 190, bw, 176),
                [[(t, 14, C["sky"], True)], [(tech, 10, C["indigo"], True)], [(" ", 5, C["text"], False)], [(body, 10.5, C["text2"], False)]],
                boxed=True)
    textbox(p, "principles", (MX, 534, PAGE_W - 2 * MX, PAGE_H - 534 - 16), [
        [("Design principles", 14, C["text"], True)], [(" ", 5, C["text"], False)],
        [("Why DuckDB, not Postgres? ", 10.5, C["sky"], True), ("No server to run, embedded columnar format, reads Parquet directly, sub-second analytical window functions.", 10.5, C["text2"], False)],
        [("Why pre-aggregate, not query live? ", 10.5, C["sky"], True), ("1.5M crash rows will not filter interactively in a browser. Stages 4 and 5 run once in about 5 seconds; the dashboards read the cubes instantly.", 10.5, C["text2"], False)],
        [("No Airflow: ", 10.5, C["sky"], True), ("sequential Python scripts (01_ to 04_) keep the pipeline reproducible and easy to defend in review.", 10.5, C["text2"], False)],
        [(" ", 5, C["text"], False)],
        [("Refresh this report: ", 10.5, C["green"], True), ("python run_pipeline.py  →  python powerbi/build_powerbi_report.py  →  open the .pbip in Power BI Desktop  →  Home › Refresh.", 10.5, C["text2"], False)]],
        boxed=True)
    pages.append(p)
    return pages


def theme():
    solid = lambda c: {"solid": {"color": c}}
    return {
        "name": "TrafficDark",
        "dataColors": [C["sky"], C["rose"], C["green"], C["orange"], C["indigo"], C["purple"], "#FACC15", "#2DD4BF", C["slate"]],
        "background": C["page"], "foreground": C["text"], "tableAccent": C["sky"],
        "good": C["green"], "bad": C["rose"], "neutral": "#FACC15",
        "textClasses": {"callout": {"fontSize": 24, "fontFace": FONT_B, "color": C["text"]},
                        "title": {"fontSize": 13, "fontFace": FONT_B, "color": C["text"]},
                        "header": {"fontSize": 11, "fontFace": FONT_B, "color": C["text"]},
                        "label": {"fontSize": 10, "fontFace": FONT, "color": C["text2"]}},
        "visualStyles": {
            "*": {"*": {"background": [{"show": True, "color": solid(C["card"]), "transparency": 0}],
                        "border": [{"show": True, "color": solid(C["border"]), "radius": 12}],
                        "title": [{"show": True, "fontColor": solid(C["text"]), "fontSize": 13, "fontFamily": FONT_B}],
                        "categoryAxis": [{"labelColor": solid(C["text2"]), "titleColor": solid(C["text2"]), "fontSize": 10}],
                        "valueAxis": [{"labelColor": solid(C["text2"]), "titleColor": solid(C["text2"]), "fontSize": 10, "gridlineColor": solid(C["grid"])}],
                        "legend": [{"labelColor": solid(C["text"]), "fontSize": 10}],
                        "labels": [{"color": solid(C["text"]), "fontSize": 9}],
                        "visualTooltip": [{"background": solid("#0F172A"), "titleFontColor": solid(C["text"]), "valueFontColor": solid(C["text"])}],
                        "visualHeader": [{"show": True, "background": solid(C["card"]), "border": solid(C["card"]), "foreground": solid(C["text2"])}]}},
            "page": {"*": {"background": [{"color": solid(C["page"]), "transparency": 0}],
                           "outspace": [{"color": solid("#060A14"), "transparency": 0}]}},
            "textbox": {"*": {"background": [{"show": False}], "border": [{"show": False}], "title": [{"show": False}]}},
            "slicer": {"*": {"items": [{"fontColor": solid(C["text"]), "background": solid(C["alt"])}],
                             "header": [{"fontColor": solid(C["text2"])}]}},
            "tableEx": {"*": {"values": [{"backColor": solid(C["card"]), "fontColor": solid(C["text"])}],
                              "columnHeaders": [{"backColor": solid(C["page"]), "fontColor": solid(C["sky"])}]}},
            "pivotTable": {"*": {"values": [{"backColor": solid(C["card"]), "fontColor": solid(C["text"])}],
                                 "columnHeaders": [{"backColor": solid(C["page"]), "fontColor": solid(C["sky"])}],
                                 "rowHeaders": [{"backColor": solid(C["page"]), "fontColor": solid(C["text"])}]}},
        },
    }


def write_report(pages):
    shutil.rmtree(REPORT, ignore_errors=True)
    d = os.path.join(REPORT, "definition")
    rr = os.path.join(REPORT, "StaticResources", "RegisteredResources")
    os.makedirs(rr, exist_ok=True)
    write_json(os.path.join(REPORT, ".platform"), {"$schema": SCHEMA["platform"], "metadata": {"type": "Report", "displayName": NAME}, "config": {"version": "2.0", "logicalId": new_id()}})
    write_json(os.path.join(REPORT, "definition.pbir"), {"$schema": SCHEMA["pbir"], "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(os.path.join(d, "version.json"), {"$schema": SCHEMA["version"], "version": "2.0.0"})
    write_json(os.path.join(rr, "TrafficDark.json"), theme())
    images = ["basemap_uk.png", "basemap_india.png"]
    for img in images:
        shutil.copyfile(os.path.join(ASSETS, img), os.path.join(rr, img))
    write_json(os.path.join(d, "report.json"), {
        "$schema": SCHEMA["report"], "layoutOptimization": "None",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55", "type": "SharedResources"},
                            "customTheme": {"name": "TrafficDark.json", "reportVersionAtImport": "5.55", "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "TrafficDark.json", "path": "TrafficDark.json", "type": "CustomTheme"}]
                              + [{"name": i, "path": i, "type": "Image"} for i in images]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True, "useEnhancedTooltips": True,
                     "useDefaultAggregateDisplayName": True}})
    write_json(os.path.join(d, "pages", "pages.json"), {"$schema": SCHEMA["pages"], "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    n = 0
    for p in pages:
        write_json(os.path.join(d, "pages", p.name, "page.json"), {
            "$schema": SCHEMA["page"], "name": p.name, "displayName": p.display, "displayOption": "FitToPage",
            "width": PAGE_W, "height": p.height,
            "objects": {"background": [{"properties": {"color": colour(C["page"]), "transparency": n_(0)}}],
                        "outspace": [{"properties": {"color": colour("#060A14"), "transparency": n_(0)}}]}})
        for v in p.visuals:
            write_json(os.path.join(d, "pages", p.name, "visuals", v["name"], "visual.json"), v)
            n += 1
    write_json(os.path.join(OUT, f"{NAME}.pbip"), {"$schema": SCHEMA["pbip"], "version": "1.0",
                                                    "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                                    "settings": {"enableAutoRecovery": True}})
    write_text(os.path.join(OUT, ".gitignore"), "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    print(f"report: {len(pages)} pages, {n} visuals")


def main():
    tables, uk_segs, in_segs = export_data()
    # Image aspect ratios match the plot areas of the two map visuals on the WHERE? page
    bounds = {"UK": build_basemap(uk_segs, "basemap_uk.png", 1400, 580),
              "India": build_basemap(in_segs, "basemap_india.png", 900, 595)}
    write_model(tables)
    write_report(build_pages(bounds))
    print(f"done -> open {os.path.join(OUT, NAME + '.pbip')} in Power BI Desktop and click Refresh")


if __name__ == "__main__":
    main()
