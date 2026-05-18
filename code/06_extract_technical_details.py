"""
extract_technical_details.py — Extraction d'aspects techniques des 45 PDFs inclus

Pour chaque article, scanne le texte du PDF et detecte :
  - Langages de programmation (Python, MATLAB, R, etc.)
  - Frameworks de simulation (EnergyPlus, TRNSYS, Modelica, etc.)
  - Protocoles de communication (MQTT, OPC-UA, BACnet, REST, etc.)
  - Plateformes DT (Azure DT, Eclipse Ditto, etc.)
  - Methodes ML (LSTM, RF, MPC, RL, etc.)
  - Types de simulation (CFD, FEM, agent-based, co-simulation, etc.)
  - Capteurs IoT specifiques
  - Type de validation (real, pilot, sim, testbed)

Sortie : extraction/technical_extraction.csv
"""

import pdfplumber, pandas as pd, re
from pathlib import Path

BASE = Path(__file__).parent
INCL = BASE / "results_screening" / "fulltext_screening_results.csv"
OUT = BASE / "extraction" / "technical_extraction.csv"

# Patterns techniques (insensibles a la casse)
PATTERNS = {
    # langages
    "python": r"\b(python|jupyter|notebook|scikit[\-\s]?learn|sklearn|pandas|numpy|tensorflow|pytorch|keras)\b",
    "matlab": r"\b(matlab|simulink)\b",
    "r_lang": r"\b(\sR\sstatistical|R\spackage|RStudio)\b",
    "java": r"\bjava(?!script)\b",
    "javascript": r"\b(javascript|node[\-\s]?js|node\.js)\b",
    "cpp": r"\bC\+\+|cpp\b",

    # simulation engines
    "energyplus": r"\b(energy[\-\s]?plus|energyplus|EnergyPlus)\b",
    "trnsys": r"\bTRNSYS\b",
    "modelica": r"\b(modelica|dymola|openmodelica)\b",
    "openstudio": r"\b(open[\-\s]?studio|OpenStudio)\b",
    "ida_ice": r"\bIDA[\-\s]?ICE\b",
    "designbuilder": r"\bdesign[\-\s]?builder\b",
    "espr": r"\bESP[\-\s]?r\b",
    "ansys_fluent": r"\b(ansys\s*fluent|ansys|fluent)\b",
    "openfoam": r"\bopen[\-\s]?foam\b",

    # CAD / BIM
    "revit": r"\b(revit|autodesk\s*revit)\b",
    "ifc": r"\b(IFC|industry\s*foundation\s*classes)\b",
    "dynamo": r"\b(dynamo)\b",
    "rhino": r"\b(rhinoceros|rhino[\-\s]?\d)\b",

    # plateformes DT
    "azure_dt": r"\b(azure\s*digital\s*twins?|adt)\b",
    "eclipse_ditto": r"\beclipse\s*ditto\b",
    "aws_iot": r"\b(AWS\s*IoT|amazon\s*web\s*services)\b",
    "ibm_maximo": r"\bIBM\s*maximo\b",

    # protocoles communication
    "mqtt": r"\bMQTT\b",
    "opc_ua": r"\bOPC[\-\s]?UA\b",
    "bacnet": r"\bBACnet\b",
    "rest_api": r"\bREST(?:\s|ful|\sAPI|API)\b",
    "http": r"\bHTTP[/]?\b",
    "coap": r"\bCoAP\b",
    "modbus": r"\bmodbus\b",
    "knx": r"\bKNX\b",
    "zigbee": r"\bzigbee\b",
    "lorawan": r"\blora[\-\s]?wan\b|\blora\b",
    "websocket": r"\bweb[\-\s]?socket\b",
    "fmi_fmu": r"\bFMI\b|\bFMU\b|functional\s*mock[\-\s]?up",

    # ML / control
    "lstm": r"\bLSTM\b",
    "bilstm": r"\bBi[\-\s]?LSTM\b",
    "transformer": r"\btransformer(?:\s*model|s)?\b|\battention\s*mechanism\b",
    "cnn": r"\b(CNN|convolutional\s*neural)\b",
    "rf_ensemble": r"\b(random\s*forest|gradient\s*boost|xgboost|adaboost)\b",
    "ann": r"\b(ANN|artificial\s*neural\s*network|deep\s*neural\s*network|MLP|multilayer)\b",
    "rnn": r"\bRNN\b|\brecurrent\s*neural\b",
    "rl": r"\b(reinforcement\s*learning|Q[\-\s]?learning|deep\s*q[\-\s]?network|DQN|fitted\sQ)\b",
    "mpc": r"\b(model\s*predictive\s*control|MPC)\b",
    "ga": r"\b(genetic\s*algorithm|NSGA[\-\s]?I+|GA\s*optimization)\b",
    "pso": r"\b(particle\s*swarm|PSO\b|MOPSO)\b",
    "bayesian": r"\b(bayesian\s*(?:network|optimization|regulariz|inference)|gaussian\s*process)\b",
    "transfer_learning": r"\btransfer\s*learning\b",

    # types de simulation
    "cfd_sim": r"\b(CFD|computational\s*fluid\s*dynamics)\b",
    "fem": r"\b(FEM|finite\s*element\s*method|finite\s*element\s*analysis|FEA)\b",
    "agent_based": r"\b(agent[\-\s]?based\s*(?:model|simulation)|ABM)\b",
    "co_simulation": r"\bco[\-\s]?simulation\b|\bco[\-\s]?simulator\b",
    "rom_reduced_order": r"\b(reduced[\-\s]?order\s*model|ROM\b)\b",
    "monte_carlo": r"\bmonte[\-\s]?carlo\b",

    # capteurs / IoT
    "iot_general": r"\binternet\s*of\s*things\b|\bIoT\b",
    "wifi_probe": r"\bWi[\-\s]?Fi\s*probe\b",
    "ble_bluetooth": r"\b(bluetooth|BLE\b)\b",
    "raspberry_pi": r"\b(raspberry[\-\s]?pi|RPi)\b",
    "arduino": r"\barduino\b",
    "esp32": r"\b(ESP[\s\-]?32|ESP[\s\-]?8266|nodeMCU)\b",
    "lidar_scanner": r"\b(LiDAR|laser\s*scanner|3D\s*scanning|point\s*cloud)\b",

    # types de capteurs
    "temp_sensor": r"\b(temperature\s*sensor|thermocouple|DHT2[12]|PT100|LM35)\b",
    "co2_sensor": r"\b(CO2\s*sensor|SCD30|MHZ19)\b",
    "occupancy_pir": r"\b(PIR|passive\s*infrared|occupancy\s*sensor)\b",
    "camera_sensor": r"\b(camera[\-\s]?based|CCTV|image\s*recognition)\b",
    "energy_meter": r"\b(smart\s*meter|energy\s*meter|kWh\s*meter)\b",

    # validation
    "hil": r"\bhardware[\-\s]?in[\-\s]?the[\-\s]?loop\b|\bHIL\b",
    "sil": r"\bsoftware[\-\s]?in[\-\s]?the[\-\s]?loop\b|\bSiL\b",
    "real_deployment": r"\b(real[\-\s]?world\s*deployment|field\s*deployment|operational\s*deployment|deployed\s*in)\b",
    "case_study": r"\bcase[\-\s]?stud(?:y|ies)\b",
    "testbed": r"\btest[\-\s]?bed\b",

    # autres
    "ontology": r"\bontolog(?:y|ies|ical)\b",
    "knowledge_graph": r"\bknowledge\s*graph\b",
    "blockchain": r"\bblockchain\b",
    "edge_computing": r"\bedge\s*computing\b",
    "fog_computing": r"\bfog\s*computing\b",
    "cloud_computing": r"\bcloud\s*(?:computing|service|platform)\b",
    "cybersec": r"\b(cyber[\-\s]?security|cyber[\-\s]?attack)\b",
}


