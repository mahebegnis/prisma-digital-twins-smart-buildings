# Digital Twins for Smart Buildings — A PRISMA 2020 Systematic Review

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PRISMA 2020](https://img.shields.io/badge/PRISMA-2020-success.svg)](http://www.prisma-statement.org/)

> **The Role of Digital Twins in Energy Optimization and Smart Building Management: A Systematic Review using PRISMA**
> Master 1 Data & Artificial Intelligence — Université Catholique de Lille — École du Numérique — May 2026

**Authors:** BEGNIS Mahé · RAYANE Rémy · BENSALEM Jibril · SIGNATE Maïmouna · DAGAR Vaneck

---

## What this repository contains

This repository hosts the **complete materials** of a PRISMA 2020 systematic review on Digital Twins for energy optimization in smart buildings (2015–2025), including:

- The final **IEEE-formatted article** (29 pages, 52 references, 361 clickable hyperlinks)
- The full **Python pipeline** (7 scripts) of the multi-stage screening procedure
- The **decision CSVs** at each pipeline step (548 → 167 → 130 → 45 articles)
- The **technical mapping** of all 45 included studies for RQ4 (80 regex patterns × 45 articles)

## Repository structure

```
.
├── README.md                          ← this file
├── LICENSE                            ← CC BY 4.0
├── CITATION.cff                       ← machine-readable citation
├── .gitignore
├── requirements.txt                   ← Python dependencies
├── article/                           ← main deliverable
│   ├── article_FINAL.pdf              ← final article (29 p, IEEE format, clickable refs)
│   ├── PRISMA_flow_diagram.png        ← Figure 1 (raster)
│   └── PRISMA_flow_diagram.pdf        ← Figure 1 (vector)
├── code/                              ← PRISMA pipeline scripts
│   ├── 01_pipeline_complet.py
│   ├── 02_screening_v3_strict.py
│   ├── 03_borderline_decisions.py
│   ├── 04_fetch_pdfs.py
│   ├── 05_fulltext_screening_decisions.py
│   ├── 06_extract_technical_details.py
│   └── 07_prisma_flow_diagram.py
└── data/                              ← CSV artefacts (each pipeline step)
    ├── 01_corpus_unified_screening_ready.csv      ← 548 deduplicated records
    ├── 02_screening_results_v2_corrected.csv      ← V2 LLM (548 → 167)
    ├── 03_screening_v3_final.csv                  ← V3 strict (167 → 130)
    ├── 04_screening_v3_borderline_decisions.csv   ← 48 borderline decisions
    ├── 05_fulltext_screening_results.csv          ← 130 with retrieval status
    ├── 06_included_papers_v4_classified.csv       ← 45 included + classification
    └── 07_technical_extraction.csv                ← 45 × 80 RQ4 patterns
```

## PRISMA 2020 pipeline

```
704  raw records (Scopus 343 + WoS 150 + SpringerNature 144 + IEEE 67)
─────  −156 duplicates (DOI then Title+Year)
548  unified deduplicated corpus
─────  −381 V2 LLM-assisted title+abstract (validated by all 5 members)
167  candidates
─────  −37 V3 strict (4 cumulative criteria)
130  for full-text retrieval
─────  −79 paywall (mainly IEEE conferences)
51   full-text PDFs read
─────  −6 documented full-text exclusions (validated by all 5 members)
45   studies included in the qualitative synthesis
```

## Four research questions

| RQ | Question | Tables in article |
|---|---|---|
| **RQ1** | DT use categories for Smart Buildings | 3, 4 |
| **RQ2** | Effectiveness (energy, comfort, cost) and reported KPIs | 2, 5 |
| **RQ3** | Challenges and technical limitations | 6 |
| **RQ4** | Technical tools and methods actually mobilized | 7, 8 |

## Key findings

- **4 thematic categories**: Energy consumption & supervision (71 %), Indoor Comfort & IAQ (20 %), Maintenance & Structural Health (7 %), Specialized Applications (2 %)
- **Kritzinger taxonomy**: 71 % implement a true Twin, 29 % remain at Shadow level
- **Reported energy savings**: 15–33 %, median ≈ 22 %
- **Dominant stack** (RQ4): EnergyPlus (33 %), Python (27 %), MPC (49 %)
- **Critical research gap**: **0 / 45** studies in tropical maritime, ultra-marine, or coastal climates — motivating a future pilot DT for a bioclimatic building in such a context

## How to reproduce the pipeline

```bash
# Clone the repository
git clone https://github.com/mahebegnis/prisma-digital-twins-smart-buildings.git
cd prisma-digital-twins-smart-buildings

# Install dependencies (Python 3.10+ required)
pip install -r requirements.txt

# Run the pipeline (steps 01 → 07)
python code/01_pipeline_complet.py
python code/02_screening_v3_strict.py
python code/03_borderline_decisions.py
python code/04_fetch_pdfs.py
python code/05_fulltext_screening_decisions.py
python code/06_extract_technical_details.py
python code/07_prisma_flow_diagram.py
```

**Reproducibility note**: the pipeline is **fully reproducible up to V3 screening** (steps 01–03). The full-text screening (step 05) is **partially reproducible** because LLM reading is not strictly deterministic; however, every decision is documented with a rationale in the corresponding CSV.

## Data not included (publisher copyright)

For copyright reasons, this repository does **NOT** redistribute:

- The 45 full-text PDFs of the included studies
- The raw export CSVs from the 4 databases (Scopus, WoS, IEEE Xplore, SpringerNature)

All DOIs are provided in the bibliography of the article and in the CSVs, allowing independent retrieval via institutional access.

## Methodological transparency

This review used **Large Language Model assistance** at multiple stages:

- **Gemini 2.5 Flash** for the V1 exploratory pilot on the Scopus subset (calibration only)
- **Claude Opus (Anthropic)** for V2 title+abstract screening and full-text reading

All manual decisions were **initially produced by one team member and subsequently reviewed and validated by all five team members**. Disagreements were resolved by team discussion. This peer-validation procedure is stronger than a single-reviewer protocol but **not strictly equivalent** to a PRISMA-recommended double-reviewer protocol with Cohen's kappa — this nuance is explicitly declared in §4.4 limitation 3 of the article. Future work includes a formal independent double-screening with kappa computation.

## Citation

If you use this work, please cite it as:

> BEGNIS, M., RAYANE, R., BENSALEM, J., SIGNATE, M., & DAGAR, V. (2026).
> *The Role of Digital Twins in Energy Optimization and Smart Building Management:
> A Systematic Review using PRISMA*.
> Université Catholique de Lille — École du Numérique — Master 1 Data & AI.
> GitHub: https://github.com/mahebegnis/prisma-digital-twins-smart-buildings

A machine-readable [`CITATION.cff`](./CITATION.cff) is provided.

## License

This work is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](./LICENSE). You are free to share and adapt the material, provided you give appropriate credit.

---

*Repository prepared in May 2026 as part of the Master 1 Data & AI methodology of research course.*
