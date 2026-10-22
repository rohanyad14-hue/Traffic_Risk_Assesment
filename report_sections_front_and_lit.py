"""
report_sections_front_and_lit.py
Contains Front Matter, Introduction, Literature Review, Research Questions, and Methodology
for the Traffic Accident Analysis Technical Report.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "extracted_logo.png")
COLOR_TITLE = RGBColor(0x1F, 0x4E, 0x79)
COLOR_MUTED = RGBColor(0x71, 0x80, 0x96)

def build_cover_page(doc, add_p):
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(10)
    p_top.paragraph_format.space_after = Pt(14)
    if os.path.exists(LOGO_PATH):
        r_logo = p_top.add_run()
        r_logo.add_picture(LOGO_PATH, width=Inches(3.2))

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(14)
    p_title.paragraph_format.space_after = Pt(8)
    r_title = p_title.add_run("TRAFFIC ACCIDENT ANALYSIS & SEVERITY RISK MODELING")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(20)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    r_sub = p_sub.add_run("An Exposure-Adjusted Visual Analytics Framework for Proactive Highway Safety & Hazard Identification")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(12.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

    p_dept1 = doc.add_paragraph()
    p_dept1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept1.paragraph_format.space_before = Pt(4)
    p_dept1.paragraph_format.space_after = Pt(2)
    r_dept1 = p_dept1.add_run("School of Computer Science and Engineering")
    r_dept1.font.name = "Times New Roman"
    r_dept1.font.size = Pt(12)
    r_dept1.font.bold = True
    r_dept1.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_dept2 = doc.add_paragraph()
    p_dept2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dept2.paragraph_format.space_before = Pt(0)
    p_dept2.paragraph_format.space_after = Pt(2)
    r_dept2 = p_dept2.add_run("M. Tech Artificial Intelligence and Machine Learning")
    r_dept2.font.name = "Times New Roman"
    r_dept2.font.size = Pt(12)
    r_dept2.font.bold = True
    r_dept2.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_sem = doc.add_paragraph()
    p_sem.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sem.paragraph_format.space_before = Pt(0)
    p_sem.paragraph_format.space_after = Pt(14)
    r_sem = p_sem.add_run("Fall Semester 2026")
    r_sem.font.name = "Times New Roman"
    r_sem.font.size = Pt(11.5)
    r_sem.font.bold = True
    r_sem.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_c1 = doc.add_paragraph()
    p_c1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_c1.paragraph_format.space_before = Pt(0)
    p_c1.paragraph_format.space_after = Pt(2)
    r_c1 = p_c1.add_run("Course Title: Technical Report Writing / Visual Analytics Lab")
    r_c1.font.name = "Times New Roman"
    r_c1.font.size = Pt(11)
    r_c1.font.bold = True
    r_c1.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_c2 = doc.add_paragraph()
    p_c2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_c2.paragraph_format.space_before = Pt(0)
    p_c2.paragraph_format.space_after = Pt(2)
    r_c2 = p_c2.add_run("Course Code: MAENG501 / CSE5001")
    r_c2.font.name = "Times New Roman"
    r_c2.font.size = Pt(11)
    r_c2.font.bold = True
    r_c2.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_c3 = doc.add_paragraph()
    p_c3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_c3.paragraph_format.space_before = Pt(0)
    p_c3.paragraph_format.space_after = Pt(24)
    r_c3 = p_c3.add_run("Slot: TF2 | Review 1 Prototype")
    r_c3.font.name = "Times New Roman"
    r_c3.font.size = Pt(11)
    r_c3.font.bold = True
    r_c3.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_subto_h = doc.add_paragraph()
    p_subto_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subto_h.paragraph_format.space_before = Pt(0)
    p_subto_h.paragraph_format.space_after = Pt(2)
    r_subto_h = p_subto_h.add_run("SUBMITTED TO:")
    r_subto_h.font.name = "Times New Roman"
    r_subto_h.font.size = Pt(11)
    r_subto_h.font.bold = True
    r_subto_h.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

    p_subto_name = doc.add_paragraph()
    p_subto_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subto_name.paragraph_format.space_before = Pt(0)
    p_subto_name.paragraph_format.space_after = Pt(2)
    r_subto_name = p_subto_name.add_run("DR. MANIKANDAN K")
    r_subto_name.font.name = "Times New Roman"
    r_subto_name.font.size = Pt(11.5)
    r_subto_name.font.bold = True
    r_subto_name.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_subto_dept = doc.add_paragraph()
    p_subto_dept.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_subto_dept.paragraph_format.space_before = Pt(0)
    p_subto_dept.paragraph_format.space_after = Pt(22)
    r_subto_dept = p_subto_dept.add_run("SCHOOL OF COMPUTER SCIENCE AND ENGINEERING (SCOPE)")
    r_subto_dept.font.name = "Times New Roman"
    r_subto_dept.font.size = Pt(10.5)
    r_subto_dept.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    p_by_h = doc.add_paragraph()
    p_by_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by_h.paragraph_format.space_before = Pt(0)
    p_by_h.paragraph_format.space_after = Pt(4)
    r_by_h = p_by_h.add_run("SUBMITTED BY:")
    r_by_h.font.name = "Times New Roman"
    r_by_h.font.size = Pt(11)
    r_by_h.font.bold = True
    r_by_h.font.color.rgb = RGBColor(0x2E, 0x74, 0xB5)

    authors = [
        "SARANYA DALAL — 26MML0007",
        "DIVYA VIJAYKUMAR PUJARI — 26MML0009",
        "ROHAN YADAV — 26MML0020"
    ]
    for auth in authors:
        p_a = doc.add_paragraph()
        p_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_a.paragraph_format.space_before = Pt(0)
        p_a.paragraph_format.space_after = Pt(2)
        r_a = p_a.add_run(auth)
        r_a.font.name = "Times New Roman"
        r_a.font.size = Pt(11)
        r_a.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

    doc.add_page_break()

def build_abstract(doc, add_h1, add_p, add_callout):
    add_h1(doc, "ABSTRACT", align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_p(doc, 
        "Road traffic collisions constitute one of the leading global causes of preventable mortality, claiming approximately 1.19 million lives annually and inflicting profound socio-economic devastation. For decades, conventional municipal and transportation safety analyses have relied predominantly on raw crash frequency metrics—commonly referred to as 'blackspot counting'—to detect hazardous roadway segments and prioritize engineering capital investments. However, this study empirically demonstrates that frequency-based collision modeling introduces systemic structural distortions that severely compromise public safety. Because high-volume transit corridors such as grade-separated motorways and urban interchanges carry tens of millions of vehicles annually, they inevitably accumulate large absolute crash counts consisting almost entirely of minor, low-speed property damage shunts and slight injuries, creating the deceptive appearance of extreme danger. Conversely, low-volume rural single-carriageway corridors and unlit peripheral curves carry modest traffic volumes and register very few total collisions, yet consistently generate catastrophic, high-velocity fatal and serious casualties.")

    add_p(doc,
        "To resolve this fundamental paradox, this technical report presents an end-to-end, reproducible visual analytics and statistical modeling framework that formulates an exposure-adjusted severity risk index. By shifting the unit of analysis from individual crash events to cohesive road network segments, the framework synthesizes multi-grain data feeds comprising 22,000 UK STATS19 collision records, OpenStreetMap (OSM) roadway geometric configurations, Annual Average Daily Traffic (AADT) sensor counts, and Open-Meteo atmospheric observations. Incident severity is calibrated using published UK Department for Transport (DfT) economic injury-cost ratios (Fatal = 50, Serious = 10, Slight = 1), normalized against annual roadway exposure measured in Million Vehicle-Kilometers (MVKM), and stabilized via a near-zero denominator suppression threshold.")

    add_p(doc,
        "Empirical validation across the synthesized network provides undeniable mathematical proof of the severity-frequency inversion thesis. While the high-volume M25 Orbital Interchange (SEG-0417) registers 47 crashes, its 27.1 MVKM exposure yields a safe risk index of 6.86 per MVKM (ranking #152 out of 160). In stark contrast, the low-volume B4009 Chiltern Ridge Curve (SEG-1902) records only 6 crashes, but due to severe trauma and low exposure (2.5 MVKM), produces a catastrophic risk index of 84.40 per MVKM (ranking #2 as a lethal trap). Thus, a corridor with one-eighth the crashes exhibits over twelve times the true risk! A spatiotemporal 168-cell matrix reveals a dramatic circadian night-time surge, where fatality rates peak at 6.82% during pre-dawn hours (02:00–05:00) despite minimal traffic. Multi-hazard environmental interaction doubles severe outcome rates under unlit, wet conditions, while vulnerable road users (VRUs) face near-exponential mortality growth exceeding 48.9% at 70 mph. Furthermore, cross-geographic transferability benchmarking on Bengaluru arterial corridors demonstrates that mixed-traffic conditions with 55%+ two-wheeler modal share drive severe risk to 56.82 per MVKM. A trained Random Forest classifier (87.1% accuracy, 0.884 ROC-AUC) isolates VRU presence, traffic volume, and posted speed limits as paramount severity determinants, powering an interactive policy simulator that forecasts up to 65.4% severe harm reduction through targeted engineering retrofits.")

    add_callout(doc, 
        "Central Empirical Axiom: 'One-eighth the crashes. Twelve times the risk. Low frequency masks high severity.' Traditional frequency-based blackspot prioritization systematically misallocates safety resources away from lethal rural corridors to congested urban motorways.",
        title="CORE RESEARCH THESIS")

    p_kw = add_p(doc, "Keywords: ", bold=True, size=10.5)
    r_kws = p_kw.add_run("Traffic Safety Analytics, Exposure Normalization, Million Vehicle-Kilometers (MVKM), DfT Severity Weighting, Frequency-Severity Paradox, DuckDB OLAP Cubes, Circadian Risk Dynamics, Vulnerable Road Users (VRU), Random Forest Severity Attribution, Mixed-Traffic Transferability.")
    r_kws.font.name = "Times New Roman"
    r_kws.font.size = Pt(10.5)
    r_kws.font.italic = True
    r_kws.font.color.rgb = RGBColor(0x4A, 0x55, 0x68)

    doc.add_page_break()

def build_table_of_contents(doc, add_h1, add_table_data):
    add_h1(doc, "TABLE OF CONTENTS", align=WD_ALIGN_PARAGRAPH.CENTER)
    
    headers = ["Title / Section Heading", "Page No."]
    toc_rows = [
        ["Abstract", "i"],
        ["List of Figures", "ii"],
        ["List of Tables", "iv"],
        ["1. INTRODUCTION", "1"],
        ["    1.1 Global and National Highway Safety Realities", "1"],
        ["    1.2 The Systemic Fallacy of Raw Crash Frequency ('Blackspot Counting')", "2"],
        ["    1.3 The Severity-Frequency Inversion Thesis: Central Claim", "3"],
        ["    1.4 Objectives, Scope, and Structural Organization", "4"],
        ["2. LITERATURE REVIEW", "5"],
        ["    2.1 Classical Crash Frequency & Hotspot Identification Models", "5"],
        ["    2.2 Exposure-Based Normalization & Economic Injury Cost Weighting", "6"],
        ["    2.3 Environmental, Circadian, and Roadway Hostility Factors", "7"],
        ["    2.4 Vulnerable Road User (VRU) Dynamics & Mixed-Traffic Heterogeneity", "8"],
        ["    2.5 Visual Analytics and Columnar OLAP Architectures in Safety Engineering", "9"],
        ["    2.6 Critical Literature Gaps and Conceptual Departure", "10"],
        ["3. RESEARCH QUESTIONS", "11"],
        ["4. METHODOLOGY & SYSTEM ARCHITECTURE", "12"],
        ["    4.1 Reproducible End-to-End Pipeline Architecture", "12"],
        ["    4.2 Multi-Grain Data Ingestion and Road Network Synthesis", "13"],
        ["    4.3 Mathematical Formulation of Road Exposure and Severity Risk", "14"],
        ["    4.4 Statistical Suppression Floor Criteria & Denominator Boundary Rules", "15"],
        ["    4.5 Four-Quadrant Strategic Roadway Classification Matrix", "16"],
        ["    4.6 High-Performance Columnar OLAP Engine (DuckDB & Parquet Cubes)", "17"],
        ["5. RESULTS AND DISCUSSION", "18"],
        ["    5.1 Dataset Demographics and Network Exposure Baseline", "18"],
        ["        5.1.1 Network Crash Severity Breakdown (Figure 1, Table 1)", "18"],
        ["        5.1.2 Roadway Hierarchy & Geometric Characteristics (Figure 2, Table 2)", "19"],
        ["        5.1.3 Traffic Volume Exposure Distributions Across Road Classes (Figure 3, Table 3)", "20"],
        ["    5.2 The Core Severity-Frequency Inversion: Benchmark Case Study & 4-Quadrant Analysis", "21"],
        ["        5.2.1 Four-Quadrant Strategic Roadway Classification Matrix (Figure 4, Table 4)", "21"],
        ["        5.2.2 Empirical Benchmark Case Study Validation: SEG-0417 vs. SEG-1902 (Figure 5, Table 5)", "22"],
        ["        5.2.3 Systemic Rank Inversion & Priority Misallocation (Figure 6, Table 6)", "23"],
        ["    5.3 Temporal & Circadian Risk Dynamics: The Midnight Lethality Peak", "24"],
        ["        5.3.1 24-Hour Circadian Dual-Axis Risk Curve (Figure 7, Table 7)", "24"],
        ["        5.3.2 168-Cell Spatiotemporal Day-of-Week × Hour Heatmap (Figure 8, Table 8)", "25"],
        ["        5.3.3 Weekday Baseline vs. Weekend Recreational Nocturnal Contrast (Figure 9, Table 9)", "26"],
        ["    5.4 Spatial Risk Topography & Network Geometry", "27"],
        ["        5.4.1 Spatial Risk Topography & Geometric Decoupling (Figure 10, Table 10)", "27"],
        ["        5.4.2 Speed Limit Regimes and Kinetic Energy Scaling (Figure 11, Table 11)", "28"],
        ["    5.5 Environmental Hostility Amplifiers: Precipitation, Wet Friction, and Darkness", "29"],
        ["        5.5.1 Atmospheric Weather Conditions & Friction Degradation (Figure 12, Table 12)", "29"],
        ["        5.5.2 Roadway Illumination Quality & Ambient Darkness Multiplication (Figure 13, Table 13)", "30"],
        ["        5.5.3 Compound Multi-Hazard Environmental Hostility Index (Figure 14, Table 14)", "31"],
        ["    5.6 Vehicle Vulnerability & Modal Hierarchy: VRU Mortality Across Speed Regimes", "32"],
        ["        5.6.1 Modal Vulnerability Hierarchy Across Vehicle Categories (Figure 15, Table 15)", "32"],
        ["        5.6.2 Vulnerable Road User Mortality Escalation by Speed Regime (Figure 16, Table 16)", "33"],
        ["    5.7 Machine Learning Severity Attribution & Targeted Policy Simulation", "34"],
        ["        5.7.1 Random Forest Feature Importance Spectrum (Figure 17, Table 17)", "34"],
        ["        5.7.2 Classification Model Performance & Confusion Matrix Validation (Figure 18, Table 18)", "35"],
        ["        5.7.3 Targeted Engineering Countermeasure Policy Simulation (Figure 19, Table 19)", "36"],
        ["    5.8 Emerging Market Transferability: Indian Urban Mixed-Traffic Case Study", "37"],
        ["        5.8.1 Bengaluru Arterial Corridor Risk Evaluation (Figure 20, Table 20)", "37"],
        ["        5.8.2 Two-Wheeler Modal Share Divergence & Vulnerability Density (Figure 21, Table 21)", "38"],
        ["        5.8.3 Synthesis Framework: From Reactive Blackspots to Proactive Exposure Analytics (Figure 22, Table 22)", "39"],
        ["6. CONCLUSIONS & POLICY RECOMMENDATIONS", "40"],
        ["    6.1 Empirical Summary & Resolution of Research Questions", "40"],
        ["    6.2 Structural Policy Interventions for Highway & Municipal Authorities", "41"],
        ["    6.3 Algorithmic Integration with Intelligent Transportation Systems (ITS) & Vision Zero", "42"],
        ["    6.4 Limitations and Future Research Directions", "43"],
        ["REFERENCES", "44"],
        ["APPENDIX", "46"],
        ["    Appendix A: Mathematical Derivations and Numerical Boundary Conditions", "46"],
        ["    Appendix B: Data Dictionary and DuckDB Pipeline Schemas", "47"],
        ["    Appendix C: Visual Analytics Dashboard User Guide & Streamlit Implementation", "48"]
    ]
    add_table_data(doc, headers, toc_rows, col_widths=[5.0, 1.2], right_align_cols=[1])
    doc.add_page_break()

def build_list_of_figures(doc, add_h1, add_p):
    add_h1(doc, "List of Figures", align=WD_ALIGN_PARAGRAPH.CENTER)
    
    figures_list = [
        ("Figure 1", "Overall Crash Severity Distribution & DfT Economic Injury Weights (N = 22,000)", "18"),
        ("Figure 2", "Road Network Hierarchy Distribution (OSM Road Classification Breakdown; N = 160 Segments)", "19"),
        ("Figure 3", "Traffic Volume Exposure Spectrum by Functional Road Class (Annual Average Daily Traffic Distribution)", "20"),
        ("Figure 4", "Four-Quadrant Analytical Scatter Matrix: Raw Incident Volume vs. Exposure-Adjusted Severity Risk Index", "21"),
        ("Figure 5", "Benchmark Case Study Validation: SEG-0417 (M25 Interchange) vs. SEG-1902 (B4009 Ridge Curve)", "22"),
        ("Figure 6", "Systemic Priority Inversion: Distribution of Rank Displacement (Delta Rank Shifts)", "23"),
        ("Figure 7", "24-Hour Circadian Risk Dynamics: Gross Hourly Crash Volume vs. Fatality Proportion (%)", "24"),
        ("Figure 8", "168-Cell Spatiotemporal Risk Heatmap Matrix (Day-of-Week x Hour-of-Day Mean Severity Weight)", "25"),
        ("Figure 9", "Nocturnal Severity Contrast: Weekdays vs. Weekend Recreational Late-Night Outcome Proportions", "26"),
        ("Figure 10", "Geospatial Road Network Risk Topography (Circle Size = Volume, Color = Exposure-Adjusted Risk)", "27"),
        ("Figure 11", "Kinetic Energy Scaling: Posted Speed Limit Regimes vs. Fatality Rate Escalation", "28"),
        ("Figure 12", "Atmospheric Weather Hostility: Severe Outcome Proportions Across Meteorological Regimes", "29"),
        ("Figure 13", "Illumination Deprivation: Severe Harm Multipliers in Streetlit vs. Dark Unlit Road Corridors", "30"),
        ("Figure 14", "Compound Environmental Hostility Index: Multi-Hazard Friction and Darkness Risk Amplification", "31"),
        ("Figure 15", "Modal Vulnerability Hierarchy: Severe Injury and Fatality Rates Across Primary Vehicle Categories", "32"),
        ("Figure 16", "Vulnerable Road User (VRU) Mortality Escalation as a Function of Posted Speed Limit Tiers", "33"),
        ("Figure 17", "Predictive Severity Attribution: Random Forest Feature Importance Spectrum (Gini Impurity Metric)", "34"),
        ("Figure 18", "Hotspot Classifier Validation: Confusion Matrix Heatmap and Standard Classification Metrics", "35"),
        ("Figure 19", "Targeted Engineering Policy Simulation: Cumulative Risk Reductions Under Infrastructure Countermeasures", "36"),
        ("Figure 20", "India Mixed-Traffic Transferability: Severe Risk Divergence on Bengaluru Arterial Corridors", "37"),
        ("Figure 21", "Vulnerability Density: Correlation Between Two-Wheeler Modal Share (%) and Risk Index per MVKM", "38"),
        ("Figure 22", "The Exposure-Adjusted Visual Analytics Architecture: Paradigm Transition from Reactive Counting to Proactive Safety", "39")
    ]
    
    for f_label, f_title, f_page in figures_list:
        p = add_p(doc, f"{f_label}: {f_title}", bold=False, size=10, space_after=3)
        r_dots = p.add_run(" " + "." * max(5, int(75 - len(f_label) - len(f_title)*0.55)) + " ")
        r_dots.font.color.rgb = COLOR_MUTED
        r_pg = p.add_run(f_page)
        r_pg.font.bold = True
        r_pg.font.color.rgb = COLOR_TITLE

    doc.add_page_break()

def build_list_of_tables(doc, add_h1, add_p):
    add_h1(doc, "List of Tables", align=WD_ALIGN_PARAGRAPH.CENTER)
    
    tables_list = [
        ("Table 1", "Overall Network Crash Severity Breakdown, Proportions, and DfT Economic Weights", "18"),
        ("Table 2", "Road Hierarchy Classification, Lane Configuration, and Segment Length Metrics", "19"),
        ("Table 3", "Traffic Volume Exposure Statistics and Annual Million Vehicle-Kilometers (MVKM) by Road Class", "20"),
        ("Table 4", "Four-Quadrant Strategic Roadway Classification Matrix and Aggregate Safety Outcomes", "21"),
        ("Table 5", "Empirical Validation Benchmark Case Study: SEG-0417 vs. SEG-1902 Comparative Metrics", "22"),
        ("Table 6", "Top 10 High-Lethality Road Segments Subject to Systemic Rank Inversion ('Deadly Traps')", "23"),
        ("Table 7", "24-Hour Circadian Temporal Distribution of Incident Volume, Fatalities, and Fatality Rate (%)", "24"),
        ("Table 8", "Circadian Operational Phase Aggregations and Temporal Safety Performance Metrics", "25"),
        ("Table 9", "Nocturnal Severity Contrast: Weekday Normal vs. Weekend Recreational Incident Cohorts", "26"),
        ("Table 10", "Spatial Corridor Risk Density and Segment Inversion Statistics Across Network Geographic Sectors", "27"),
        ("Table 11", "Posted Speed Limit Regimes vs. Crash Severity Distribution and Vulnerable User Involvement", "28"),
        ("Table 12", "Atmospheric Weather Conditions vs. Crash Volume, Fatalities, and Severe Outcome Rate", "29"),
        ("Table 13", "Roadway Illumination Quality and Ambient Darkness Impact on Crash Severity Outcomes", "30"),
        ("Table 14", "Compound Environmental Hostility Matrix (Multi-Factor Interaction of Weather, Surface, and Light)", "31"),
        ("Table 15", "Primary Vehicle Classification Vulnerability and Severe Harm Injury Profiles", "32"),
        ("Table 16", "Vulnerable Road User (VRU) Mortality Rate Escalation Across Posted Speed Tiers", "33"),
        ("Table 17", "Random Forest Severity Attribution: Top Predictor Features and Gini Impurity Weights", "34"),
        ("Table 18", "Hotspot Classifier Performance Metrics (Accuracy, Precision, Recall, F1-Score, ROC-AUC)", "35"),
        ("Table 19", "Targeted Countermeasure Policy Simulation: Projected Injury & Risk Index Reductions", "36"),
        ("Table 20", "Indian Urban Mixed-Traffic Corridor Benchmark Analysis (Bengaluru Arterial Cohort)", "37"),
        ("Table 21", "Cross-Jurisdictional Comparison: UK STATS19 Network vs. Bengaluru Arterial Corridors", "38"),
        ("Table 22", "Synthesis Summary: Traditional Reactive Blackspots vs. Exposure-Adjusted Proactive Interventions", "39")
    ]
    
    for t_label, t_title, t_page in tables_list:
        p = add_p(doc, f"{t_label}: {t_title}", bold=False, size=10, space_after=3)
        r_dots = p.add_run(" " + "." * max(5, int(75 - len(t_label) - len(t_title)*0.55)) + " ")
        r_dots.font.color.rgb = COLOR_MUTED
        r_pg = p.add_run(t_page)
        r_pg.font.bold = True
        r_pg.font.color.rgb = COLOR_TITLE

    doc.add_page_break()

print("Front matter module loaded.")
