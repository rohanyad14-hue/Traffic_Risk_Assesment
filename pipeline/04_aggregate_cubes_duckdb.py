"""
Pipeline Stage 5 & 6: Pre-aggregating Visual Analytics Cubes via DuckDB
- Computes multi-dimensional cubes for instant browser dashboard interactivity
- Exports:
    1. cube_temporal_heatmap.parquet (Hour x Day-of-Week matrix)
    2. cube_circadian_hourly.parquet (24-Hour circadian severity rate)
    3. cube_environmental_matrix.parquet (Weather x Surface x Lighting interactions)
    4. cube_vehicle_vulnerability.parquet (Vehicle type x Severity x Speed limit)
    5. cube_segments_spatial.geojson & .parquet (Spatial segment layer with exposure & risk)
    6. cube_quadrants_summary.parquet (Frequency vs Severity 4-quadrant metrics)
    7. cube_india_transferability.parquet (Indian urban corridor transferability case)
    8. cube_ml_risk_weights.json (Trained classifier feature importances)
"""

import os
import json
import duckdb
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
CUBES_DIR = os.path.join(BASE_DIR, "data", "cubes")
DB_PATH = os.path.join(BASE_DIR, "data", "traffic_analytics.duckdb")

def build_india_context_cubes(conn):
    """
    Builds India (Bengaluru) cubes that mirror the UK cube schemas, so the dashboard's
    'Study Context' switch can re-point every module at the India data.
    Exports:
        cube_india_segments_spatial.parquet   (same columns as cube_segments_spatial where available)
        cube_india_temporal_heatmap.parquet   (Day x Hour)
        cube_india_circadian_hourly.parquet   (24-hour profile)
        cube_india_vehicle_vulnerability.parquet (Vehicle x Road class; India data has no speed limits)
        cube_india_quadrants_summary.parquet  (4-quadrant summary)
    The India feed carries no weather / surface / lighting fields, so there is no India environmental cube.
    """
    print("-> Building India Study-Context Cubes (segments, temporal, circadian, vehicle, quadrants)...")
    segs_path = os.path.join(BASE_DIR, "data", "raw", "raw_india_segments.parquet").replace(os.sep, "/")
    crashes_path = os.path.join(BASE_DIR, "data", "raw", "raw_india_crashes.parquet").replace(os.sep, "/")

    conn.execute(f"""
    CREATE OR REPLACE TEMP VIEW india_crashes AS
    SELECT
        c.*,
        CASE c.day_of_week
            WHEN 'Mon' THEN 'Monday' WHEN 'Tue' THEN 'Tuesday' WHEN 'Wed' THEN 'Wednesday'
            WHEN 'Thu' THEN 'Thursday' WHEN 'Fri' THEN 'Friday' WHEN 'Sat' THEN 'Saturday'
            ELSE 'Sunday' END AS day_name,
        CASE c.day_of_week
            WHEN 'Mon' THEN 0 WHEN 'Tue' THEN 1 WHEN 'Wed' THEN 2 WHEN 'Thu' THEN 3
            WHEN 'Fri' THEN 4 WHEN 'Sat' THEN 5 ELSE 6 END AS dow_num,
        CASE c.severity WHEN 'Fatal' THEN 50 WHEN 'Serious' THEN 10 ELSE 1 END AS severity_wt,
        CASE WHEN c.primary_vehicle IN ('Two-Wheeler', 'Pedestrian') THEN 1 ELSE 0 END AS is_vulnerable_user
    FROM read_parquet('{crashes_path}') c
    """)

    # Segment grain: exposure, risk, suppression, ranks and quadrants (same rules as Stage 4)
    df_seg = conn.execute(f"""
    SELECT
        s.segment_id, s.road_name, s.road_class, s.length_km, s.aadt, s.two_wheeler_pct,
        s.start_lat, s.start_lon, s.end_lat, s.end_lon,
        COUNT(c.crash_id) AS crash_n,
        COALESCE(SUM(c.severity_wt), 0) AS severity_wt_sum,
        COALESCE(SUM(CASE WHEN c.severity = 'Fatal' THEN 1 ELSE 0 END), 0) AS fatal_count,
        COALESCE(SUM(CASE WHEN c.severity = 'Serious' THEN 1 ELSE 0 END), 0) AS serious_count,
        COALESCE(SUM(CASE WHEN c.severity = 'Slight' THEN 1 ELSE 0 END), 0) AS slight_count,
        COALESCE(SUM(c.is_night), 0) AS night_crash_count,
        COALESCE(SUM(c.is_vulnerable_user), 0) AS vulnerable_user_crash_count
    FROM read_parquet('{segs_path}') s
    LEFT JOIN india_crashes c ON s.segment_id = c.segment_id
    GROUP BY ALL
    ORDER BY s.segment_id
    """).df()

    df_seg["exposure_mvkm"] = (df_seg["aadt"] * df_seg["length_km"] * 365.0 / 1_000_000.0).round(2)
    df_seg["risk_per_mvkm"] = np.where(
        df_seg["exposure_mvkm"] > 0, df_seg["severity_wt_sum"] / df_seg["exposure_mvkm"], 0.0
    ).round(2)
    df_seg["is_suppressed"] = (df_seg["crash_n"] < 3) | (df_seg["exposure_mvkm"] < 0.20)
    active = ~df_seg["is_suppressed"]
    df_seg["rank_raw_count"] = df_seg["crash_n"].rank(ascending=False, method="min").astype(int)
    df_seg["rank_exposure_risk"] = np.where(
        active, df_seg["risk_per_mvkm"].rank(ascending=False, method="min").astype(int), 999
    )
    df_seg["rank_shift"] = df_seg["rank_raw_count"] - df_seg["rank_exposure_risk"]

    med_c = df_seg.loc[active, "crash_n"].median()
    med_r = df_seg.loc[active, "risk_per_mvkm"].median()

    def classify(row):
        if row["is_suppressed"]:
            return "Suppressed (Low Sample Noise)"
        hi_c, hi_r = row["crash_n"] >= med_c, row["risk_per_mvkm"] >= med_r
        if hi_c and hi_r:
            return "Q1: High Frequency - High Severity (Severe Congested)"
        if hi_r:
            return "Q2: Low Frequency - High Severity (Deadly Trap - Primary Focus)"
        if not hi_c:
            return "Q3: Low Frequency - Low Severity (Safe Segment)"
        return "Q4: High Frequency - Low Severity (Fender-Benders)"

    df_seg["quadrant"] = df_seg.apply(classify, axis=1)
    df_seg.to_parquet(os.path.join(CUBES_DIR, "cube_india_segments_spatial.parquet"), index=False)

    conn.register("india_segs_df", df_seg)
    conn.execute("""
    SELECT
        quadrant,
        COUNT(*) AS segment_count,
        SUM(crash_n) AS total_crashes,
        SUM(fatal_count) AS total_fatalities,
        SUM(serious_count) AS total_serious_injuries,
        ROUND(AVG(exposure_mvkm), 2) AS mean_exposure_mvkm,
        ROUND(AVG(risk_per_mvkm), 2) AS mean_risk_per_mvkm,
        ROUND(SUM(fatal_count) * 100.0 / NULLIF(SUM(crash_n), 0), 2) AS fatality_share_pct
    FROM india_segs_df
    GROUP BY quadrant
    ORDER BY mean_risk_per_mvkm DESC
    """).df().to_parquet(os.path.join(CUBES_DIR, "cube_india_quadrants_summary.parquet"), index=False)
    conn.unregister("india_segs_df")

    conn.execute("""
    SELECT
        day_name AS day_of_week, dow_num, hour,
        COUNT(*) AS total_crashes,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_crashes,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_crashes,
        SUM(CASE WHEN severity = 'Slight' THEN 1 ELSE 0 END) AS slight_crashes,
        ROUND(AVG(severity_wt), 2) AS avg_severity_weight,
        ROUND(SUM(CASE WHEN severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_rate_pct
    FROM india_crashes
    GROUP BY day_name, dow_num, hour
    ORDER BY dow_num, hour
    """).df().to_parquet(os.path.join(CUBES_DIR, "cube_india_temporal_heatmap.parquet"), index=False)

    conn.execute("""
    SELECT
        hour,
        COUNT(*) AS crash_count,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_count,
        ROUND(AVG(severity_wt), 2) AS mean_severity_wt,
        ROUND(SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fatality_rate_pct,
        ROUND(SUM(is_vulnerable_user) * 100.0 / COUNT(*), 2) AS vulnerable_pct
    FROM india_crashes
    GROUP BY hour
    ORDER BY hour
    """).df().to_parquet(os.path.join(CUBES_DIR, "cube_india_circadian_hourly.parquet"), index=False)

    conn.execute(f"""
    SELECT
        c.primary_vehicle,
        s.road_class,
        COUNT(*) AS crash_count,
        SUM(CASE WHEN c.severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN c.severity = 'Serious' THEN 1 ELSE 0 END) AS serious_count,
        ROUND(SUM(CASE WHEN c.severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_rate_pct,
        ROUND(AVG(c.severity_wt), 2) AS avg_severity_wt
    FROM india_crashes c
    JOIN read_parquet('{segs_path}') s ON s.segment_id = c.segment_id
    GROUP BY c.primary_vehicle, s.road_class
    ORDER BY c.primary_vehicle, s.road_class
    """).df().to_parquet(os.path.join(CUBES_DIR, "cube_india_vehicle_vulnerability.parquet"), index=False)


