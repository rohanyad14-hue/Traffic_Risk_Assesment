@echo off
title Traffic Accident Analysis & Visualization
echo =======================================================================
echo TRAFFIC ACCIDENT ANALYSIS & VISUALIZATION (Review 1 Prototype)
echo =======================================================================
echo.

echo [1/3] Checking and installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements. Please ensure Python is installed and added to PATH.
    pause
    exit /b %errorlevel%
)
echo.

echo [2/3] Running Data Pipeline (Batch Ingest, Exposure Modeling, Cubes)...
python run_pipeline.py
if %errorlevel% neq 0 (
    echo [ERROR] Pipeline failed.
    pause
    exit /b %errorlevel%
)
echo.

echo [3/3] Launching Interactive Visual Analytics Dashboard...
echo Opening in default browser at http://localhost:8501
python -m streamlit run app.py
pause
