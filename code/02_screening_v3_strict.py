"""
screening_v3_strict.py — Resserrement du screening titre+abstract

ENTREE : results_screening/included_papers_v2_final.csv (167 articles V2)
SORTIE : results_screening/screening_v3_strict.csv + 3 fichiers par bucket

OBJECTIF : reduire le dataset de 167 a ~100 articles via 4 criteres stricts
appliques sur titre + abstract + keywords.

CRITERES :
  C1 — Digital Twin explicite (digital twin / digital shadow)
  C2 — Validation explicite (case study, experiment, prototype, testbed...)
  C3 — Abstract substantiel (>= 100 mots)
  C4 — Scope batiment individuel (pas urbain/district)

CHAQUE CRITERE est evalue en {PASS, WEAK, FAIL} selon la force du signal.

LOGIQUE DE BUCKET :
  - 4 PASS                  -> INCLUDE_AUTO
  - >= 1 FAIL               -> EXCLUDE_AUTO
  - Mix PASS / WEAK         -> BORDERLINE  (escalade vers reviewer)

REPRODUCTIBILITE : 100% deterministe, regex documentees et auditables.
"""

import re
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent
INPUT = BASE / "results_screening" / "included_papers_v2_final.csv"
OUT_FULL = BASE / "results_screening" / "screening_v3_strict.csv"
OUT_INC = BASE / "results_screening" / "screening_v3_include_auto.csv"
OUT_BORD = BASE / "results_screening" / "screening_v3_borderline.csv"
OUT_EXC = BASE / "results_screening" / "screening_v3_exclude_auto.csv"


# ======================================================================
# C1 — DT explicite
# ======================================================================
RE_DT_STRICT = re.compile(
    r"\b(digital\s+twin|digital\s+twins|digital\s+twinning|"
    r"digital\s+shadow|digital\s+shadows)\b",
    re.I,
)
RE_DT_WEAK = re.compile(
    r"\b(digital\s+replica|virtual\s+replica|virtual\s+twin|"
    r"cyber[\s\-]*physical(?:\s+system|\s+systems)?|\bcps\b)",
    re.I,
)


def evaluate_c1(text: str) -> str:
    """C1 — DT explicite. Returns PASS / WEAK / FAIL."""
    if RE_DT_STRICT.search(text):
        return "PASS"
    if RE_DT_WEAK.search(text):
        return "WEAK"
    return "FAIL"


# ======================================================================
# C2 — Validation explicite
# ======================================================================
RE_VAL_STRICT = re.compile(
    r"\b("
    r"case\s+stud(?:y|ies)|"
    r"experiment(?:al|ed|ation|s)?|"
    r"prototype|"
    r"test[\s\-]?bed|"
    r"pilot(?:\s+(?:project|building|deployment|study))?|"
    r"deploy(?:ed|ment)|"
    r"field\s+(?:test|study|deployment|measurement|trial)|"
    r"real[\s\-]world|real\s+building|live\s+building|"
    r"validat(?:ed|ion|e)|"
    r"demonstrat(?:or|ion|ed|e)|"
    r"benchmark(?:ed|ing)?|"
    r"empirical(?:ly)?"
    r")\b",
    re.I,
)
RE_VAL_WEAK = re.compile(
    r"\b("
    r"evaluat(?:e|es|ed|ion|ing)|"
    r"test(?:ed|ing|s)?|"
    r"measur(?:e|es|ed|ement|ing)|"
    r"monitor(?:ed|ing)|"
    r"implement(?:ed|ation|s|ing)|"
    r"assess(?:ed|ment|ing)|"
    r"propose(?:d)?\s+a\s+(?:framework|methodology|model)"
    r")\b",
    re.I,
)


def evaluate_c2(text: str) -> str:
    """C2 — Validation explicite. Returns PASS / WEAK / FAIL."""
    if RE_VAL_STRICT.search(text):
        return "PASS"
    if RE_VAL_WEAK.search(text):
        return "WEAK"
    return "FAIL"


# ======================================================================
# C3 — Abstract substantiel
# ======================================================================
def word_count(text: str) -> int:
    if not text or pd.isna(text):
        return 0
    return len(re.findall(r"\b\w+\b", str(text)))


def evaluate_c3(abstract: str) -> str:
    """C3 — Abstract >= 100 mots PASS, 50-99 WEAK, < 50 FAIL."""
    n = word_count(abstract)
    if n >= 100:
        return "PASS"
    if n >= 50:
        return "WEAK"
    return "FAIL"


# ======================================================================
# C4 — Scope batiment individuel
# ======================================================================
RE_URBAN_STRONG = re.compile(
    r"\b("
    r"urban[\s\-]scale|city[\s\-]scale|district[\s\-]scale|"
    r"smart\s+cit(?:y|ies)|smart\s+urban|"
    r"urban\s+(?:planning|management|building\s+energy|digital\s+twin|environment)|"
    r"city\s+(?:planning|management|level|scale)|"
    r"neighborhood|neighbourhood|"
    r"energy\s+communit(?:y|ies)|"
    r"local\s+energy\s+communit(?:y|ies)|"
    r"\d{2,}\s+(?:households|buildings)|"
    r"district\s+(?:heating|cooling)|"
    r"city[\s\-]level|"
    r"urban\s+area|"
    r"residential\s+area"
    r")\b",
    re.I,
)
RE_URBAN_WEAK = re.compile(
    r"\b(urban|city|district|microgrid|community|cities)\b",
    re.I,
)
RE_BUILDING_ANCHOR = re.compile(
    r"\b("
    r"individual\s+building|single\s+building|"
    r"building[\s\-]level|per[\s\-]building|"
    r"office\s+building|residential\s+building|"
    r"hospital\s+building|school\s+building|"
    r"university\s+building|commercial\s+building|"
    r"specific\s+building|test\s+building|target\s+building|"
    r"existing\s+building|"
    r"case\s+study\s+building|"
    r"a\s+building|the\s+building|one\s+building"
    r")\b",
    re.I,
)


