#!/usr/bin/env bash
echo "======================================================================="
echo "TRAFFIC ACCIDENT ANALYSIS & VISUALIZATION (Review 1 Prototype)"
echo "======================================================================="
echo ""

echo "[1/3] Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install requirements."
    exit 1
fi
echo ""

echo "[2/3] Running Data Pipeline..."
python run_pipeline.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Pipeline execution failed."
    exit 1
fi
echo ""

echo "[3/3] Launching Streamlit Dashboard..."
python -m streamlit run app.py