def run_stage_5_and_6():
    print("==================================================")
    print("STAGE 5 & 6: AGGREGATE CUBES VIA DUCKDB & ML")
    print("==================================================")
    
    os.makedirs(CUBES_DIR, exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    # 1. Cube 1: Temporal Heatmap (Day of Week x Hour)
    print("-> Building Temporal Cube (Day x Hour)...")
    q_temporal = """
    SELECT 
        day_of_week,
        dow_num,
        hour,
        COUNT(*) AS total_crashes,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_crashes,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_crashes,
        SUM(CASE WHEN severity = 'Slight' THEN 1 ELSE 0 END) AS slight_crashes,
        ROUND(AVG(severity_wt), 2) AS avg_severity_weight,
        ROUND(SUM(CASE WHEN severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_rate_pct
    FROM processed_crashes
    GROUP BY day_of_week, dow_num, hour
    ORDER BY dow_num, hour
    """
    df_temporal = conn.execute(q_temporal).df()
    df_temporal.to_parquet(os.path.join(CUBES_DIR, "cube_temporal_heatmap.parquet"), index=False)
    
    # 2. Cube 2: 24-Hour Circadian Profile
    print("-> Building Circadian Profile Cube...")
    q_circadian = """
    SELECT 
        hour,
        COUNT(*) AS crash_count,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_count,
        ROUND(AVG(severity_wt), 2) AS mean_severity_wt,
        ROUND(SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fatality_rate_pct,
        ROUND(SUM(is_vulnerable_user) * 100.0 / COUNT(*), 2) AS vulnerable_pct
    FROM processed_crashes
    GROUP BY hour
    ORDER BY hour
    """
    df_circadian = conn.execute(q_circadian).df()
    df_circadian.to_parquet(os.path.join(CUBES_DIR, "cube_circadian_hourly.parquet"), index=False)
    
    # 3. Cube 3: Environmental Matrix (Weather x Surface x Light)
    print("-> Building Environmental Interaction Cube...")
    q_env = """
    SELECT 
        weather_condition,
        road_surface_condition,
        light_condition,
        COUNT(*) AS crash_volume,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_count,
        ROUND(AVG(severity_wt), 2) AS mean_severity_wt,
        ROUND(SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fatality_rate_pct,
        ROUND(SUM(CASE WHEN severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_outcome_pct
    FROM processed_crashes
    GROUP BY weather_condition, road_surface_condition, light_condition
    ORDER BY severe_outcome_pct DESC
    """
    df_env = conn.execute(q_env).df()
    df_env.to_parquet(os.path.join(CUBES_DIR, "cube_environmental_matrix.parquet"), index=False)
    
    # 4. Cube 4: Vehicle Vulnerability & Speed Limits
    print("-> Building Vehicle & Speed Limit Vulnerability Cube...")
    q_veh = """
    SELECT 
        primary_vehicle,
        speed_limit_mph,
        COUNT(*) AS crash_count,
        SUM(CASE WHEN severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN severity = 'Serious' THEN 1 ELSE 0 END) AS serious_count,
        ROUND(SUM(CASE WHEN severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_rate_pct,
        ROUND(AVG(severity_wt), 2) AS avg_severity_wt
    FROM processed_crashes
    GROUP BY primary_vehicle, speed_limit_mph
    ORDER BY primary_vehicle, speed_limit_mph
    """
    df_veh = conn.execute(q_veh).df()
    df_veh.to_parquet(os.path.join(CUBES_DIR, "cube_vehicle_vulnerability.parquet"), index=False)
    
    # 5. Cube 5: Spatial Segments GeoJSON and Table
    print("-> Building Spatial Segments GeoJSON & Parquet Cube...")
    df_segs = conn.execute("SELECT * FROM segment_exposure_risk").df()
    df_segs.to_parquet(os.path.join(CUBES_DIR, "cube_segments_spatial.parquet"), index=False)
    
    # Build GeoJSON feature collection for 3D/Map display
    features = []
    for _, row in df_segs.iterrows():
        coords = [
            [row["start_lon"], row["start_lat"]],
            [row["end_lon"], row["end_lat"]]
        ]
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            },
            "properties": {
                "segment_id": row["segment_id"],
                "road_name": row["road_name"],
                "road_class": row["road_class"],
                "speed_limit_mph": int(row["speed_limit_mph"]),
                "aadt": int(row["aadt"]),
                "exposure_mvkm": float(row["exposure_mvkm"]),
                "crash_n": int(row["crash_n"]),
                "severity_wt_sum": int(row["severity_wt_sum"]),
                "risk_per_mvkm": float(row["risk_per_mvkm"]),
                "quadrant": str(row["quadrant"]),
                "rank_raw_count": int(row["rank_raw_count"]),
                "rank_exposure_risk": int(row["rank_exposure_risk"]),
                "rank_shift": int(row["rank_shift"]),
                "lighting_quality": str(row["lighting_quality"]),
                "curvature_risk": str(row["curvature_risk"]),
                "is_benchmark": bool(row["segment_id"] in ["SEG-0417", "SEG-1902"])
            }
        }
        features.append(feat)
        
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(os.path.join(CUBES_DIR, "cube_segments.geojson"), "w") as f:
        json.dump(geojson_data, f)
        
    # 6. Cube 6: Quadrants Summary
    print("-> Building Frequency vs Severity Quadrants Summary...")
    q_quad = """
    SELECT 
        quadrant,
        COUNT(*) AS segment_count,
        SUM(crash_n) AS total_crashes,
        SUM(fatal_count) AS total_fatalities,
        SUM(serious_count) AS total_serious_injuries,
        ROUND(AVG(exposure_mvkm), 2) AS mean_exposure_mvkm,
        ROUND(AVG(risk_per_mvkm), 2) AS mean_risk_per_mvkm,
        ROUND(SUM(fatal_count) * 100.0 / NULLIF(SUM(crash_n), 0), 2) AS fatality_share_pct
    FROM segment_exposure_risk
    GROUP BY quadrant
    ORDER BY mean_risk_per_mvkm DESC
    """
    df_quad = conn.execute(q_quad).df()
    df_quad.to_parquet(os.path.join(CUBES_DIR, "cube_quadrants_summary.parquet"), index=False)
    
    # 7. Cube 7: Indian City Transferability Case (Slide 7)
    print("-> Building Indian City Transferability Cube...")
    raw_ind_segs_path = os.path.join(BASE_DIR, "data", "raw", "raw_india_segments.parquet").replace(os.sep, "/")
    raw_ind_crashes_path = os.path.join(BASE_DIR, "data", "raw", "raw_india_crashes.parquet").replace(os.sep, "/")
    
    q_india = f"""
    WITH ind_agg AS (
        SELECT 
            c.segment_id,
            COUNT(*) AS crash_n,
            SUM(CASE WHEN c.severity = 'Fatal' THEN 50 WHEN c.severity = 'Serious' THEN 10 ELSE 1 END) AS severity_wt_sum,
            SUM(CASE WHEN c.severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_count,
            SUM(CASE WHEN c.primary_vehicle IN ('Two-Wheeler', 'Pedestrian') THEN 1 ELSE 0 END) AS vrus_crash_count
        FROM read_parquet('{raw_ind_crashes_path}') c
        GROUP BY c.segment_id
    )
    SELECT 
        s.segment_id,
        s.road_name,
        s.road_class,
        s.length_km,
        s.aadt,
        s.two_wheeler_pct,
        s.start_lat,
        s.start_lon,
        s.end_lat,
        s.end_lon,
        a.crash_n,
        a.fatal_count,
        a.vrus_crash_count,
        ROUND((s.aadt * s.length_km * 365.0) / 1000000.0, 2) AS exposure_mvkm,
        ROUND(a.severity_wt_sum / ((s.aadt * s.length_km * 365.0) / 1000000.0), 2) AS risk_per_mvkm
    FROM read_parquet('{raw_ind_segs_path}') s
    LEFT JOIN ind_agg a ON s.segment_id = a.segment_id
    """
    df_india = conn.execute(q_india).df()
    df_india.to_parquet(os.path.join(CUBES_DIR, "cube_india_transferability.parquet"), index=False)
    
    # 7b. India study-context cubes (same schema as the UK cubes so the dashboard can switch context)
    build_india_context_cubes(conn)
    
    # 8. Train ML Hotspot & Severity Predictor (matching literature review on slide 4)
    print("-> Training ML Severity Risk Classifier (Random Forest / SHAP-Proxy)...")
    df_model_data = conn.execute("""
    SELECT 
        severity,
        speed_limit_mph,
        is_night,
        is_weekend,
        is_adverse_weather,
        is_wet_surface,
        is_dark_unlit,
        is_vulnerable_user,
        lanes,
        aadt,
        length_km
    FROM processed_crashes
    """).df()
    
    # Target: High Severity (Fatal or Serious = 1, Slight = 0)
    y = (df_model_data["severity"].isin(["Fatal", "Serious"])).astype(int)
    X = df_model_data.drop(columns=["severity"])
    
    clf = RandomForestClassifier(n_estimators=60, max_depth=8, random_state=42)
    clf.fit(X, y)
    
    importances = dict(zip(X.columns, [round(float(imp), 4) for imp in clf.feature_importances_]))
    # Sort descending
    importances_sorted = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    
    ml_report = {
        "model_type": "RandomForest Hotspot Severity Classifier",
        "training_samples": len(X),
        "target_balance_severe_pct": round(float(y.mean() * 100), 2),
        "feature_importances": importances_sorted,
        "features": list(X.columns)
    }
    
    with open(os.path.join(CUBES_DIR, "cube_ml_risk_weights.json"), "w") as f:
        json.dump(ml_report, f, indent=2)
        
    conn.close()
    print(" Stage 5 & 6 Cube Pre-aggregation Complete.")

if __name__ == "__main__":
    run_stage_5_and_6()
