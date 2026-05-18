"""
borderline_decisions.py — Decisions humaines sur les 48 articles BORDERLINE V3

Apres analyse manuelle de chaque titre + abstract complet.

Logique :
- INCLURE si : DT/CPS clairement central + scope batiment individuel + validation
- EXCLURE si : scope urbain/district dominant, framework purement theorique,
  ou validation explicitement absente
"""

import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
INPUT = BASE / "results_screening" / "screening_v3_borderline.csv"
OUTPUT = BASE / "results_screening" / "screening_v3_borderline_decisions.csv"
FINAL = BASE / "results_screening" / "screening_v3_final.csv"

# ----------------------------------------------------------------------
# Decisions humaines : index -> (decision, motif)
# ----------------------------------------------------------------------
BORDERLINE_DECISIONS = {
    6: ("INCLURE", "CPS multi-niveau pour AC cluster, validation, batiment public"),
    10: ("INCLURE", "Real-world experiments office, 47.92% savings, CPS deploye"),
    23: ("INCLURE", "DT explicite + LSTM, validation ASHRAE dataset (mon pilote)"),
    25: ("INCLURE", "HIL testbed CPS smart commercial buildings"),
    34: ("INCLURE", "DT explicite IoT residential, 98% accuracy validation"),
    54: ("INCLURE", "DT batiment energy flexibility, dispatch strategy"),
    60: ("EXCLURE", "ROM conceptuel sans validation propre, methodologique"),
    74: ("INCLURE", "DT heritage building, CFD simulation, single building"),
    76: ("EXCLURE", "Auteurs declarent 'no validation was performed' — disqualifiant"),
    78: ("INCLURE", "CPS Spanish school, 43 days winter validation, real data"),
    90: ("INCLURE", "CPS DMPC 6-story building 40 rooms, sim+practical"),
    99: ("INCLURE", "DT explicit office building case, BIM+IoT+ML"),
    101: ("EXCLURE", "'Digital twins of cities' dominant, district co-simulation"),
    102: ("EXCLURE", "Beijing intelligent communities urban scope explicite"),
    107: ("INCLURE", "DT explicit pour Building EPC scheme, framework documente"),
    111: ("INCLURE", "DT heritage HBIM workflow, Italian listed buildings"),
    122: ("EXCLURE", "LPS retrofit strategie multi-stock, pas DT operationnel"),
    132: ("INCLURE", "CPS+WiFi occupancy, ensemble classification validation"),
    139: ("INCLURE", "Physics-based DT + SiL simulation MPC building"),
    141: ("INCLURE", "DT explicit, 3 case studies (Heron+Veolia+Emotion)"),
    155: ("EXCLURE", "3 WEAKs, communication-focused, validation faible"),
    158: ("EXCLURE", "Smart grid focus dominant, buildings subordonnes"),
    162: ("INCLURE", "DT integration N79 zone analysis, IoT+ML"),
    185: ("INCLURE", "DT prototype U-shaped military building case study"),
    199: ("INCLURE", "DT 8500m2 university building, MPC HVAC validation"),
    235: ("INCLURE", "DT facility management, sensor calibration test campaign"),
    238: ("EXCLURE", "Urban superblocks Iran case studies, scope explicite"),
    248: ("INCLURE", "CPS smart building testbed MQTT+Node-RED, experimental"),
    272: ("INCLURE", "CPS open-space office HVAC, hybrid model validation"),
    275: ("EXCLURE", "Rome 16 buildings 216 apartments residential district"),
    278: ("INCLURE", "CPS dynamic modeling smart building, real-world validation"),
    296: ("INCLURE", "CPS HVAC case study smart building design"),
    311: ("EXCLURE", "Investment decision toolset, pas DT operation"),
    314: ("INCLURE", "DT public building Milano, iterative simulation"),
    323: ("INCLURE", "CPS smart home thermal comfort, simulation validation"),
    327: ("INCLURE", "CPS BAS benchmark library, 3 Oxford case studies"),
    346: ("INCLURE", "Hybrid DT multi-zone building EnergyPlus+GA"),
    350: ("EXCLURE", "178k buildings utility 1400km2 service area, city-scale"),
    356: ("INCLURE", "CPHS iHouse predictive thermal comfort"),
    363: ("INCLURE", "Physics-based DT + SiL real measurement data"),
    371: ("EXCLURE", "Framework theorique sans validation propre"),
    372: ("INCLURE", "DT existing office building case Modelica BEM"),
    373: ("INCLURE", "Physics-based DT + SiL hierarchical MPC"),
    379: ("INCLURE", "CPS thermostatic zoning HVAC, extensive simulations"),
    385: ("INCLURE", "CPHS adaptive MPC iHouse, real env data"),
    530: ("EXCLURE", "Energy management 'city and nation' national scale"),
    535: ("INCLURE", "DT-towards Hale Court sheltered housing case study"),
    547: ("INCLURE", "CPS commercial building case study closed-loop sim"),
}


