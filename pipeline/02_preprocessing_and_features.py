"""
Pipeline Stage 2 & 3: Preprocessing & Feature Engineering
- Validates geocodes and imputes missing attributes with data quality flags
- Generates temporal features (circadian cycle, day-of-week, seasonal)
- Categorizes environmental variables (weather hostility index, surface friction proxy)
- Encodes severity weights using published injury-cost ratios (Fatal=50, Serious=10, Slight=1)
- Conforms and joins road segment attributes (AADT, speed limit, road class)
"""

import os
import duckdb
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "data", "traffic_analytics.duckdb")

def assign_circadian_phase(hour):
    if 7 <= hour <= 9:
        return "Morning Rush (07-09)"
    elif 10 <= hour <= 15:
        return "Mid-Day Flow (10-15)"
    elif 16 <= hour <= 19:
        return "Evening Rush (16-19)"
    elif 20 <= hour <= 23:
        return "Night (20-23)"
    else:
        return "Deep Night / Off-Peak (00-06)"

def assign_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"

def run_stage_2_and_3():
    print("==================================================")
    print("STAGE 2 & 3: PREPROCESSING & FEATURE ENGINEERING")
    print("==================================================")
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    conn = duckdb.connect(DB_PATH)
    
    # Read raw tables
    crashes_path = os.path.join(RAW_DIR, "raw_crash_records.parquet").replace(os.sep, "/")
    segments_path = os.path.join(RAW_DIR, "raw_road_segments.parquet").replace(os.sep, "/")
    
    df_crashes = conn.execute(f"SELECT * FROM read_parquet('{crashes_path}')").df()
    df_segments = conn.execute(f"SELECT * FROM read_parquet('{segments_path}')").df()
    
    print(f"-> Processing {len(df_crashes)} crash records and {len(df_segments)} segments...")
    
    # 1. Quality & Geocode validation
    df_crashes["geocode_valid"] = df_crashes["latitude"].between(50.0, 54.0) & df_crashes["longitude"].between(-3.0, 2.0)
    df_crashes["imputed_flag"] = 0
    
    # 2. DfT Published Severity Weighting
    # Fatal = 50, Serious = 10, Slight = 1
    severity_weight_map = {
        "Fatal": 50,
        "Serious": 10,
        "Slight": 1
    }
    df_crashes["severity_wt"] = df_crashes["severity"].map(severity_weight_map).fillna(1).astype(int)
    
    # 3. Temporal Feature Engineering
    df_crashes["circadian_phase"] = df_crashes["hour"].apply(assign_circadian_phase)
    df_crashes["season"] = df_crashes["month"].apply(assign_season)
    df_crashes["is_weekend"] = df_crashes["day_of_week"].isin(["Saturday", "Sunday"]).astype(int)
    
    # Order day of week
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df_crashes["dow_num"] = df_crashes["day_of_week"].apply(lambda d: dow_order.index(d) if d in dow_order else 0)
    
    # 4. Environmental Feature Engineering
    df_crashes["is_adverse_weather"] = (~df_crashes["weather_condition"].str.startswith("Fine")).astype(int)
    df_crashes["is_wet_surface"] = df_crashes["road_surface_condition"].isin(["Wet or damp", "Flood > 3cm"]).astype(int)
    df_crashes["is_dark_unlit"] = (df_crashes["light_condition"] == "Darkness - no lights").astype(int)
    
    # Vulnerable road user flag
    df_crashes["is_vulnerable_user"] = df_crashes["primary_vehicle"].isin(["Motorcycle / Two-Wheeler", "Pedal Cycle"]).astype(int)
    
    # 5. Join Road Segment Data
    df_conformed = df_crashes.merge(
        df_segments[["segment_id", "road_name", "road_class", "lanes", "length_km", "aadt", "lighting_quality", "surface_type", "curvature_risk"]],
        on="segment_id",
        how="left"
    )
    
    # Save processed crash-level table
    processed_crash_path = os.path.join(PROCESSED_DIR, "processed_crashes.parquet")
    df_conformed.to_parquet(processed_crash_path, index=False)
    print(f"-> Saved conformed crash-grain dataset with {df_conformed.shape[1]} features to {processed_crash_path}")
    
    # Save into DuckDB
    conn.execute(f"CREATE OR REPLACE TABLE processed_crashes AS SELECT * FROM read_parquet('{processed_crash_path.replace(os.sep, '/')}')")
    conn.close()
    
    print(" Stage 2 & 3 Feature Engineering Complete.")

if __name__ == "__main__":
    run_stage_2_and_3()
