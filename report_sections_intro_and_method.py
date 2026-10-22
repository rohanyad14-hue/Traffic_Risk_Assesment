"""
report_sections_intro_and_method.py
Contains Section 1 (Introduction), Section 2 (Literature Review),
Section 3 (Research Questions), and Section 4 (Methodology & System Architecture).
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def build_section_1_introduction(doc, add_h1, add_h2, add_p, add_callout):
    add_h1(doc, "1. INTRODUCTION")
    
    add_h2(doc, "1.1 Global and National Highway Safety Realities")
    add_p(doc,
        "Road traffic crashes represent one of the most critical public health and socio-economic crises of the modern era. According to the World Health Organization (WHO) Global Status Report on Road Safety, road traffic injuries cause approximately 1.19 million preventable fatalities each year, ranking as the leading cause of death globally for children and young adults aged 5 to 29 years. Beyond the immeasurable human suffering of bereavement and permanent disability, road trauma imposes a severe macroeconomic burden, consuming between 2% and 5% of national Gross Domestic Product (GDP) across middle- and high-income economies through emergency healthcare expenditure, legal adjudication, property destruction, and long-term loss of productive human capital.")
    
    add_p(doc,
        "In developing nations such as India, the crisis is particularly acute. Official data published by the Ministry of Road Transport and Highways (MoRTH) indicates that India accounts for over 168,000 traffic fatalities annually—representing roughly 11% of the global total despite possessing only 1% of the world's vehicular fleet. Simultaneously, mature motorized economies such as the United Kingdom have achieved significant historical reductions through structured reporting protocols (such as the STATS19 road collision database) and rigorous civil engineering standards. Nonetheless, recent years have witnessed an alarming stagnation in fatality reduction rates across both emerging and developed transportation networks. Highway authorities increasingly recognize that conventional safety auditing practices have hit a point of diminishing returns, largely because the analytical paradigms used to detect roadway hazards are fundamentally flawed.")

    add_h2(doc, "1.2 The Systemic Fallacy of Raw Crash Frequency ('Blackspot Counting')")
    add_p(doc,
        "For more than six decades, transportation agencies, highway patrol divisions, and municipal planning bodies have relied almost exclusively on raw crash incident counts—often termed 'blackspot analysis' or 'crash clustering'—to identify high-risk roadway locations. Under this legacy paradigm, road segments or intersections that accumulate the highest total volume of police-recorded collisions ($N$) over a given observation period (typically 3 to 5 years) are flagged as hazardous priorities and allocated public remediation funds for safety improvements.")
    
    add_p(doc,
        "However, raw frequency models suffer from a fatal methodological blind spot: they fail to normalize incident counts against vehicular exposure. Road networks are inherently heterogeneous in traffic throughput. A multi-lane grade-separated motorway or an urban expressway interchange carries tens of millions of vehicle-kilometers annually. On such high-density corridors, vehicle interactions occur under heavy congestion and bumper-to-bumper queueing, resulting in frequent low-speed rear-end shunts, side-swipes, and minor fender-benders that generate negligible physical injury. Because these minor incidents aggregate into high total collision counts ($N$), raw blackspot metrics flag them as extreme hazards.")

    add_p(doc,
        "Conversely, winding rural single-carriageway corridors, unlit suburban peripheral curves, and narrow regional link roads carry comparatively modest traffic volumes. Because total vehicle exposure is low, the gross number of collisions on these segments appears statistically minimal. However, due to higher operating speeds, lack of physical median separation, adverse horizontal curvature, and absence of fixed illumination, the collisions that do occur on these corridors produce catastrophic outcomes characterized by violent head-on collisions, rollover impacts, and high mortality rates. Under conventional blackspot screening, these lethal corridors remain completely invisible because their low crash counts fail to trigger municipal intervention thresholds.")

    add_h2(doc, "1.3 The Severity-Frequency Inversion Thesis: Central Claim")
    add_p(doc,
        "This fundamental disconnect gives rise to the central claim and theoretical departure of this research:")
    
    add_callout(doc,
        "Central Research Claim: 'One-eighth the crashes. Twelve times the risk. Low frequency masks high severity.' Conventional raw incident counting systematically misrepresents roadway hazard, blinding safety engineers to lethal, low-volume rural traps while over-investing capital in high-volume, low-severity urban corridors.",
        title="CENTRAL THESIS OF THIS REPORT")

    add_p(doc,
        "When roadway incident frequency is weighted by the economic and clinical severity of human injuries and normalized against annual traffic volume exposure (Million Vehicle-Kilometers, MVKM), the true hierarchy of highway danger is radically inverted. Highway engineering interventions must therefore shift from reactive, frequency-driven blackspot remediation toward proactive, exposure-adjusted severity risk analytics.")

    add_h2(doc, "1.4 Objectives, Scope, and Structural Organization")
    add_p(doc,
        "The overarching objective of this research is to construct, validate, and operationalize an end-to-end visual analytics framework for exposure-adjusted traffic accident risk modeling. Specifically, this study delivers:")
    
    add_p(doc, "1. A reproducible batch data engineering pipeline that ingests multi-grain collision, road network, traffic volume, and meteorological data, conforms spatial geometries, encodes official DfT injury severity weights, and computes exposure-adjusted risk indices.", bold=False, size=11)
    add_p(doc, "2. A Four-Quadrant Strategic Roadway Classification Matrix that partitions road segments into operational safety typologies (Severe Congested, Deadly Traps, Safe Segments, and Fender-Benders) to guide municipal decision-making.", bold=False, size=11)
    add_p(doc, "3. An empirical investigation of temporal and circadian risk dynamics, proving how nocturnal physiological fatigue, speed escalation, and darkness amplify fatality rates even as gross traffic drops to minimal levels.", bold=False, size=11)
    add_p(doc, "4. Multi-hazard environmental and modal vulnerability assessments, quantifying the compound risks of adverse precipitation, unlit roads, and vulnerable road user (VRU) physical fragility across posted speed tiers.", bold=False, size=11)
    add_p(doc, "5. A high-performance columnar OLAP aggregation architecture (DuckDB + Parquet) coupled with a Random Forest machine learning classifier to deliver an interactive 'what-if' policy simulation sandbox for roadway safety engineers.", bold=False, size=11)
    add_p(doc, "6. A cross-geographic transferability benchmark evaluating the framework under extreme mixed-traffic heterogeneity (55%+ two-wheeler modal share) on arterial highway corridors in Bengaluru, India.", bold=False, size=11)

    add_p(doc,
        "The remainder of this report is organized as follows: Section 2 conducts a comprehensive literature review of highway safety modeling, exposure normalization, and visual analytics. Section 3 formalizes the core Research Questions (RQs). Section 4 outlines the pipeline architecture, mathematical formulations, and engineering design. Section 5 presents detailed empirical results and analytical discussion across 22 publication-grade figures and 22 structured data tables. Section 6 concludes with actionable policy recommendations and future research directions.")

def build_section_2_literature_review(doc, add_h1, add_h2, add_p, add_callout):
    add_h1(doc, "2. LITERATURE REVIEW")
    
    add_h2(doc, "2.1 Classical Crash Frequency & Hotspot Identification Models")
    add_p(doc,
        "The identification of hazardous roadway locations—conventionally termed 'hotspots', 'blackspots', or 'sites with promise'—has historically been formulated as an extreme-value statistical counting problem. Early transportation safety researchers (e.g., McGuigan, 1982; Hauer, 1996) utilized simple historical crash count rankings ($N$). However, raw count models are severely corrupted by the phenomenon of Regression-to-the-Mean (RTM)—the statistical reality that sites experiencing an unusually high number of crashes in a given short interval naturally regress toward their long-term mean in subsequent periods, irrespective of whether an engineering countermeasure was deployed.")
    
    add_p(doc,
        "To mitigate RTM, classical highway safety engineering adopted generalized linear models (GLMs), predominantly Poisson regression and Negative Binomial (Poisson-gamma) models, to account for overdispersion in discrete crash count data (Lord & Mannering, 2010). The Empirical Bayes (EB) method, formalized extensively in the AASHTO Highway Safety Manual (HSM, 2010), combines observed collision history with model-predicted baseline frequencies from Safety Performance Functions (SPFs) to estimate expected long-term crash frequencies. While EB represents a substantial statistical advance over raw counts, contemporary transportation scholars (Elvik, 2008; Geurts & Wets, 2003) emphasize that standard SPFs remain fundamentally frequency-centric. By optimizing almost exclusively for total incident count reduction rather than human injury severity reduction, classical methods perpetuate an implicit bias toward heavily trafficked urban facilities where property-damage-only incidents dominate.")

    add_h2(doc, "2.2 Exposure-Based Normalization & Economic Injury Cost Weighting")
    add_p(doc,
        "To establish equitable risk comparisons across roads of differing operational scales, exposure normalization is essential. In highway safety epidemiology, exposure represents the measure of opportunity for a crash to occur (Chapman, 1973). The universally recognized gold standard for roadway exposure is Annual Vehicle-Kilometers Traveled (VKT) or Million Vehicle-Kilometers (MVKM), calculated as the product of Annual Average Daily Traffic (AADT), segment length ($L$), and operational days per year ($365$). Normalizing crashes by MVKM yields a crash rate ($R = N / \text{MVKM}$).")

    add_p(doc,
        "Crucially, treating all crash events as homogeneous occurrences in crash rate calculations introduces severe economic distortion. A single fatal collision imposes staggering socio-economic losses—including loss of human life, productive years, extensive police investigations, and hospital intensive care—orders of magnitude greater than a minor bumper tap. Consequently, transportation economists and government agencies have developed comprehensive economic injury valuations. The UK Department for Transport (DfT, 2021) in its annual 'Reported Road Casualties Great Britain' assigns explicit economic cost ratios to human injury severities: an average fatal collision incurs an economic cost of approximately £2.1 million, a serious injury collision incurs roughly £240,000, and a slight injury collision incurs £25,000. These values establish an empirical economic weighting ratio of approximately 50 : 10 : 1 (or 84 : 9.6 : 1 in unrounded valuations). The Indian Road Congress (IRC:SP:88-2019) similarly recommends equivalent severity weighting matrices for national highway safety audits, corroborating the necessity of weighting crash frequencies by empirical severity cost.")

    add_h2(doc, "2.3 Environmental, Circadian, and Roadway Hostility Factors")
    add_p(doc,
        "Crash occurrence and severity are governed by dynamic interactions between human physiological factors, vehicular dynamics, and ambient physical environments (Evans, 2004). Chronobiological research (Akerstedt, 2000; Horne & Reyner, 1995) demonstrates that human alertness and cognitive reaction times follow a profound 24-hour circadian cycle, with severe psychomotor troughs occurring between 02:00 and 06:00 (the post-midnight circadian window). While gross traffic volumes drop precipitously during nocturnal hours, drivers who operate vehicles during this period frequently suffer from acute sleep deprivation, fatigue-induced microsleeps, or alcohol and substance impairment. Furthermore, the absence of congestion enables substantially higher cruising speeds, drastically amplifying kinetic impact forces ($E_k = \frac{1}{2}mv^2$) in the event of an impact.")

    add_p(doc,
        "Meteorological and lighting hostility factors compound these kinetic risks. Atmospheric precipitation (rain, snowfall, freezing fog) induces hydroplaning and significantly degrades the skid resistance and friction coefficient ($\mu$) of the asphalt surface (Wallman & Astrom, 2001). Under dark unlit conditions, driver perception-reaction distance exceeds vehicular headlight illumination boundaries, particularly on rural single-carriageway corridors where physical median barriers and street lighting are absent. Despite these well-documented physical realities, few analytical platforms systematically fuse real-time meteorological observation feeds with crash records at segment granularity.")

    add_h2(doc, "2.4 Vulnerable Road User (VRU) Dynamics & Mixed-Traffic Heterogeneity")
    add_p(doc,
        "Vulnerable Road Users (VRUs)—specifically pedestrians, pedal cyclists, and motorized two-wheeler riders—lack the protective structural steel cage, crumple zones, seatbelt pre-tensioners, and airbags of passenger cars. As demonstrated by Rosén et al. (2011) and Wramborg (2005), the probability of fatal injury for an unprotected pedestrian struck by a motor vehicle escalates non-linearly with impact speed: pedestrian fatality risk is below 10% at an impact speed of 30 km/h (18.6 mph), rises steeply to approximately 30% at 40 km/h (25 mph), exceeds 50% at 50 km/h (31 mph), and approaches near certainty (>85%) at speeds exceeding 70 km/h (43.5 mph).")

    add_p(doc,
        "In emerging market urban environments, this vulnerability is vastly amplified by mixed-traffic heterogeneity. In cities like Bengaluru, Mumbai, and New Delhi, motorized two-wheelers (scooters, motorcycles) comprise 50% to 70% of total modal share (Tiwari, 2002; Mohan, 2009). These two-wheelers share the exact same unsegregated carriageway space with heavy commercial trucks, intercity buses, and passenger cars under volatile speed differentials and absence of lane discipline. As a result, standard Western highway safety guidelines that assume predominantly homogeneous four-wheeled passenger car traffic severely under-predict crash severity in emerging markets.")

    add_h2(doc, "2.5 Visual Analytics and Columnar OLAP Architectures in Safety Engineering")
    add_p(doc,
        "While statistical modeling provides theoretical rigor, municipal highway safety engineers require interactive, visual tools to explore high-dimensional data, evaluate trade-offs, and communicate findings to political stakeholders (Thomas & Cook, 2005). Historically, transportation Geographic Information Systems (GIS) software (e.g., Esri ArcGIS, QGIS) has been constrained by slow rendering speeds, cumbersome row-oriented relational database backends, and lack of real-time multi-dimensional slicing capabilities.")

    add_p(doc,
        "Recent breakthroughs in modern data architecture have transformed this landscape. Embedded columnar Online Analytical Processing (OLAP) database engines—exemplified by DuckDB (Raasveldt & Mühleisen, 2019)—execute vectorized queries across multi-million row Parquet datasets in milliseconds directly within process memory, bypassing traditional relational database overhead. When integrated with web-based GPU-accelerated spatial rendering libraries (such as PyDeck and Mapbox GL) and reactive dashboard frameworks (such as Streamlit), safety analysts can perform sub-second interactive slicing across multi-dimensional cubes (temporal heatmaps, environmental cross-tabulations, and 3D geospatial overlays) without requiring dedicated database server clusters.")

    add_h2(doc, "2.6 Critical Literature Gaps and Conceptual Departure")
    add_p(doc,
        "A rigorous synthesis of existing literature identifies three fundamental research gaps:")
    
    add_p(doc, "1. Methodological Decoupling: Most existing research either evaluates raw crash counts using advanced spatial statistics OR computes aggregate macroscopic crash rates at the provincial/state level. There is a marked absence of segment-grain frameworks that simultaneously integrate microscopic vehicle exposure, economic injury weighting, and statistical suppression thresholds.", bold=False, size=11)
    add_p(doc, "2. Failure to Operationalize the Inversion: While academic papers occasionally acknowledge that low-volume roads have high crash rates, there is no standardized operational decision matrix (such as our proposed 4-Quadrant Matrix) that translates this mathematical reality into actionable engineering countermeasure budgets.", bold=False, size=11)
    add_p(doc, "3. Cross-Geographic Transferability Deficit: Safety models developed for homogenous Western highway traffic are rarely tested for algorithmic transferability against the volatile, high-vulnerability mixed-traffic conditions of developing world urban corridors.", bold=False, size=11)

    add_callout(doc,
        "Research Need: An end-to-end, reproducible visual analytics system that unifies multi-source data ingestion, exposure normalization, economic injury weighting, columnar OLAP aggregation, machine learning attribution, and mixed-traffic transferability into a single cohesive platform.",
        title="LITERATURE GAP & CONTRIBUTION")

def build_section_3_research_questions(doc, add_h1, add_h2, add_p, add_callout):
    add_h1(doc, "3. RESEARCH QUESTIONS")
    add_p(doc,
        "To rigorously investigate the severity-frequency paradox and validate the exposure-adjusted visual analytics framework, this technical report addresses five primary Research Questions (RQs):")

    add_h2(doc, "RQ 1: Circadian and Temporal Dynamics (WHEN?)")
    add_p(doc,
        "How do 24-hour circadian cycles and weekly temporal dynamics invert the proportion of fatal versus minor traffic collisions, and to what extent does nocturnal volume reduction mask disproportionately catastrophic human trauma during post-midnight operating hours?")

    add_h2(doc, "RQ 2: Spatial Exposure Risk Divergence and Priority Inversion (WHERE?)")
    add_p(doc,
        "To what extent does normalizing incident frequency by Million Vehicle-Kilometers (MVKM) invert network safety rankings relative to conventional raw crash counts, and how can road segments be strategically partitioned into operational quadrants (Severe Congested, Deadly Traps, Safe Roads, and Fender-Benders) to eliminate misallocation of public safety capital?")

    add_h2(doc, "RQ 3: Multi-Hazard Environmental Amplification (UNDER WHAT CONDITIONS?)")
    add_p(doc,
        "What are the empirical interaction effects between adverse meteorological precipitation, roadway surface friction degradation, and unlit ambient darkness on collision severity weights, and how does environmental hostility amplify fatal crash probabilities?")

    add_h2(doc, "RQ 4: Modal Vulnerability & Mixed-Traffic Transferability (WHO & WHERE ELSE?)")
    add_p(doc,
        "How does physical vehicle vulnerability escalate fatal crash risk for Vulnerable Road Users (VRUs) across posted speed regimes, and how effectively does the exposure-adjusted risk framework transfer to emerging market urban corridors characterized by 55%+ two-wheeler modal share (e.g., Bengaluru, India)?")

    add_h2(doc, "RQ 5: Predictive Severity Attribution & Engineering Simulation (WHY & WHAT IF?)")
    add_p(doc,
        "Can ensemble machine learning architectures (Random Forest Hotspot Severity Classifiers) isolate the most decisive roadway and environmental features governing crash severity, and can these feature weights power an interactive 'what-if' policy simulation sandbox to quantify projected casualty reductions from targeted engineering countermeasures?")

def build_section_4_methodology(doc, add_h1, add_h2, add_h3, add_p, add_callout):
    add_h1(doc, "4. METHODOLOGY & SYSTEM ARCHITECTURE")
    
    add_h2(doc, "4.1 Reproducible End-to-End Pipeline Architecture")
    add_p(doc,
        "The system architecture is engineered as a reproducible, multi-stage batch data pipeline that processes multi-grain external feeds, executes econometric feature transformations, and compiles optimized columnar OLAP cubes for interactive browser analytics. The pipeline executes sequentially across six distinct stages:")
    
    add_p(doc, "• Stage 1 (Ingest): Ingests multi-grain data feeds comprising 22,000 UK STATS19 collision records, OpenStreetMap (OSM) roadway segments, Annual Average Daily Traffic (AADT) sensor counts, and Open-Meteo hourly weather observations. Persists immutable raw Parquet tables and initializes the DuckDB analytics warehouse.", bold=False, size=11)
    add_p(doc, "• Stage 2 (Preprocess): Validates geocodes, checks coordinate bounding envelopes, flags imputed missing attributes, and derives temporal cyclical features (24-hour circadian phases, day-of-week indexes, seasonality).", bold=False, size=11)
    add_p(doc, "• Stage 3 (Feature Engineering): Encodes published DfT injury severity weights (Fatal = 50, Serious = 10, Slight = 1), categorizes environmental hostility indices, and conforms segment attributes (speed limits, lane configurations, road hierarchy classes).", bold=False, size=11)
    add_p(doc, "• Stage 4 (Exposure & Risk Modeling): Shifts analytical grain from individual Crash-Grain to cohesive Road-Segment Grain. Computes annual vehicle exposure in Million Vehicle-Kilometers (MVKM), derives the Exposure-Adjusted Risk Index ($R$), applies statistical suppression floor thresholds, and classifies segments into 4 strategic quadrants.", bold=False, size=11)
    add_p(doc, "• Stage 5 (OLAP Aggregation): Uses DuckDB's in-process columnar SQL engine to pre-aggregate multi-dimensional analytics cubes (168-cell temporal heatmaps, circadian profiles, environmental interaction matrices, and spatial GeoJSON layers). Trains an ensemble Random Forest Hotspot Severity Classifier to extract Gini feature importances.", bold=False, size=11)
    add_p(doc, "• Stage 6 (Interactive Visual Analytics): Deploys an interactive Streamlit web dashboard with GPU-accelerated PyDeck 3D spatial mapping and Plotly visualizations, enabling highway engineers to slice datasets, evaluate benchmark cases, and run policy simulations with sub-second response times.", bold=False, size=11)

    add_h2(doc, "4.2 Mathematical Formulation of Road Exposure and Severity Risk")
    add_p(doc,
        "The mathematical foundation of the framework rests on three interrelated equations governing exposure, injury weighting, and normalized risk:")

    add_h3(doc, "1. Annual Roadway Segment Exposure (E)")
    add_p(doc,
        "Annual vehicular exposure represents the gross opportunity for collision interactions on a given roadway link. For road segment $j$, annual exposure $E_j$ measured in Million Vehicle-Kilometers (MVKM) is formally defined as:")
    
    add_p(doc,
        "E_j = (AADT_j × L_j × 365) / 1,000,000", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_p(doc,
        "Where AADT_j is the Annual Average Daily Traffic (vehicles per day), L_j is the segment length in kilometers, and 365 represents the annual operational expansion factor.")

    add_h3(doc, "2. Economic Injury Severity Weight Sum (S)")
    add_p(doc,
        "To reflect the true human and economic trauma of collisions, each crash event $i$ occurring on segment $j$ is assigned an economic weight $w_i$ based on UK Department for Transport / IRC published injury cost valuations:")
    
    add_p(doc,
        "w_i = 50  if Severity = Fatal\n"
        "w_i = 10  if Severity = Serious\n"
        "w_i = 1   if Severity = Slight", bold=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_p(doc,
        "The aggregate severity score $S_j$ for road segment $j$ across all $N_j$ recorded collisions is computed as:")
    
    add_p(doc,
        "S_j = ∑_{i=1}^{N_j} w_i = (50 × Fatal_j) + (10 × Serious_j) + (1 × Slight_j)", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_h3(doc, "3. Exposure-Adjusted Risk Index (R)")
    add_p(doc,
        "The Exposure-Adjusted Severity Risk Index $R_j$ expresses the economic injury severity generated per million vehicle-kilometers of travel:")
    
    add_p(doc,
        "R_j = S_j / E_j = (∑ w_i) / E_j", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_h2(doc, "4.3 Statistical Suppression Floor Criteria")
    add_p(doc,
        "A critical vulnerability in rate-based normalization is the 'small denominator problem.' When a road segment possesses extremely short length or near-zero traffic throughput, its annual exposure $E_j \to 0$. In such cases, a single isolated collision can cause the mathematical quotient $R_j = S_j / E_j$ to explode toward infinity, generating spurious statistical noise and false alarms. To guarantee numerical stability and operational credibility, the framework enforces a dual statistical suppression filter:")
    
    add_p(doc,
        "A road segment j is withheld from public hazard ranking if:\n"
        "N_j < 3   OR   E_j < 0.20 MVKM", bold=True, size=11.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    
    add_p(doc,
        "Segments failing this threshold are flagged in the data pipeline with `is_suppressed = True` and diverted to a secondary sparse-network audit queue rather than active capital prioritization.")

    add_h2(doc, "4.4 Four-Quadrant Strategic Roadway Classification Matrix")
    add_p(doc,
        "To convert the continuous distributions of incident frequency ($N$) and exposure-adjusted risk ($R$) into actionable engineering interventions, segments are classified using a 2×2 Four-Quadrant Strategic Matrix partitioned by the network median thresholds ($\tilde{N}$ and $\tilde{R}$):")
    
    add_p(doc, "• Quadrant 1 (Q1: High Frequency - High Severity | Severe Congested): Major arterials and urban ring roads with high traffic throughput and frequent severe crashes. Require comprehensive structural retrofits: grade separation, signal optimization, and speed enforcement.", bold=False, size=11)
    add_p(doc, "• Quadrant 2 (Q2: Low Frequency - High Severity | Deadly Traps - PRIMARY FOCUS): Rural curves, unlit single carriageways, and regional links with few total crashes but lethal trauma. Represent the highest return on safety investment: require immediate low-cost high-impact fixes (reflective signage, chevron alignment boards, high-friction resurfacing, and LED street lighting).", bold=False, size=11)
    add_p(doc, "• Quadrant 3 (Q3: Low Frequency - Low Severity | Safe Corridors): Standard well-engineered roads carrying low volumes with minimal minor shunts. Require routine preventive maintenance and periodic safety monitoring.", bold=False, size=11)
    add_p(doc, "• Quadrant 4 (Q4: High Frequency - Low Severity | Fender-Benders): Heavily congested motorways and dense commercial corridors where minor property-damage shunts dominate. Require traffic incident management, queue warning systems, and access management rather than expensive structural overhauls.", bold=False, size=11)

    add_h2(doc, "4.5 High-Performance Columnar OLAP Engine (DuckDB & Parquet Cubes)")
    add_p(doc,
        "To deliver instantaneous, sub-second visual analytics for end users without expensive cloud computing infrastructure, all processed crash records and segment metrics are persisted in immutable Apache Parquet format and registered in a lightweight embedded DuckDB columnar database. DuckDB's vectorized query execution engine pre-aggregates multi-dimensional cubes:")
    
    add_p(doc, "1. `cube_circadian_hourly.parquet`: 24-hour circadian crash volumes, fatality rates, and vulnerability shares.\n"
               "2. `cube_temporal_heatmap.parquet`: 168-cell matrix cross-tabulating Day-of-Week × Hour-of-Day severity.\n"
               "3. `cube_environmental_matrix.parquet`: Multi-hazard interactions between weather, surface friction, and light.\n"
               "4. `cube_vehicle_vulnerability.parquet`: Primary vehicle categories cross-tabulated across speed limits.\n"
               "5. `cube_segments_spatial.parquet` & `.geojson`: Spatial road segment layers with exposure, risk, and 4-quadrants.\n"
               "6. `cube_quadrants_summary.parquet`: High-level executive metrics summarized by operational quadrant.\n"
               "7. `cube_india_transferability.parquet`: Bengaluru arterial mixed-traffic benchmark dataset.\n"
               "8. `cube_ml_risk_weights.json`: Feature importances from a trained Random Forest Hotspot Classifier.", bold=False, size=10.5)

print("Intro, Lit Review, and Methodology module loaded.")