def evaluate_c4(text: str) -> str:
    """C4 — Scope batiment individuel.

    PASS : pas de signal urbain
    WEAK : urbain-strong + ancrage batiment (mix), ou urbain-weak seul
    FAIL : urbain-strong sans ancrage batiment
    """
    has_urban_strong = bool(RE_URBAN_STRONG.search(text))
    has_urban_weak = bool(RE_URBAN_WEAK.search(text))
    has_building = bool(RE_BUILDING_ANCHOR.search(text))

    if has_urban_strong and not has_building:
        return "FAIL"
    if has_urban_strong and has_building:
        return "WEAK"
    if has_urban_weak and not has_building:
        return "WEAK"
    return "PASS"


# ======================================================================
# Bucketization
# ======================================================================
def bucketize(c1: str, c2: str, c3: str, c4: str) -> str:
    statuses = [c1, c2, c3, c4]
    if "FAIL" in statuses:
        return "EXCLUDE_AUTO"
    if all(s == "PASS" for s in statuses):
        return "INCLUDE_AUTO"
    return "BORDERLINE"


# ======================================================================
# MAIN
# ======================================================================
def main():
    df = pd.read_csv(INPUT)
    print(f"Input : {len(df)} articles inclus V2\n")

    rows = []
    for _, r in df.iterrows():
        title = str(r.get("Title", ""))
        abstract = str(r.get("Abstract", ""))
        keywords = str(r.get("Keywords", ""))
        # full = recherche large pour C1 et C2
        full = " ".join([title, abstract, keywords])
        # title_abs = recherche restreinte pour C4 (scope) — evite faux positifs
        # sur les Keywords Scopus auto-indexes (ex: "urban area" comme tag)
        title_abs = " ".join([title, abstract])

        c1 = evaluate_c1(full)
        c2 = evaluate_c2(full)
        c3 = evaluate_c3(abstract)
        c4 = evaluate_c4(title_abs)
        bucket = bucketize(c1, c2, c3, c4)

        rows.append({
            "index": r["index"],
            "Title": r["Title"],
            "Year": r["Year"],
            "Database": r["Database"],
            "DOI": r["DOI"],
            "Abstract": r["Abstract"],
            "C1_dt": c1,
            "C2_validation": c2,
            "C3_abstract": c3,
            "C4_scope": c4,
            "abstract_words": word_count(abstract),
            "bucket_v3": bucket,
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_FULL, index=False)

    inc = out[out["bucket_v3"] == "INCLUDE_AUTO"]
    bord = out[out["bucket_v3"] == "BORDERLINE"]
    exc = out[out["bucket_v3"] == "EXCLUDE_AUTO"]
    inc.to_csv(OUT_INC, index=False)
    bord.to_csv(OUT_BORD, index=False)
    exc.to_csv(OUT_EXC, index=False)

    # ---- Stats ----
    print("=" * 60)
    print("DISTRIBUTION DES BUCKETS")
    print("=" * 60)
    for b in ["INCLUDE_AUTO", "BORDERLINE", "EXCLUDE_AUTO"]:
        n = (out["bucket_v3"] == b).sum()
        print(f"  {b:15s} {n:3d} ({n/len(out)*100:.1f}%)")

    print("\n" + "=" * 60)
    print("DISTRIBUTION PAR CRITERE")
    print("=" * 60)
    for c, lbl in [
        ("C1_dt", "C1 — DT explicite"),
        ("C2_validation", "C2 — Validation"),
        ("C3_abstract", "C3 — Abstract substantiel"),
        ("C4_scope", "C4 — Scope batiment"),
    ]:
        d = out[c].value_counts().to_dict()
        print(f"  {lbl:30s} PASS={d.get('PASS',0):3d}  WEAK={d.get('WEAK',0):3d}  FAIL={d.get('FAIL',0):3d}")

    # Detail des FAIL par critere
    print("\n" + "=" * 60)
    print("ARTICLES EXCLUDE_AUTO — repartition par 1er critere FAIL")
    print("=" * 60)
    excl = out[out["bucket_v3"] == "EXCLUDE_AUTO"]
    fail_by_c = {}
    for _, r in excl.iterrows():
        for c in ["C1_dt", "C2_validation", "C3_abstract", "C4_scope"]:
            if r[c] == "FAIL":
                fail_by_c.setdefault(c, 0)
                fail_by_c[c] += 1
                break
    for c, n in fail_by_c.items():
        print(f"  {c}: {n}")

    print(f"\nFichiers sortie :")
    print(f"  {OUT_FULL}")
    print(f"  {OUT_INC}  ({len(inc)} articles)")
    print(f"  {OUT_BORD} ({len(bord)} articles)")
    print(f"  {OUT_EXC}  ({len(exc)} articles)")


if __name__ == "__main__":
    main()