def main():
    bd = pd.read_csv(INPUT)
    print(f"Input : {len(bd)} BORDERLINEs")
    assert len(bd) == len(BORDERLINE_DECISIONS), \
        f"Mismatch : {len(bd)} dans CSV vs {len(BORDERLINE_DECISIONS)} decisions"

    bd["decision_v3_human"] = bd["index"].apply(
        lambda i: BORDERLINE_DECISIONS.get(int(i), ("?", "?"))[0]
    )
    bd["motif_v3_human"] = bd["index"].apply(
        lambda i: BORDERLINE_DECISIONS.get(int(i), ("?", "?"))[1]
    )

    # Stats
    print("\n=== Distribution des decisions ===")
    print(bd["decision_v3_human"].value_counts().to_dict())

    bd.to_csv(OUTPUT, index=False)
    print(f"\nSauve : {OUTPUT}")

    # Construction du fichier final
    full = pd.read_csv(BASE / "results_screening" / "screening_v3_strict.csv")

    # decision finale par article :
    #  - INCLUDE_AUTO -> INCLURE
    #  - EXCLUDE_AUTO -> EXCLURE
    #  - BORDERLINE -> selon decision humaine
    def final_decision(row):
        if row["bucket_v3"] == "INCLUDE_AUTO":
            return "INCLURE"
        if row["bucket_v3"] == "EXCLUDE_AUTO":
            return "EXCLURE"
        # BORDERLINE
        return BORDERLINE_DECISIONS.get(int(row["index"]), ("?", "?"))[0]

    def final_motif(row):
        if row["bucket_v3"] == "INCLUDE_AUTO":
            return "Tous criteres PASS"
        if row["bucket_v3"] == "EXCLUDE_AUTO":
            fails = []
            for c in ["C1_dt", "C2_validation", "C3_abstract", "C4_scope"]:
                if row[c] == "FAIL":
                    fails.append(c)
            return f"FAIL on {','.join(fails)}"
        return BORDERLINE_DECISIONS.get(int(row["index"]), ("?", "?"))[1]

    full["decision_v3_final"] = full.apply(final_decision, axis=1)
    full["motif_v3_final"] = full.apply(final_motif, axis=1)

    full.to_csv(FINAL, index=False)
    print(f"\nSauve final : {FINAL}")

    # Stats final
    print("\n=== DECISIONS FINALES ===")
    print(full["decision_v3_final"].value_counts().to_dict())

    # Export des inclus uniquement
    incl_final = full[full["decision_v3_final"] == "INCLURE"]
    incl_path = BASE / "results_screening" / "included_papers_v3_for_fulltext.csv"
    incl_final.to_csv(incl_path, index=False)
    print(f"\nFichier des inclus pour full-text : {incl_path}")
    print(f"Total inclus V3 : {len(incl_final)} articles")


if __name__ == "__main__":
    main()
