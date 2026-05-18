"""
fetch_pdfs.py — Acquisition automatique des PDF open-access pour les articles
                inclus dans le screening V2.

STRATEGIE :
    1. Essai Unpaywall (gratuit, email requis en query param)
       -> retourne un best_oa_location avec url_for_pdf si disponible
    2. Si echec : essai arXiv (API simple, match par titre)
    3. Si echec : log "MANUAL_NEEDED" pour action humaine via acces institutionnel

USAGE :
    $ python3 fetch_pdfs.py --email you@example.com

SORTIES :
    fulltexts/{idx:04d}_{first_author}_{year}.pdf
    extraction/pdf_acquisition_log.csv

DEPENDANCES :
    pip install requests pandas
"""

import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

BASE = Path(__file__).parent.parent
CORPUS = BASE / "results_screening" / "screening_results_v2_corrected.csv"
PDF_DIR = BASE / "fulltexts"
LOG_PATH = BASE / "extraction" / "pdf_acquisition_log.csv"

UNPAYWALL_API = "https://api.unpaywall.org/v2/{doi}?email={email}"
OPENALEX_API = "https://api.openalex.org/works/doi:{doi}"
S2_API = "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf,title"
CORE_API = "https://api.core.ac.uk/v3/search/works?q=doi:{doi}&limit=1"
ARXIV_API = "http://export.arxiv.org/api/query?search_query=ti:{title}&max_results=5"

REQUEST_TIMEOUT = 20
SLEEP_BETWEEN = 0.4


def safe_name(s: str, max_len: int = 40) -> str:
    """Normalise une chaine pour nom de fichier."""
    s = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(s))
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len]


def first_author_lastname(authors: str) -> str:
    """Extrait le nom de famille du premier auteur."""
    if not authors or pd.isna(authors):
        return "unknown"
    first = str(authors).split(";")[0].split(",")[0].strip()
    # "Smith John" ou "John Smith"  : on prend le dernier token
    tokens = first.split()
    if not tokens:
        return "unknown"
    return safe_name(tokens[-1], 20)


