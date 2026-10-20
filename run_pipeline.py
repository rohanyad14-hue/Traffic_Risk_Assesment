"""
Master Pipeline Orchestrator
Executes the reproducible batch pipeline in sequence:
Stage 1: Data Ingestion & Network Synthesis (Python + Parquet + DuckDB)
Stage 2 & 3: Preprocessing & Feature Engineering (DfT Severity Weights, Circadian Slots)
Stage 4: Exposure Calculation & Severity Risk Modeling (Grain shift to Road Segment)
Stage 5 & 6: Pre-aggregating Visual Analytics Cubes via DuckDB & ML Hotspot Modeling
"""

import sys
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import importlib

stage1 = importlib.import_module("pipeline.01_data_generation_and_ingest")
stage2 = importlib.import_module("pipeline.02_preprocessing_and_features")
stage3 = importlib.import_module("pipeline.03_exposure_and_risk_modeling")
stage4 = importlib.import_module("pipeline.04_aggregate_cubes_duckdb")

def run_all():
    print("================================================================================")
    print("TRAFFIC ACCIDENT ANALYSIS & VISUALIZATION PIPELINE")
    print("Visual Analytics Lab — Review 1 Prototype")
    print("Authors: Saranya Dalal [26MML0007], Divya Pujari [26MML0009], Rohan Yadav [26MML0020]")
    print("Guide: Dr Manikandan K (SCOPE)")
    print("================================================================================")
    start_total = time.time()
    
    t0 = time.time()
    stage1.run_stage_1()
    print(f"Stage 1 finished in {time.time() - t0:.2f}s\n")
    
    t1 = time.time()
    stage2.run_stage_2_and_3()
    print(f"Stage 2 & 3 finished in {time.time() - t1:.2f}s\n")
    
    t2 = time.time()
    stage3.run_stage_4()
    print(f"Stage 4 finished in {time.time() - t2:.2f}s\n")
    
    t3 = time.time()
    stage4.run_stage_5_and_6()
    print(f"Stage 5 & 6 finished in {time.time() - t3:.2f}s\n")
    
    elapsed = time.time() - start_total
    print("================================================================================")
    print(f"PIPELINE RUN COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS!")
    print("All Parquet cubes, GeoJSON features, and DuckDB storage are pre-aggregated.")
    print("Ready to launch interactive visual analytics dashboard via: streamlit run app.py")
    print("================================================================================")

if __name__ == "__main__":
    run_all()
