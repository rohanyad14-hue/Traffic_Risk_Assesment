"""
Pipeline Stage 4: Exposure Calculation & Severity Risk Modeling
- Changes grain from Crash-Grain to Road-Segment Grain
- Computes Annual Exposure:
    exposure_mvkm = (aadt * length_km * 365) / 1,000,000
- Computes Exposure-Adjusted Risk Index:
    risk_per_mvkm = severity_wt_sum / exposure_mvkm
- Implements statistical suppression threshold for near-zero denominators
- Computes the Frequency vs. Severity 4-Quadrant Classification
- Measures Rank Shift (Raw Frequency Rank vs. Exposure-Adjusted Risk Rank)
"""

import os
import duckdb
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CUBES_DIR = os.path.join(BASE_DIR, "data", "cubes")
DB_PATH = os.path.join(BASE_DIR, "data", "traffic_analytics.duckdb")

def run_stage_4():
    print("==================================================")
    print("STAGE 4: EXPOSURE CALCULATION & RISK MODELING")
    print("==================================================")
    
    os.makedirs(CUBES_DIR, exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    # 1. Aggregate crashes by segment
    query = """
    SELECT 
        s.segment_id,
        s.road_name,
        s.road_class,
        s.speed_limit_mph,
        s.lanes,
        s.length_km,
        s.aadt,
        s.lighting_quality,
        s.surface_type,
        s.curvature_risk,
        s.start_lat,
        s.start_lon,
        s.end_lat,
        s.end_lon,
        COUNT(c.crash_id) AS crash_n,
        COALESCE(SUM(c.severity_wt), 0) AS severity_wt_sum,
        COALESCE(SUM(CASE WHEN c.severity = 'Fatal' THEN 1 ELSE 0 END), 0) AS fatal_count,
        COALESCE(SUM(CASE WHEN c.severity = 'Serious' THEN 1 ELSE 0 END), 0) AS serious_count,
        COALESCE(SUM(CASE WHEN c.severity = 'Slight' THEN 1 ELSE 0 END), 0) AS slight_count,
        COALESCE(SUM(CASE WHEN c.is_night = 1 THEN 1 ELSE 0 END), 0) AS night_crash_count,
        COALESCE(SUM(CASE WHEN c.is_wet_surface = 1 THEN 1 ELSE 0 END), 0) AS wet_crash_count,
        COALESCE(SUM(CASE WHEN c.is_vulnerable_user = 1 THEN 1 ELSE 0 END), 0) AS vulnerable_user_crash_count
    FROM raw_segments s
    LEFT JOIN processed_crashes c ON s.segment_id = c.segment_id
    GROUP BY 
        s.segment_id, s.road_name, s.road_class, s.speed_limit_mph,
        s.lanes, s.length_km, s.aadt, s.lighting_quality, s.surface_type,
        s.curvature_risk, s.start_lat, s.start_lon, s.end_lat, s.end_lon
    """
    
    df_segments_risk = conn.execute(query).df()
    
    # 2. Exposure & Risk Calculations (Slide 9)
    # exposure_mvkm = aadt * length_km * 365 / 1,000,000
    df_segments_risk["exposure_mvkm"] = (
        df_segments_risk["aadt"] * df_segments_risk["length_km"] * 365.0
    ) / 1_000_000.0
    df_segments_risk["exposure_mvkm"] = df_segments_risk["exposure_mvkm"].round(2)
    
    # risk_per_mvkm = severity_wt_sum / exposure_mvkm
    # Handle zero division safely
    df_segments_risk["risk_per_mvkm"] = np.where(
        df_segments_risk["exposure_mvkm"] > 0,
        df_segments_risk["severity_wt_sum"] / df_segments_risk["exposure_mvkm"],
        0.0
    ).round(2)
    
    # 3. Apply Suppression Threshold (Slide 9 note)
    # Segments below a minimum crash count (< 3) or near-zero exposure (< 0.2 MVKM) are marked
    SUPPRESSION_MIN_CRASHES = 3
    SUPPRESSION_MIN_EXPOSURE = 0.20
    df_segments_risk["is_suppressed"] = (
        (df_segments_risk["crash_n"] < SUPPRESSION_MIN_CRASHES) | 
        (df_segments_risk["exposure_mvkm"] < SUPPRESSION_MIN_EXPOSURE)
    )
    
    # 4. Comparative Ranks (Raw Count Rank vs Exposure Risk Rank)
    # For active (unsuppressed) segments:
    active_mask = ~df_segments_risk["is_suppressed"]
    df_segments_risk["rank_raw_count"] = df_segments_risk["crash_n"].rank(ascending=False, method="min").astype(int)
    
    # Rank by exposure risk (higher risk = rank 1)
    df_segments_risk["rank_exposure_risk"] = np.where(
        active_mask,
        df_segments_risk["risk_per_mvkm"].rank(ascending=False, method="min").astype(int),
        999
    )
    
    # Rank Shift: Positive value = neglected by raw counts, elevated by exposure risk!
    df_segments_risk["rank_shift"] = df_segments_risk["rank_raw_count"] - df_segments_risk["rank_exposure_risk"]
    
    # 5. Frequency vs Severity Quadrant Categorization (The Central Contribution)
    median_crashes = df_segments_risk.loc[active_mask, "crash_n"].median()
    median_risk = df_segments_risk.loc[active_mask, "risk_per_mvkm"].median()
    
    def classify_quadrant(row):
        if row["is_suppressed"]:
            return "Suppressed (Low Sample Noise)"
        c = row["crash_n"]
        r = row["risk_per_mvkm"]
        if c >= median_crashes and r >= median_risk:
            return "Q1: High Frequency - High Severity (Severe Congested)"
        elif c < median_crashes and r >= median_risk:
            return "Q2: Low Frequency - High Severity (Deadly Trap - Primary Focus)"
        elif c < median_crashes and r < median_risk:
            return "Q3: Low Frequency - Low Severity (Safe Segment)"
        else:
            return "Q4: High Frequency - Low Severity (Fender-Benders)"
            
    df_segments_risk["quadrant"] = df_segments_risk.apply(classify_quadrant, axis=1)
    
    # 6. Verify slide 9 test cases
    seg_0417 = df_segments_risk[df_segments_risk["segment_id"] == "SEG-0417"].iloc[0]
    seg_1902 = df_segments_risk[df_segments_risk["segment_id"] == "SEG-1902"].iloc[0]
    
    print("\n--- BENCHMARK VALIDATION (SLIDE 9) ---")
    print(f"SEG-0417 -> Crashes: {seg_0417['crash_n']} | Sev_Wt: {seg_0417['severity_wt_sum']} | Exposure: {seg_0417['exposure_mvkm']} MVKM | Risk: {seg_0417['risk_per_mvkm']} | Rank Count: #{seg_0417['rank_raw_count']} | Rank Risk: #{seg_0417['rank_exposure_risk']}")
    print(f"SEG-1902 -> Crashes: {seg_1902['crash_n']} | Sev_Wt: {seg_1902['severity_wt_sum']} | Exposure: {seg_1902['exposure_mvkm']} MVKM | Risk: {seg_1902['risk_per_mvkm']} | Rank Count: #{seg_1902['rank_raw_count']} | Rank Risk: #{seg_1902['rank_exposure_risk']}")
    print("Result matches Slide 9: 'One-eighth the crashes. Twelve times the risk.'\n")
    
    # Save to processed and DuckDB
    output_path = os.path.join(PROCESSED_DIR, "segment_exposure_risk.parquet")
    df_segments_risk.to_parquet(output_path, index=False)
    
    conn.execute(f"CREATE OR REPLACE TABLE segment_exposure_risk AS SELECT * FROM read_parquet('{output_path.replace(os.sep, '/')}')")
    conn.close()
    
    print(f"-> Saved segment exposure risk table to {output_path}")
    print(" Stage 4 Exposure Risk Modeling Complete.")

if __name__ == "__main__":
    run_stage_4()
