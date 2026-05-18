"""
fulltext_screening_decisions.py — Decisions du screening full-text

Pour chaque article V3 ayant un PDF disponible, decision Include/Exclude
basee sur lecture du PDF (abstract + intro + methodologie + conclusion).

Pour les articles V3 sans PDF disponible (44 cas), classes en
EXCLUDE_NO_PDF (motif : full-text non recupere).
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent
V3 = BASE / "results_screening" / "included_papers_v3_for_fulltext.csv"
OUTPUT = BASE / "results_screening" / "fulltext_screening_results.csv"

# ----------------------------------------------------------------------
# Decisions humaines (51 articles avec PDF)
# Format : idx -> (decision, kritzinger, building_scope, validation, domain, motif)
# ----------------------------------------------------------------------
DECISIONS = {
    6:   ("INCLURE", "Shadow", "individual",          "simulation_only",     "HVAC",         "CPS multi-niveau pour AC cluster, MOPSO optimization, case study, demand response 92%"),
    24:  ("INCLURE", "Twin",   "individual",          "real_deployment",     "ENERGY_MGMT",  "DT real-time + offline + IAQ + thermal + electricity, validated <1% error in real building"),
    25:  ("INCLURE", "Twin",   "individual",          "testbed",             "ENERGY_MGMT",  "HIL testbed CPS smart commercial buildings, DOE prototype, BAS controllers"),
    30:  ("EXCLURE", "Model",  "district",            "simulation_only",     "ENERGY_MGMT",  "Multi-region household energy forecasting (Diyarbakir+Istanbul+Odemis) — echelle multi-regional, hors scope batiment individuel"),
    33:  ("INCLURE", "Twin",   "individual",          "pilot",               "HVAC",         "Thermal modeling existing buildings, novel methodology, case study, validation real building"),
    42:  ("INCLURE", "Twin",   "individual",          "real_deployment",     "COMFORT",      "DT+IoT+BIM platform thermal comfort, case study real building, FB Prophet/NeuralProphet"),
    53:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "COMFORT",      "Co-zyBench DT benchmarking tool, building+occupant DTs, co-simulation, real building reference"),
    54:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "ENERGY_MGMT",  "DT-based BEF dispatch strategy, simulation 98.4% ideal, parameter fault tolerance"),
    67:  ("INCLURE", "Shadow", "individual",          "pilot",               "ENERGY_MGMT",  "BIM+IoT integration, real-time data, case study Italy, Revit+Dynamo+API"),
    68:  ("EXCLURE", "n/a",    "n/a",                 "n/a",                 "n/a",          "Article de revue (Review) — pas d'etude primaire propre"),
    72:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "HVAC",         "Multi-indicator HBIM-DT adaptive HVAC IAQ heritage, CFD simulation, 30% energy savings"),
    74:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "STRUCTURAL",   "DT-HBIM heritage thermal performance, CFD+structural, 62.9% deformation reduction"),
    78:  ("INCLURE", "Twin",   "individual",          "real_deployment",     "HVAC",         "CPS Spanish school heating system, 43 days winter 2015/2016, energy savings 1/3"),
    88:  ("INCLURE", "Shadow", "individual",          "pilot",               "HVAC",         "Data-driven thermal zoning DT-enabled, large educational building 168 rooms 262 sensors"),
    89:  ("INCLURE", "Twin",   "individual",          "pilot",               "ENERGY_MGMT",  "DT O&M platform campus building (BIM education center), IoT+smart meter, BP NN"),
    94:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "RENEWABLES_STORAGE", "DT thermal energy storage Phase Change Material, intelligent building, simulation"),
    99:  ("INCLURE", "Twin",   "individual",          "simulation_only",     "ENERGY_MGMT",  "DT framework BIM+IoT office building, DesignBuilder simulation, 30% max savings"),
    106: ("INCLURE", "Shadow", "individual",          "simulation_only",     "ENERGY_MGMT",  "DT NZEB existing buildings, BIM+hierarchy-flow chart, UK case study, 23 year ROI"),
    112: ("INCLURE", "Shadow", "individual",          "real_deployment",     "ENERGY_MGMT",  "Lean DT building energy monitoring TRV+GAHP, M&V regression rolling horizon"),
    114: ("INCLURE", "Twin",   "individual",          "simulation_only",     "ENVELOPE",     "DT white-box BEM educational building, blind control passive heating, EnergyPlus, real weather"),
    121: ("INCLURE", "Twin",   "individual",          "pilot",               "MAINTENANCE",  "DT framework fault detection comfort BIM+sensors+BN, 2 case studies Norway 2019-2022"),
    124: ("INCLURE", "Twin",   "individual",          "real_deployment",     "HVAC",         "Multi-stage calibration DT cold chain logistics center, EnergyPlus+PSO, real-world building"),
    132: ("INCLURE", "Shadow", "individual",          "real_deployment",     "ENERGY_MGMT",  "Energy-CPS occupancy WiFi probe, ensemble classification, 26.4% energy saving experiment"),
    139: ("INCLURE", "Twin",   "individual",          "simulation_only",     "ENERGY_MGMT",  "Hierarchical MPC physics-based DT, multi-zone commercial building, SiL simulation"),
    142: ("INCLURE", "Twin",   "individual",          "real_deployment",     "HVAC",         "DT model calibration HVAC ADNM, validated with real HVAC data, RMSE -60-70% vs traditional NM"),
    144: ("EXCLURE", "Twin",   "multi-bldg",          "pilot",               "MAINTENANCE",  "Mega-facilities (hospitals + airports), multi-buildings cases, hors scope batiment individuel"),
    150: ("INCLURE", "Twin",   "individual",          "pilot",               "COMFORT",      "DT virtual sensors real-time indoor comfort, BES+CFD coupling, test facility validation"),
    153: ("INCLURE", "Twin",   "individual",          "real_deployment",     "HVAC",         "DT predictive ASHP heat pump FCPM-SBLS, railway passenger station, MAE 0.045"),
    166: ("INCLURE", "Shadow", "individual",          "simulation_only",     "ENERGY_MGMT",  "DT residential building Chalmers student house, synthesised data, agent-based simulation"),
    170: ("INCLURE", "Twin",   "individual",          "simulation_only",     "COMFORT",      "Multi-Obj GA DT thermal comfort + energy, ANN surrogate, 25% HVAC energy reduction"),
    189: ("INCLURE", "Shadow", "individual",          "pilot",               "COMFORT",      "Early DT BIM-IoT IAQ + thermal comfort, HTML reports automated, pilot case study"),
    193: ("INCLURE", "Twin",   "individual",          "pilot",               "COMFORT",      "Smart Building DT IoT, lighting+HVAC+IAQ + ML, case study Sapienza Rome"),
    195: ("INCLURE", "Shadow", "individual",          "real_deployment",     "HVAC",         "Deep learning prediction indoor temperatures DT-HVAC, educational building, real data, RMSE 0.16C"),
    199: ("INCLURE", "Twin",   "individual",          "simulation_only",     "HVAC",         "Multi-Obj MPC ventilation 8500m2 university building DT, 18-24% energy savings"),
    200: ("EXCLURE", "Model",  "individual",          "simulation_only",     "n/a",          "BIM+BPS-based DSS for built heritage, DT vision is FUTURE not implemented (foundations laid only)"),
    215: ("EXCLURE", "Model",  "individual",          "pilot",               "n/a",          "Thermal images + point cloud fusion for wall T uniformity. DT mentioned only as future foundation, pas DT implementé"),
    226: ("INCLURE", "Twin",   "individual",          "pilot",               "COMFORT",      "BIM-based thermo-hygrometric DT, real-time monitoring office building Living Lab"),
    235: ("INCLURE", "Shadow", "individual",          "pilot",               "MAINTENANCE",  "Occupancy DT facility management, IoT camera-based, calibration test campaign Politecnico Milano"),
    250: ("INCLURE", "Twin",   "individual",          "simulation_only",     "ENERGY_MGMT",  "Scalable IoT-DT home energy management, parametric 3D models, simulation framework"),
    258: ("INCLURE", "Twin",   "individual",          "pilot",               "ENERGY_MGMT",  "DT Lazio Region HQ space management, BIM+IoT+AI+ML, 530.40 MWh/year savings"),
    261: ("INCLURE", "Twin",   "individual",          "real_deployment",     "ENERGY_MGMT",  "Large-scale field demo ontology DT building, hospital floor 12 zones 45 sensors, MAE 0.40C"),
    270: ("INCLURE", "Twin",   "individual",          "simulation_only",     "COMFORT",      "DT-Enabled BIM-IoT framework MPC indoor thermal comfort, sPMV + LSTM hybrid"),
    272: ("INCLURE", "Shadow", "individual",          "simulation_only",     "COMFORT",      "Cyber-enabled HVAC optimization open-space office, ANN+SVM, 43-69% comfort improvement"),
    306: ("INCLURE", "Twin",   "individual",          "pilot",               "OTHER",        "DT acoustics + stagecraft multipurpose hall (niche), reverberation time control real-time"),
    307: ("INCLURE", "Twin",   "individual",          "simulation_only",     "HVAC",         "DT hotel TRNSYS BEM, 5-story hotel Northern Italy, summer monitoring, control strategies"),
    327: ("INCLURE", "Twin",   "individual",          "testbed",             "ENERGY_MGMT",  "CPS BAS modular model library, Oxford BAS real setup, 3 case studies, benchmarks"),
    341: ("INCLURE", "Twin",   "individual",          "pilot",               "HVAC",         "DT Design HVAC ERV unit, Modelica DTI + physical twin, MQTT, predictive maintenance"),
    366: ("INCLURE", "Twin",   "individual",          "testbed",             "ENERGY_MGMT",  "Cloud-based HIL DT building automation controllers, KPI evaluation, virtual vs hardware"),
    535: ("INCLURE", "Shadow", "individual",          "real_deployment",     "ENERGY_MGMT",  "Energy signature DT TRV+GAHP, Hale Court before/after retrofit, 3 monitoring periods"),
    542: ("EXCLURE", "n/a",    "n/a",                 "n/a",                 "n/a",          "Industry case study (Willow Inc) - peer-review status non clair, narrative-style article"),
    547: ("INCLURE", "Shadow", "individual",          "simulation_only",     "ENERGY_MGMT",  "Data-driven predictive control commercial buildings CPS, RF, large office closed-loop sim"),
}


def main():
    v3 = pd.read_csv(V3)
    v3['idx'] = v3['index'].astype(int)

    # PDFs disponibles
    pdf_indices = {int(f.stem.split('_')[0]) for f in (BASE / "fulltexts").glob("*.pdf")}

    rows = []
    for _, r in v3.iterrows():
        idx = int(r['index'])
        title = str(r['Title'])
        year = int(r['Year']) if pd.notna(r['Year']) else 0
        doi = str(r.get('DOI',''))
        if idx in pdf_indices:
            if idx in DECISIONS:
                dec, kr, sc, val, dom, motif = DECISIONS[idx]
            else:
                dec, kr, sc, val, dom, motif = ("PENDING", "?", "?", "?", "?", "Article a screen")
            pdf_status = "AVAILABLE"
        else:
            dec, kr, sc, val, dom, motif = ("EXCLURE_NO_PDF", "n/a", "n/a", "n/a", "n/a",
                                              "Full-text non disponible (acces institutionnel limite, ex: IEEE)")
            pdf_status = "MISSING"

        rows.append({
            'index': idx,
            'title': title,
            'year': year,
            'doi': doi,
            'pdf_status': pdf_status,
            'fulltext_decision': dec,
            'kritzinger_level': kr,
            'building_scope': sc,
            'validation_type': val,
            'domain': dom,
            'motif': motif,
        })

    df = pd.DataFrame(rows).sort_values('index')
    df.to_csv(OUTPUT, index=False)

    # stats
    print(f"=== DECISIONS FULL-TEXT (n={len(df)}) ===")
    print(df['fulltext_decision'].value_counts().to_dict())

    incl = df[df['fulltext_decision']=='INCLURE']
    print(f"\nArticles INCLURE final : {len(incl)}")
    print(f"\nRepartition par domaine :")
    print(incl['domain'].value_counts().to_dict())
    print(f"\nRepartition par Kritzinger level :")
    print(incl['kritzinger_level'].value_counts().to_dict())
    print(f"\nRepartition par validation type :")
    print(incl['validation_type'].value_counts().to_dict())

    print(f"\nFichier sauve : {OUTPUT}")


if __name__ == "__main__":
    main()