def extract_pdf_text(pdf_path):
    """Texte des 5 premieres pages + 3 dernieres pages (concl/refs).

    NB : on NE collapse PAS les lettres doublees (regex `\w\1+`) car cela
    detruit les acronymes techniques avec lettres doublees (MQTT, HTTP, RNN,
    BACnet a-t-il de doubles ? non. mais OPC-UA, etc.). On accepte le bruit
    d'extraction PDF (artefacts type 'tthhee') car les patterns regex sont
    suffisamment specifiques.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            n = len(pdf.pages)
            front = " ".join((p.extract_text() or "") for p in pdf.pages[:5])
            back = " ".join((p.extract_text() or "") for p in pdf.pages[max(0,n-3):])
        return front + " " + back
    except Exception as e:
        return ""


def detect_patterns(text, patterns):
    """Pour chaque pattern, retourne True si present."""
    results = {}
    for name, pat in patterns.items():
        results[name] = bool(re.search(pat, text, re.I))
    return results


def main():
    incl = pd.read_csv(INCL)
    incl = incl[incl['fulltext_decision'] == 'INCLURE'].copy()
    incl['idx'] = incl['index'].astype(int)

    rows = []
    for _, r in incl.iterrows():
        idx = int(r['idx'])
        pdf_files = list((BASE / "fulltexts").glob(f"{idx:04d}*.pdf"))
        if not pdf_files:
            continue
        text = extract_pdf_text(pdf_files[0])
        if not text:
            continue
        flags = detect_patterns(text, PATTERNS)
        row = {'idx': idx, 'title': r['title'][:80], 'year': r['year'],
                'category': r.get('domain', '?')}
        row.update(flags)
        rows.append(row)
        print(f"[{idx:03d}] processed", end=" ", flush=True)
        if len(rows) % 10 == 0: print()

    print()
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(f"\nTotal articles processes : {len(df)}")
    print(f"Sortie : {OUT}")

    # Stats : presence par technique
    print(f"\n=== TAUX DE DETECTION (% des 45 articles ou la techno est mentionnee) ===")
    for col in PATTERNS.keys():
        n = df[col].sum()
        pct = n / len(df) * 100
        if n >= 1:  # au moins 1 article
            print(f"  {col:25s} {n:3d}/{len(df)} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
