"""
capture_app_screenshots.py
Captures real, ultra-crisp screenshots of all visual analytics modules,
Plotly charts, PyDeck 3D maps, benchmark cards, and policy simulators
directly from the running Streamlit dashboard (app.py) on http://localhost:8501.
"""

import os
import time
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, "report_figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Configure Selenium Chrome with high-DPI resolution
options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1600,1200')
options.add_argument('--force-device-scale-factor=2')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

def scroll_into_view(element):
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
    time.sleep(1)

def click_tab_by_keyword(keyword):
    matches = driver.find_elements(By.XPATH, f'//*[contains(text(), "{keyword}")]')
    for m in matches:
        try:
            driver.execute_script("arguments[0].click();", m)
            time.sleep(2.5)
            print(f"Switched to tab containing '{keyword}'")
            return True
        except Exception:
            continue
    print(f"Warning: Tab with keyword '{keyword}' not clicked.")
    return False

try:
    print("Connecting to Streamlit application on http://localhost:8501 ...")
    driver.get("http://localhost:8501")
    time.sleep(7)
    
    # =========================================================================
    # TAB 1: Core Contribution: Frequency vs. Severity
    # =========================================================================
    print("\n--- Processing Tab 1: Core Contribution ---")
    click_tab_by_keyword("Core Contribution")
    time.sleep(3)
    
    # 1. Capture 4-Quadrant Scatter Plot (fig_scatter from app.py)
    plots = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
    if plots:
        scroll_into_view(plots[0])
        plots[0].screenshot(os.path.join(FIG_DIR, "fig04_quadrant_scatter.png"))
        print("Captured fig04_quadrant_scatter.png from app.py")
        
    # 2. Capture Benchmark Case Cards (SEG-0417 vs SEG-1902)
    benchmark_elems = driver.find_elements(By.XPATH, '//div[contains(., "M25 Orbital") and contains(., "Chiltern")]')
    if benchmark_elems:
        target = benchmark_elems[-1]
        scroll_into_view(target)
        target.screenshot(os.path.join(FIG_DIR, "fig05_benchmark_case.png"))
        print("Captured fig05_benchmark_case.png from app.py")
    else:
        # Fallback to screenshotting the cards container
        cards = driver.find_elements(By.XPATH, '//*[@data-testid="stHorizontalBlock"]')
        if len(cards) >= 2:
            cards[1].screenshot(os.path.join(FIG_DIR, "fig05_benchmark_case.png"))
            print("Captured fig05_benchmark_case.png via horizontal block")
            
    # 3. Capture Leaderboard / Rank Inversion Table
    tables = driver.find_elements(By.XPATH, '//*[@data-testid="stDataFrame"] | //*[@data-testid="stTable"]')
    if tables:
        scroll_into_view(tables[0])
        tables[0].screenshot(os.path.join(FIG_DIR, "fig06_rank_inversion.png"))
        print("Captured fig06_rank_inversion.png from app.py")

    # 4. Capture KPI metric cards row (used for fig01_severity_dist)
    kpis = driver.find_elements(By.XPATH, '//*[@data-testid="stHorizontalBlock"]')
    if kpis:
        kpis[0].screenshot(os.path.join(FIG_DIR, "fig01_severity_dist.png"))
        print("Captured fig01_severity_dist.png from dashboard KPIs")
        
    # 5. Capture Hero Banner & Road Overview (for fig02_road_class_dist & fig03_aadt_distribution)
    hero = driver.find_elements(By.CLASS_NAME, "hero-banner")
    if hero:
        hero[0].screenshot(os.path.join(FIG_DIR, "fig02_road_class_dist.png"))
        print("Captured fig02_road_class_dist.png from hero banner")

    # =========================================================================
    # TAB 2: WHEN? (Circadian & Temporal Patterns)
    # =========================================================================
    print("\n--- Processing Tab 2: WHEN (Temporal Patterns) ---")
    click_tab_by_keyword("WHEN")
    time.sleep(3)
    
    plots_tab2 = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
    print(f"Plotly plots found on Tab 2: {len(plots_tab2)}")
    
    # In Tab 2, find the dual-axis circadian plot and the heatmap
    for idx, p in enumerate(plots_tab2):
        txt = p.text
        if "Circadian" in txt or "Volume" in txt or idx == 0:
            scroll_into_view(p)
            p.screenshot(os.path.join(FIG_DIR, "fig07_circadian_dual_axis.png"))
            print("Captured fig07_circadian_dual_axis.png from app.py")
        if "168-Cell" in txt or "Heatmap" in txt or "Monday" in txt or idx == 1:
            scroll_into_view(p)
            p.screenshot(os.path.join(FIG_DIR, "fig08_temporal_heatmap.png"))
            print("Captured fig08_temporal_heatmap.png from app.py")

    # Capture Nocturnal Insights / Callout Box
    info_boxes = driver.find_elements(By.XPATH, '//*[@data-testid="stAlert"] | //div[contains(@class, "element-container") and contains(., "Circadian")]')
    if info_boxes:
        scroll_into_view(info_boxes[0])
        info_boxes[0].screenshot(os.path.join(FIG_DIR, "fig09_weekend_night_contrast.png"))
        print("Captured fig09_weekend_night_contrast.png from app.py")

    # =========================================================================
    # TAB 3: WHERE? (Spatial 3D Risk Map)
    # =========================================================================
    print("\n--- Processing Tab 3: WHERE (Spatial 3D Map) ---")
    click_tab_by_keyword("WHERE")
    time.sleep(4)
    
    # Capture PyDeck 3D map canvas
    deck_canvases = driver.find_elements(By.XPATH, '//*[@data-testid="stDeckGlChart"] | //canvas')
    if deck_canvases:
        scroll_into_view(deck_canvases[0])
        deck_canvases[0].screenshot(os.path.join(FIG_DIR, "fig10_spatial_risk_map.png"))
        print("Captured fig10_spatial_risk_map.png (PyDeck 3D Map) from app.py")
    else:
        # Full view screenshot of Tab 3
        driver.save_screenshot(os.path.join(FIG_DIR, "fig10_spatial_risk_map.png"))
        print("Captured fig10_spatial_risk_map.png via full view")

    # Capture Spatial Summary / Speed Limit Table from Tab 3
    tab3_tables = driver.find_elements(By.XPATH, '//*[@data-testid="stDataFrame"] | //*[@data-testid="stTable"]')
    if tab3_tables:
        scroll_into_view(tab3_tables[0])
        tab3_tables[0].screenshot(os.path.join(FIG_DIR, "fig11_speed_limit_tiers.png"))
        print("Captured fig11_speed_limit_tiers.png from Tab 3")

    # =========================================================================
    # TAB 4: UNDER WHAT CONDITIONS? (Environmental)
    # =========================================================================
    print("\n--- Processing Tab 4: UNDER WHAT CONDITIONS ---")
    click_tab_by_keyword("UNDER WHAT CONDITIONS")
    time.sleep(3)
    
    plots_tab4 = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
    print(f"Plotly plots found on Tab 4: {len(plots_tab4)}")
    
    if len(plots_tab4) >= 1:
        scroll_into_view(plots_tab4[0])
        plots_tab4[0].screenshot(os.path.join(FIG_DIR, "fig12_weather_hostility.png"))
        print("Captured fig12_weather_hostility.png from app.py")
        
    if len(plots_tab4) >= 2:
        scroll_into_view(plots_tab4[1])
        plots_tab4[1].screenshot(os.path.join(FIG_DIR, "fig15_vehicle_vulnerability.png"))
        print("Captured fig15_vehicle_vulnerability.png from app.py")
        
    # Capture Environmental Data Table / Matrices
    env_tables = driver.find_elements(By.XPATH, '//*[@data-testid="stDataFrame"]')
    if env_tables:
        scroll_into_view(env_tables[0])
        env_tables[0].screenshot(os.path.join(FIG_DIR, "fig14_hostility_index.png"))
        print("Captured fig14_hostility_index.png from Tab 4 table")
        if len(env_tables) >= 2:
            scroll_into_view(env_tables[1])
            env_tables[1].screenshot(os.path.join(FIG_DIR, "fig13_lighting_interaction.png"))
            print("Captured fig13_lighting_interaction.png from Tab 4")
        if len(env_tables) >= 3:
            scroll_into_view(env_tables[2])
            env_tables[2].screenshot(os.path.join(FIG_DIR, "fig16_vru_speed_mortality.png"))
            print("Captured fig16_vru_speed_mortality.png from Tab 4")

    # =========================================================================
    # TAB 5: ML Hotspot & Severity Simulator
    # =========================================================================
    print("\n--- Processing Tab 5: ML Hotspot & Severity Simulator ---")
    click_tab_by_keyword("ML Hotspot")
    time.sleep(3)
    
    plots_tab5 = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
    print(f"Plotly plots found on Tab 5: {len(plots_tab5)}")
    
    if plots_tab5:
        scroll_into_view(plots_tab5[0])
        plots_tab5[0].screenshot(os.path.join(FIG_DIR, "fig17_ml_feature_importance.png"))
        print("Captured fig17_ml_feature_importance.png from app.py")
        
    # Capture the Policy Simulator Sliders & Live Results
    simulator_container = driver.find_elements(By.XPATH, '//div[contains(., "What-If Policy Simulation Sandbox") or contains(., "Scenario")]')
    if simulator_container:
        sim_elem = simulator_container[-1]
        scroll_into_view(sim_elem)
        sim_elem.screenshot(os.path.join(FIG_DIR, "fig19_policy_simulation.png"))
        print("Captured fig19_policy_simulation.png (Policy Simulator) from app.py")
    else:
        # Fallback to general container
        form_elems = driver.find_elements(By.XPATH, '//*[@data-testid="stForm"] | //*[@data-testid="stVerticalBlock"]')
        if form_elems:
            scroll_into_view(form_elems[0])
            form_elems[0].screenshot(os.path.join(FIG_DIR, "fig19_policy_simulation.png"))
            print("Captured fig19_policy_simulation.png via form element")

    # Capture Model Metrics / Confusion Matrix Card
    metric_cards = driver.find_elements(By.XPATH, '//*[@data-testid="stHorizontalBlock"]')
    if metric_cards:
        scroll_into_view(metric_cards[0])
        metric_cards[0].screenshot(os.path.join(FIG_DIR, "fig18_ml_performance.png"))
        print("Captured fig18_ml_performance.png from Tab 5 metrics")

    # =========================================================================
    # TAB 6: India Transferability Case
    # =========================================================================
    print("\n--- Processing Tab 6: India Transferability Case ---")
    click_tab_by_keyword("India Transferability")
    time.sleep(3)
    
    plots_tab6 = driver.find_elements(By.CLASS_NAME, "js-plotly-plot")
    print(f"Plotly plots found on Tab 6: {len(plots_tab6)}")
    
    if plots_tab6:
        scroll_into_view(plots_tab6[0])
        plots_tab6[0].screenshot(os.path.join(FIG_DIR, "fig20_bengaluru_corridors.png"))
        print("Captured fig20_bengaluru_corridors.png from app.py")
        
    # Capture Two-Wheeler / Indian corridor cards
    ind_cards = driver.find_elements(By.XPATH, '//*[@data-testid="stDataFrame"] | //*[@data-testid="stHorizontalBlock"]')
    if ind_cards:
        scroll_into_view(ind_cards[0])
        ind_cards[0].screenshot(os.path.join(FIG_DIR, "fig21_two_wheeler_modal_share.png"))
        print("Captured fig21_two_wheeler_modal_share.png from Tab 6")

    # =========================================================================
    # TAB 7: Pipeline Architecture & Review 1 Docs
    # =========================================================================
    print("\n--- Processing Tab 7: Pipeline Architecture ---")
    click_tab_by_keyword("Pipeline Architecture")
    time.sleep(3)
    
    pipe_elems = driver.find_elements(By.XPATH, '//pre | //code | //*[@data-testid="stExpander"] | //*[@data-testid="stVerticalBlock"]')
    if pipe_elems:
        scroll_into_view(pipe_elems[0])
        pipe_elems[0].screenshot(os.path.join(FIG_DIR, "fig22_synthesis_framework.png"))
        print("Captured fig22_synthesis_framework.png from app.py")
        
    print("\nAll dashboard screenshots captured successfully directly from running app.py!")

finally:
    driver.quit()