def unpaywall_lookup(doi: str, email: str) -> dict | None:
    """Retourne {url: ..., version: ..., license: ...} ou None."""
    if not doi or pd.isna(doi):
        return None
    try:
        r = requests.get(
            UNPAYWALL_API.format(doi=quote(doi, safe=""), email=email),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        loc = data.get("best_oa_location") or {}
        url = loc.get("url_for_pdf")
        if not url:
            return None
        return {
            "url": url,
            "version": loc.get("version", "unknown"),
            "license": loc.get("license", "unknown"),
        }
    except (requests.RequestException, json.JSONDecodeError, ValueError):
        return None


def openalex_lookup(doi: str) -> str | None:
    """
    Match DOI strict via OpenAlex.
    Inspecte best_oa_location ET locations[] pour trouver un PDF reel.
    Filtre : on rejette les landing_page_url renvoyant vers doi.org
    (= page editeur paywall) et on privilegie host_type='repository'.
    """
    if not doi or pd.isna(doi):
        return None
    try:
        r = requests.get(
            OPENALEX_API.format(doi=quote(doi, safe="")),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        # parcourir TOUTES les locations dans l'ordre best d'abord
        candidates = []
        if data.get("best_oa_location"):
            candidates.append(data["best_oa_location"])
        candidates.extend(data.get("locations") or [])
        for loc in candidates:
            if not loc.get("is_oa"):
                continue
            pdf = loc.get("pdf_url")
            if pdf:
                return pdf
            # repository (HAL, Zenodo, OSF, IR universitaire) : landing page
            # peut servir un PDF
            host = (loc.get("host_type") or "").lower()
            if host == "repository":
                lp = loc.get("landing_page_url") or ""
                # rejeter doi.org (redirige vers publisher = paywall)
                if lp and "doi.org/" not in lp:
                    return lp
        return None
    except (requests.RequestException, json.JSONDecodeError, ValueError):
        return None


def s2_lookup(doi: str) -> str | None:
    """Match DOI strict via Semantic Scholar."""
    if not doi or pd.isna(doi):
        return None
    try:
        r = requests.get(
            S2_API.format(doi=quote(doi, safe="")),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        oa = data.get("openAccessPdf") or {}
        return oa.get("url")
    except (requests.RequestException, json.JSONDecodeError, ValueError):
        return None


def core_lookup(doi: str) -> str | None:
    """Match DOI strict via CORE."""
    if not doi or pd.isna(doi):
        return None
    try:
        r = requests.get(
            CORE_API.format(doi=quote(doi, safe="")),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get("results") or []
        if not results:
            return None
        return results[0].get("downloadUrl")
    except (requests.RequestException, json.JSONDecodeError, ValueError):
        return None


def _jaccard(a: str, b: str) -> float:
    """Jaccard similarity sur tokens >= 4 caracteres."""
    ta = set(re.findall(r"\w{4,}", (a or "").lower()))
    tb = set(re.findall(r"\w{4,}", (b or "").lower()))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def arxiv_lookup(title: str, authors: str = "",
                 sim_threshold: float = 0.6) -> str | None:
    """
    Match strict arXiv : retourne URL PDF UNIQUEMENT si :
      - similarite Jaccard titre attendu vs titre arXiv >= sim_threshold
      - au moins un nom d'auteur commun (lastname)

    Sans cette double validation, le risque est de telecharger un article
    sans rapport (premier resultat arXiv pour un mot-cle banal).
    """
    if not title:
        return None
    try:
        r = requests.get(
            ARXIV_API.format(title=quote(title[:200], safe="")),
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code != 200:
            return None
        # parsing minimal des entrees Atom
        # chaque <entry> contient <title>, <author><name>, et un <link rel="...pdf">
        entries = re.findall(r"<entry>(.*?)</entry>", r.text, re.S)
        expected_authors = set()
        if authors:
            for a in re.split(r"[;,]", str(authors)):
                a = a.strip()
                if not a:
                    continue
                tokens = a.split()
                if tokens:
                    expected_authors.add(tokens[-1].lower())

        for e in entries:
            tm = re.search(r"<title>(.*?)</title>", e, re.S)
            arxiv_title = re.sub(r"\s+", " ", tm.group(1)).strip() if tm else ""
            sim = _jaccard(title, arxiv_title)
            if sim < sim_threshold:
                continue
            arxiv_authors = set(
                n.strip().split()[-1].lower()
                for n in re.findall(r"<name>(.*?)</name>", e)
                if n.strip()
            )
            if expected_authors and not (expected_authors & arxiv_authors):
                continue
            pdfm = re.search(r'href="(https?://arxiv\.org/pdf/[^"]+)"', e)
            if pdfm:
                return pdfm.group(1)
    except requests.RequestException:
        return None
    return None


def download_pdf(url: str, dest: Path) -> bool:
    """Telecharge et verifie qu'il s'agit bien d'un PDF."""
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        if r.status_code != 200:
            return False
        ctype = r.headers.get("Content-Type", "").lower()
        if "pdf" not in ctype and not url.lower().endswith(".pdf"):
            return False
        content = r.content
        if not content.startswith(b"%PDF"):
            return False
        dest.write_bytes(content)
        return True
    except requests.RequestException:
        return False


def verify_pdf_title(pdf_path: Path, expected_title: str,
                      threshold: float = 0.6) -> bool:
    """
    Verifie que le PDF telecharge correspond bien au titre attendu.
    Calcule la proportion de tokens significatifs (>=5 chars) du titre presents
    dans les 2 premieres pages du PDF.
    Retourne True si ratio >= threshold.
    Necessaire pour les sources CORE/S2/arXiv qui peuvent renvoyer des
    PDF errones quand le DOI n'est pas exactement indexe.
    """
    if not expected_title:
        return True
    tokens_expected = set(re.findall(r"\w{5,}", expected_title.lower()))
    if not tokens_expected:
        return True
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        # si pdfplumber absent, on ne valide pas (laisser passer)
        return True
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:2] if len(pdf.pages) >= 2 else pdf.pages
            text = " ".join((p.extract_text() or "") for p in pages).lower()
        found = sum(1 for t in tokens_expected if t in text)
        ratio = found / len(tokens_expected)
        return ratio >= threshold
    except Exception:
        # PDF illisible : on rejete par securite
        return False


def safe_download_with_verify(url: str, dest: Path, expected_title: str,
                                source_name: str) -> bool:
    """
    Telecharge puis verifie que le PDF correspond bien au titre attendu.
    Si la verification echoue, supprime le fichier et retourne False.
    Pour Unpaywall (DOI Unpaywall = exacte), pas besoin de verifier.
    """
    if not download_pdf(url, dest):
        return False
    if source_name == "unpaywall":
        return True  # DOI Unpaywall = match exact garanti
    if verify_pdf_title(dest, expected_title):
        return True
    # PDF telecharge mais ne correspond pas -> on supprime
    try:
        dest.unlink()
    except OSError:
        pass
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True, help="email pour Unpaywall")
    ap.add_argument("--dry-run", action="store_true", help="ne telecharge pas")
    ap.add_argument("--limit", type=int, default=None,
                    help="limiter le nombre d'articles traites")
    args = ap.parse_args()

    PDF_DIR.mkdir(exist_ok=True)
    LOG_PATH.parent.mkdir(exist_ok=True)

    df = pd.read_csv(CORPUS)
    incl = df[df["decision"] == "Inclure"].copy()
    if args.limit:
        incl = incl.head(args.limit)

    log_rows = []
    for _, r in incl.iterrows():
        idx = int(r["index"])
        title = str(r.get("Title", ""))
        doi = str(r.get("DOI", "")).strip()
        year = int(r.get("Year", 0)) if pd.notna(r.get("Year")) else 0
        fname_base = f"{idx:04d}_{first_author_lastname(r.get('Authors',''))}_{year}"
        fpath = PDF_DIR / f"{fname_base}.pdf"

        if fpath.exists():
            log_rows.append([idx, doi, title[:80], "ALREADY_PRESENT", str(fpath), ""])
            continue

        status = "MANUAL_NEEDED"
        src = ""
        note = ""

        # 1. Unpaywall (DOI-based, agregateur principal)
        up = unpaywall_lookup(doi, args.email) if doi and doi != "nan" else None
        if up and not args.dry_run:
            if safe_download_with_verify(up["url"], fpath, title, "unpaywall"):
                status = "OA_UNPAYWALL"
                src = up["url"]
                note = f"version={up['version']}; license={up['license']}"
            else:
                note = "unpaywall_url_but_download_failed"
        elif up:
            status = "OA_UNPAYWALL_URL_ONLY"
            src = up["url"]
            note = f"version={up['version']}"

        # 2. OpenAlex (DOI-based, complementaire principal)
        if status == "MANUAL_NEEDED" and doi and doi != "nan":
            time.sleep(SLEEP_BETWEEN)
            oa_url = openalex_lookup(doi)
            if oa_url and not args.dry_run:
                if safe_download_with_verify(oa_url, fpath, title, "openalex"):
                    status = "OA_OPENALEX"
                    src = oa_url
                else:
                    note = "openalex_url_failed_or_wrong_title"
            elif oa_url:
                status = "OPENALEX_URL_ONLY"
                src = oa_url

        # 3. Semantic Scholar (DOI-based)
        if status == "MANUAL_NEEDED" and doi and doi != "nan":
            time.sleep(SLEEP_BETWEEN)
            s2_url = s2_lookup(doi)
            if s2_url and not args.dry_run:
                if safe_download_with_verify(s2_url, fpath, title, "s2"):
                    status = "OA_S2"
                    src = s2_url

        # 4. CORE (DOI-based)
        if status == "MANUAL_NEEDED" and doi and doi != "nan":
            time.sleep(SLEEP_BETWEEN)
            core_url = core_lookup(doi)
            if core_url and not args.dry_run:
                if safe_download_with_verify(core_url, fpath, title, "core"):
                    status = "OA_CORE"
                    src = core_url

        # 5. arXiv (fallback titre+auteurs valide strict)
        if status == "MANUAL_NEEDED":
            ax_url = arxiv_lookup(title[:200], r.get("Authors", ""))
            if ax_url and not args.dry_run:
                if safe_download_with_verify(ax_url, fpath, title, "arxiv"):
                    status = "OA_ARXIV_VALIDATED"
                    src = ax_url
            elif ax_url:
                status = "ARXIV_URL_ONLY"
                src = ax_url

        log_rows.append([idx, doi, title[:80], status, src, note])
        print(f"[{idx:04d}] {status:22s} | {title[:70]}")
        time.sleep(SLEEP_BETWEEN)

    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "doi", "title", "status", "source_url", "note"])
        w.writerows(log_rows)

    # Stats
    from collections import Counter
    counts = Counter(r[3] for r in log_rows)
    print("\n=== BILAN ACQUISITION ===")
    for s, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {s:25s} {n}")
    print(f"\nLog : {LOG_PATH}")


if __name__ == "__main__":
    main()
