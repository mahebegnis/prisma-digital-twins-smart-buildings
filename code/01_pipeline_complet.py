"""
PIPELINE PRISMA COMPLET — Nettoyage, Déduplication, Fusion inter-bases
=======================================================================
Ce script reprend l'intégralité du pipeline de préparation des données
pour la revue systématique PRISMA sur les Digital Twins / Smart Buildings.

Corrections apportées :
  - Déduplication Scopus corrigée (DOI + Title+Year au lieu de ISSN)
  - Intégration de Web of Science (savedrecs.xls)
  - Déduplication inter-bases (DOI puis Title normalisé + Year)
  - Corpus unifié prêt pour screening
"""

import pandas as pd
import numpy as np
import re
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).parent
SEARCH_DIR = BASE_DIR / "search_results"
OUTPUT_DIR = BASE_DIR / "cleaned_results"
DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ============================================================
# UTILITAIRES
# ============================================================

def normalize_title(title: str) -> str:
    """Normalise un titre pour comparaison robuste."""
    if not isinstance(title, str):
        return ""
    t = unicodedata.normalize("NFKD", title)
    t = t.lower().strip()
    t = re.sub(r"[^a-z0-9\s]", "", t)  # garde lettres, chiffres, espaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_doi(doi) -> str:
    """Normalise un DOI pour comparaison."""
    if not isinstance(doi, str) or not doi.strip():
        return ""
    d = doi.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def clean_text(s: str) -> str:
    """Nettoie un champ texte."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"[\u0000-\u001F\u007F-\u009F]", "", s)
    s = s.replace("\ufeff", "").replace("\u200b", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ============================================================
# 1. CHARGEMENT ET NORMALISATION PAR BASE
# ============================================================

def load_scopus() -> pd.DataFrame:
    """Charge et normalise Scopus (343 articles bruts)."""
    df = pd.read_csv(SEARCH_DIR / "Scorpus_343.csv")
    print(f"[Scopus] Chargé : {len(df)} articles bruts")

    out = pd.DataFrame()
    out["Title"] = df["Title"].apply(clean_text)
    out["Abstract"] = df["Abstract"].apply(clean_text)
    out["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    out["Authors"] = df["Authors"].apply(clean_text)
    out["DOI"] = df["DOI"].apply(normalize_doi)
    out["Source"] = df["Source title"].apply(clean_text)
    out["Keywords"] = (
        df[["Author Keywords", "Index Keywords"]]
        .fillna("")
        .agg(" ; ".join, axis=1)
        .apply(clean_text)
    )
    out["Database"] = "Scopus"
    out["Document_Type"] = df.get("Document Type", "").apply(clean_text) if "Document Type" in df.columns else ""

    # Suppression des entrées sans titre ou abstract
    before = len(out)
    out = out.dropna(subset=["Title", "Abstract"])
    out = out[out["Title"].str.len() > 0]
    out = out[out["Abstract"].str.len() > 0]
    print(f"[Scopus] Après suppression entrées vides : {len(out)} ({before - len(out)} retirées)")

    # Déduplication intra-base sur DOI (si disponible) puis Title+Year
    before = len(out)
    # D'abord DOI (prioritaire, ne concerne que les articles avec DOI)
    mask_doi = out["DOI"].str.len() > 0
    out_with_doi = out[mask_doi].drop_duplicates(subset=["DOI"], keep="first")
    out_without_doi = out[~mask_doi]
    out = pd.concat([out_with_doi, out_without_doi], ignore_index=True)

    # Puis Title normalisé + Year
    out["_norm_title"] = out["Title"].apply(normalize_title)
    out = out.drop_duplicates(subset=["_norm_title", "Year"], keep="first")
    out = out.drop(columns=["_norm_title"])

    print(f"[Scopus] Après déduplication intra-base : {len(out)} ({before - len(out)} doublons retirés)")
    return out.reset_index(drop=True)


def load_ieee() -> pd.DataFrame:
    """Charge et normalise IEEE Xplore (67 articles bruts)."""
    df = pd.read_csv(SEARCH_DIR / "export2025.10.26-09.51.15.csv")
    print(f"\n[IEEE] Chargé : {len(df)} articles bruts")

    out = pd.DataFrame()
    out["Title"] = df["Document Title"].apply(clean_text)
    out["Abstract"] = df["Abstract"].apply(clean_text)
    out["Year"] = pd.to_numeric(df["Publication Year"], errors="coerce")
    out["Authors"] = df["Authors"].apply(clean_text)
    out["DOI"] = df["DOI"].apply(normalize_doi)
    out["Source"] = df["Publication Title"].apply(clean_text)
    out["Keywords"] = (
        df[["Author Keywords", "IEEE Terms"]]
        .fillna("")
        .agg(" ; ".join, axis=1)
        .apply(clean_text)
    )
    out["Database"] = "IEEE Xplore"
    out["Document_Type"] = ""

    before = len(out)
    out = out.dropna(subset=["Title", "Abstract"])
    out = out[out["Title"].str.len() > 0]
    out = out[out["Abstract"].str.len() > 0]
    print(f"[IEEE] Après suppression entrées vides : {len(out)} ({before - len(out)} retirées)")

    # Déduplication intra-base
    before = len(out)
    out["_norm_title"] = out["Title"].apply(normalize_title)
    out = out.drop_duplicates(subset=["_norm_title", "Year"], keep="first")
    out = out.drop(columns=["_norm_title"])
    print(f"[IEEE] Après déduplication intra-base : {len(out)} ({before - len(out)} doublons retirés)")
    return out.reset_index(drop=True)


def load_springer() -> pd.DataFrame:
    """Charge et normalise SpringerNature (144 articles bruts).
    NOTE: SpringerNature n'a PAS de colonne Abstract dans l'export."""
    df = pd.read_csv(SEARCH_DIR / "Spring nature.csv")
    print(f"\n[SpringerNature] Chargé : {len(df)} articles bruts")

    out = pd.DataFrame()
    out["Title"] = df["Item Title"].apply(clean_text)
    out["Abstract"] = ""  # Pas d'abstract dans l'export SpringerNature
    out["Year"] = pd.to_numeric(df["Publication Year"], errors="coerce")
    out["Authors"] = df["Authors"].apply(clean_text)
    out["DOI"] = df["Item DOI"].apply(normalize_doi)
    out["Source"] = df["Publication Title"].apply(clean_text)
    out["Keywords"] = ""
    out["Database"] = "SpringerNature"
    out["Document_Type"] = df.get("Content Type", "").apply(clean_text) if "Content Type" in df.columns else ""

    before = len(out)
    out = out[out["Title"].str.len() > 0]
    print(f"[SpringerNature] Après suppression entrées vides : {len(out)} ({before - len(out)} retirées)")

    # Déduplication intra-base sur DOI
    before = len(out)
    out = out.drop_duplicates(subset=["DOI"], keep="first")
    out["_norm_title"] = out["Title"].apply(normalize_title)
    out = out.drop_duplicates(subset=["_norm_title", "Year"], keep="first")
    out = out.drop(columns=["_norm_title"])
    print(f"[SpringerNature] Après déduplication intra-base : {len(out)} ({before - len(out)} doublons retirés)")
    return out.reset_index(drop=True)


def load_wos() -> pd.DataFrame:
    """Charge et normalise Web of Science (savedrecs.xls)."""
    df = pd.read_excel(SEARCH_DIR / "savedrecs.xls")
    print(f"\n[WoS] Chargé : {len(df)} articles bruts")

    out = pd.DataFrame()
    out["Title"] = df["Article Title"].apply(clean_text)
    out["Abstract"] = df["Abstract"].apply(clean_text)
    out["Year"] = pd.to_numeric(df["Publication Year"], errors="coerce")
    out["Authors"] = df["Author Full Names"].apply(clean_text)
    out["DOI"] = df["DOI"].apply(normalize_doi)
    out["Source"] = df["Source Title"].apply(clean_text)
    out["Keywords"] = (
        df[["Author Keywords", "Keywords Plus"]]
        .fillna("")
        .agg(" ; ".join, axis=1)
        .apply(clean_text)
    )
    out["Database"] = "Web of Science"
    out["Document_Type"] = df.get("Document Type", "").apply(clean_text) if "Document Type" in df.columns else ""

    before = len(out)
    out = out.dropna(subset=["Title", "Abstract"])
    out = out[out["Title"].str.len() > 0]
    out = out[out["Abstract"].str.len() > 0]
    print(f"[WoS] Après suppression entrées vides : {len(out)} ({before - len(out)} retirées)")

    before = len(out)
    mask_doi = out["DOI"].str.len() > 0
    out_with_doi = out[mask_doi].drop_duplicates(subset=["DOI"], keep="first")
    out_without_doi = out[~mask_doi]
    out = pd.concat([out_with_doi, out_without_doi], ignore_index=True)
    out["_norm_title"] = out["Title"].apply(normalize_title)
    out = out.drop_duplicates(subset=["_norm_title", "Year"], keep="first")
    out = out.drop(columns=["_norm_title"])
    print(f"[WoS] Après déduplication intra-base : {len(out)} ({before - len(out)} doublons retirés)")
    return out.reset_index(drop=True)


# ============================================================
# 2. FUSION ET DÉDUPLICATION INTER-BASES
# ============================================================

def merge_and_deduplicate(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Fusionne les DataFrames et déduplique inter-bases.

    Stratégie hiérarchique :
      1. DOI exact match (priorité maximale)
      2. Titre normalisé + Year match

    En cas de doublon, l'article avec l'Abstract le plus long est conservé,
    et la colonne Database indique toutes les bases d'origine.
    """
    merged = pd.concat(dfs, ignore_index=True)
    print(f"\n{'='*60}")
    print(f"FUSION : {len(merged)} articles avant déduplication inter-bases")
    print(f"  - Scopus: {len(merged[merged['Database']=='Scopus'])}")
    print(f"  - IEEE: {len(merged[merged['Database']=='IEEE Xplore'])}")
    print(f"  - SpringerNature: {len(merged[merged['Database']=='SpringerNature'])}")
    print(f"  - WoS: {len(merged[merged['Database']=='Web of Science'])}")

    merged["_norm_title"] = merged["Title"].apply(normalize_title)
    merged["_norm_doi"] = merged["DOI"].apply(lambda x: x if isinstance(x, str) and len(x) > 0 else "")
    merged["_abstract_len"] = merged["Abstract"].str.len()

    # Étape 1 : grouper par DOI (non vide)
    has_doi = merged[merged["_norm_doi"].str.len() > 0].copy()
    no_doi = merged[merged["_norm_doi"].str.len() == 0].copy()

    # Pour les articles avec DOI : garder le meilleur (abstract le plus long)
    deduped_doi = (
        has_doi.sort_values("_abstract_len", ascending=False)
        .drop_duplicates(subset=["_norm_doi"], keep="first")
    )

    # Capturer les bases d'origine pour chaque DOI
    doi_databases = (
        has_doi.groupby("_norm_doi")["Database"]
        .apply(lambda x: " | ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"Database": "_all_databases"})
    )
    deduped_doi = deduped_doi.merge(doi_databases, on="_norm_doi", how="left")

    dois_kept = set(deduped_doi["_norm_doi"])
    duplicates_doi = len(has_doi) - len(deduped_doi)

    # Étape 2 : articles sans DOI + articles avec DOI non encore vus
    # Retirer du no_doi les articles dont le titre+year est déjà couvert par un DOI match
    deduped_doi_titles = set(
        deduped_doi["_norm_title"] + "|||" + deduped_doi["Year"].astype(str)
    )
    no_doi["_key"] = no_doi["_norm_title"] + "|||" + no_doi["Year"].astype(str)
    no_doi_unique = no_doi[~no_doi["_key"].isin(deduped_doi_titles)].copy()

    # Déduplication titre+year sur les articles sans DOI
    no_doi_unique = (
        no_doi_unique.sort_values("_abstract_len", ascending=False)
        .drop_duplicates(subset=["_norm_title", "Year"], keep="first")
    )
    no_doi_unique["_all_databases"] = no_doi_unique["Database"]

    duplicates_title = len(no_doi) - len(no_doi_unique)

    # Assemblage final
    result = pd.concat([deduped_doi, no_doi_unique], ignore_index=True)

    # Mettre à jour la colonne Database avec toutes les sources
    result["Database"] = result["_all_databases"].fillna(result["Database"])

    # Nettoyage colonnes internes
    result = result.drop(columns=[
        "_norm_title", "_norm_doi", "_abstract_len", "_all_databases", "_key"
    ], errors="ignore")

    total_removed = len(merged) - len(result)
    print(f"\nDéduplication inter-bases :")
    print(f"  - Par DOI : {duplicates_doi} doublons retirés")
    print(f"  - Par Titre+Year : {duplicates_title} doublons retirés")
    print(f"  - Total inter-bases : {total_removed} doublons retirés")
    print(f"  → Corpus unifié final : {len(result)} articles uniques")
    print(f"{'='*60}")

    return result.reset_index(drop=True)


# ============================================================
# 3. EXÉCUTION
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PIPELINE PRISMA — Nettoyage & Déduplication complète")
    print("=" * 60)

    # Chargement des 4 bases
    df_scopus = load_scopus()
    df_ieee = load_ieee()
    df_springer = load_springer()
    df_wos = load_wos()

    # Fusion et déduplication inter-bases
    corpus = merge_and_deduplicate([df_scopus, df_ieee, df_springer, df_wos])

    # Sauvegarde du corpus unifié
    output_path = DATA_DIR / "corpus_unified_screening_ready.csv"
    corpus.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\n✅ Corpus unifié sauvegardé : {output_path}")
    print(f"   {len(corpus)} articles prêts pour screening")

    # Statistiques finales
    print(f"\n--- Répartition par base d'origine ---")
    for db in ["Scopus", "IEEE Xplore", "SpringerNature", "Web of Science"]:
        count = corpus["Database"].str.contains(db).sum()
        print(f"  {db}: {count} articles")

    multi = corpus["Database"].str.contains(r"\|").sum()
    print(f"  Articles présents dans plusieurs bases : {multi}")

    has_abstract = (corpus["Abstract"].str.len() > 0).sum()
    no_abstract = (corpus["Abstract"].str.len() == 0).sum()
    print(f"\n  Avec abstract : {has_abstract}")
    print(f"  Sans abstract (SpringerNature) : {no_abstract}")
