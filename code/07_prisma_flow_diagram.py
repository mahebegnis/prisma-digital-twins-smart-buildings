"""
prisma_flow_diagram.py — Generate PRISMA 2020 Flow Diagram

Genere un diagramme PRISMA 2020 conforme au standard a partir de matplotlib.
Sortie : PNG (300 dpi) + PDF (vectoriel) dans google_docs/.

Usage : python3 prisma_flow_diagram.py
"""

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D


# ===========================================================
# DONNEES FINALES (validees arithmetiquement)
# ===========================================================
DATA = {
    # Identification
    "id_databases": 704,
    "id_db_breakdown": "Scopus n=343\nWeb of Science n=150\nSpringerNature n=144\nIEEE Xplore n=67",
    "id_registers": 0,
    "removed_duplicates": 156,
    "removed_automation": 0,
    "removed_other": 0,
    # Screening
    "screened": 548,
    "screened_excluded": 418,
    "reports_sought": 130,
    "reports_not_retrieved": 79,
    "reports_not_retrieved_reasons": "Paywall (mainly IEEE)",
    # Eligibility
    "assessed": 51,
    "excluded_reasons": [
        ("Literature review (no primary contribution)", 1),
        ("District / multi-region scope", 2),
        ("Mega-facility / multi-buildings", 1),
        ("DT vision (not implemented; Model only)", 2),
    ],
    # Included
    "included": 45,
}

OUT_DIR = Path(__file__).parent / "google_docs"
OUT_DIR.mkdir(exist_ok=True)
OUT_PNG = OUT_DIR / "PRISMA_flow_diagram.png"
OUT_PDF = OUT_DIR / "PRISMA_flow_diagram.pdf"


# ===========================================================
# Style
# ===========================================================
BOX_STYLE = dict(
    boxstyle="round,pad=0.4,rounding_size=0.05",
    edgecolor="#1f4e79",
    facecolor="#f2f7fd",
    linewidth=1.5,
)
EXCL_STYLE = dict(
    boxstyle="round,pad=0.4,rounding_size=0.05",
    edgecolor="#c00000",
    facecolor="#fdf3f3",
    linewidth=1.5,
)
LABEL_STYLE = dict(
    boxstyle="round,pad=0.2,rounding_size=0.0",
    facecolor="#1f4e79",
    edgecolor="none",
)
ARROW_STYLE = dict(
    arrowstyle="-|>",
    mutation_scale=18,
    color="#1f4e79",
    linewidth=1.6,
)


def add_box(ax, xy, w, h, text, style=BOX_STYLE, fontsize=9):
    """Ajoute une boite rectangulaire avec du texte centre."""
    x, y = xy
    box = FancyBboxPatch((x, y), w, h, **style)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=fontsize,
            wrap=True, color="black")


def add_label(ax, xy, w, h, text):
    """Etiquette de section verticale (Identification, Screening, Included)."""
    x, y = xy
    box = FancyBboxPatch((x, y), w, h, **LABEL_STYLE)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center", fontsize=11,
            color="white", fontweight="bold", rotation=90)


def add_arrow(ax, p1, p2):
    arrow = FancyArrowPatch(p1, p2, **ARROW_STYLE)
    ax.add_patch(arrow)


# ===========================================================
# Construction du diagramme
# ===========================================================
def build_diagram():
    fig, ax = plt.subplots(figsize=(11, 14))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 18)
    ax.axis("off")

    # Title
    fig.suptitle("PRISMA 2020 Flow Diagram",
                 fontsize=14, fontweight="bold", y=0.97)
    ax.text(6, 17.4,
            "Digital Twins for Energy Optimization in Smart Buildings — Systematic Review",
            ha="center", va="center", fontsize=10, style="italic")

    # =======================
    # ETIQUETTES de section
    # =======================
    add_label(ax, (0.2, 14.0), 0.7, 2.5, "Identification")
    add_label(ax, (0.2, 6.5),  0.7, 7.0, "Screening")
    add_label(ax, (0.2, 3.0),  0.7, 3.0, "Included")

    # =======================
    # IDENTIFICATION
    # =======================
    # Records identified
    add_box(ax, (1.5, 15.0), 4.5, 1.4,
            f"Records identified from databases\n(n = {DATA['id_databases']})\n\n"
            + DATA['id_db_breakdown'],
            fontsize=8)

    # Records removed (duplicates)
    add_box(ax, (7.5, 15.0), 3.7, 1.4,
            f"Records removed before screening:\n"
            f"  Duplicate records removed (n = {DATA['removed_duplicates']})\n"
            f"  (intra-database + inter-database)",
            style=EXCL_STYLE, fontsize=8)

    # arrow id -> screening
    add_arrow(ax, (3.75, 15.0), (3.75, 13.5))
    add_arrow(ax, (6.0, 15.7), (7.5, 15.7))  # arrow box -> exclusion box

    # =======================
    # SCREENING
    # =======================
    # Records screened
    add_box(ax, (1.5, 12.1), 4.5, 1.4,
            f"Records screened\n(n = {DATA['screened']})",
            fontsize=10)

    # Records excluded screening
    add_box(ax, (7.5, 12.1), 3.7, 1.4,
            f"Records excluded\n(n = {DATA['screened_excluded']})\n"
            "(after multi-stage title + abstract\nscreening — see Methodology §3.4)",
            style=EXCL_STYLE, fontsize=8)
    add_arrow(ax, (6.0, 12.8), (7.5, 12.8))
    add_arrow(ax, (3.75, 12.1), (3.75, 10.6))

    # Reports sought for retrieval
    add_box(ax, (1.5, 9.2), 4.5, 1.4,
            f"Reports sought for retrieval\n(n = {DATA['reports_sought']})",
            fontsize=10)

    # Reports not retrieved
    add_box(ax, (7.5, 9.2), 3.7, 1.4,
            f"Reports not retrieved\n(n = {DATA['reports_not_retrieved']})\n"
            f"({DATA['reports_not_retrieved_reasons']})",
            style=EXCL_STYLE, fontsize=8)
    add_arrow(ax, (6.0, 9.9), (7.5, 9.9))
    add_arrow(ax, (3.75, 9.2), (3.75, 7.7))

    # Reports assessed
    add_box(ax, (1.5, 6.3), 4.5, 1.4,
            f"Reports assessed for eligibility\n(n = {DATA['assessed']})",
            fontsize=10)

    # Reports excluded with reasons
    excl_text = "Reports excluded\n(n = " + str(sum(n for _, n in DATA['excluded_reasons'])) + ")\n"
    for reason, n in DATA['excluded_reasons']:
        excl_text += f"  • {reason} (n = {n})\n"
    add_box(ax, (7.5, 5.6), 3.7, 2.1,
            excl_text.rstrip(),
            style=EXCL_STYLE, fontsize=7.5)
    add_arrow(ax, (6.0, 7.0), (7.5, 6.7))
    add_arrow(ax, (3.75, 6.3), (3.75, 4.8))

    # =======================
    # INCLUDED
    # =======================
    add_box(ax, (1.5, 3.4), 4.5, 1.4,
            f"Studies included in review\n(n = {DATA['included']})",
            fontsize=11)

    # Footer
    ax.text(6, 0.3,
            "Adapted from Page MJ et al. The PRISMA 2020 statement. BMJ 2021;372:n71. "
            "https://doi.org/10.1136/bmj.n71",
            ha="center", va="center", fontsize=7, style="italic", color="#555")

    return fig


def main():
    fig = build_diagram()
    fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
    print(f"PNG : {OUT_PNG}")
    print(f"PDF : {OUT_PDF}")


if __name__ == "__main__":
    main()
