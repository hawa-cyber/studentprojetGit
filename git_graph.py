"""
git_graph.py — Affichage graphique de l'arbre Git avec matplotlib.
Chaque branche (colonne) a une couleur distincte : cercles, flèches et
étiquettes suivent la même couleur, ce qui rend le graphe lisible
quel que soit le nombre de commits.
"""

import matplotlib.pyplot as plt

from git_tree import GitTree


# ─────────────────────────────────────────────
# Constantes visuelles
# ─────────────────────────────────────────────

COULEUR_FOND  = "#1e1e2e"   # fond sombre (style terminal moderne)
COULEUR_HEAD  = "#f38ba8"   # rose vif pour le commit HEAD
COULEUR_TEXTE = "white"

RAYON        = 0.40    # rayon des cercles
ESPACEMENT_Y = 2.2     # espace vertical entre commits
ESPACEMENT_X = 2.5     # espace horizontal entre colonnes

# Une couleur distincte par colonne (branche).
# Le cycle recommence si le dépôt a plus de colonnes que de couleurs.
_PALETTE = [
    "#c792ea",  # violet
    "#82aaff",  # bleu clair
    "#c3e88d",  # vert clair
    "#ffcb6b",  # jaune
    "#89ddff",  # cyan
    "#f78c6c",  # orange
    "#f07178",  # rouge rosé
    "#b2ccd6",  # gris bleu
]


def _couleur_col(col: int) -> str:
    """Retourne la couleur associée à une colonne (cycle sur la palette).

    Args:
        col: Indice de la colonne.

    Returns:
        Code couleur hexadécimal.
    """
    return _PALETTE[col % len(_PALETTE)]


# ─────────────────────────────────────────────
# Calcul du layout
# ─────────────────────────────────────────────

def _compute_layout(tree: GitTree) -> tuple[dict, dict]:
    """Calcule en un seul passage les positions (x, y) et les colonnes de chaque commit.

    Args:
        tree: L'arbre Git à positionner.

    Returns:
        Tuple (positions, colonnes) :
            positions = {hash: (x, y)}
            colonnes  = {hash: indice_colonne}
    """
    positions: dict[str, tuple[float, float]] = {}
    colonnes:  dict[str, int] = {}

    for idx, (commit, col) in enumerate(tree.lane_assignments()):
        positions[commit.hash] = (float(col) * ESPACEMENT_X, float(idx) * ESPACEMENT_Y)
        colonnes[commit.hash]  = col

    return positions, colonnes


# ─────────────────────────────────────────────
# Dessin des éléments
# ─────────────────────────────────────────────

def _dessiner_fleches(
    ax: plt.Axes,
    tree: GitTree,
    positions: dict,
    colonnes: dict,
) -> None:
    """Dessine les flèches entre commits (enfant → parent).

    Chaque flèche prend la couleur de la branche du commit enfant,
    ce qui permet de suivre visuellement chaque branche.

    Args:
        ax: L'axe matplotlib sur lequel dessiner.
        tree: L'arbre Git.
        positions: Dictionnaire hash -> (x, y).
        colonnes: Dictionnaire hash -> indice de colonne.
    """
    for commit in tree.commits.values():
        if commit.hash not in positions:
            continue
        cx, cy  = positions[commit.hash]
        couleur = _couleur_col(colonnes.get(commit.hash, 0))

        for parent_hash in commit.parents:
            if parent_hash not in positions:
                continue
            px, py   = positions[parent_hash]
            courbure = "arc3,rad=0.25" if cx != px else "arc3,rad=0.0"

            ax.annotate(
                "",
                xy=(px, py - RAYON),       # pointe de la flèche → parent
                xytext=(cx, cy + RAYON),   # queue de la flèche  → commit
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=couleur,
                    lw=2.5,
                    connectionstyle=courbure,
                ),
                zorder=2,
            )


def _dessiner_noeuds(
    ax: plt.Axes,
    tree: GitTree,
    positions: dict,
    colonnes: dict,
) -> None:
    """Dessine les cercles, hashes courts et étiquettes de chaque commit.

    La couleur de chaque cercle correspond à sa colonne (branche),
    sauf pour le commit HEAD qui est mis en évidence en rose.

    Args:
        ax: L'axe matplotlib sur lequel dessiner.
        tree: L'arbre Git.
        positions: Dictionnaire hash -> (x, y).
        colonnes: Dictionnaire hash -> indice de colonne.
    """
    for commit in tree.commits.values():
        if commit.hash not in positions:
            continue
        x, y    = positions[commit.hash]
        col     = colonnes.get(commit.hash, 0)
        couleur = _couleur_col(col)
        is_head = any("HEAD" in ref for ref in commit.refs)

        # ── Cercle du commit ─────────────────────────────────────────────────
        ax.add_patch(plt.Circle(
            (x, y), RAYON,
            color=COULEUR_HEAD if is_head else couleur,
            zorder=3,
            linewidth=2.5,
            edgecolor="white",
        ))

        # Hash court au centre du cercle
        ax.text(
            x, y,
            commit.hash[:5],
            ha="center", va="center",
            color="white",
            fontsize=8, fontweight="bold",
            zorder=4,
        )

        # Message court affiché sous le cercle uniquement pour les commits
        # "importants" : ceux qui ont des références (branches/tags) ou
        # qui sont des commits de fusion (plusieurs parents).
        # Sur un grand dépôt, afficher le message de chaque commit
        # créerait un mur de texte illisible.
        est_important = commit.refs or len(commit.parents) > 1
        if est_important:
            msg = commit.message[:25] + "…" if len(commit.message) > 25 else commit.message
            ax.text(
                x, y - RAYON - 0.20,
                msg,
                ha="center", va="top",
                color="#aaaaaa",
                fontsize=7.5,
                zorder=4,
            )

        # ── Étiquettes (branches, tags, HEAD) ────────────────────────────────
        for i, ref in enumerate(commit.refs):
            if "HEAD ->" in ref:
                nom    = ref.replace("HEAD -> ", "")
                nom    = nom[:20] + "…" if len(nom) > 20 else nom
                label  = nom + "  ✦"
                bg, fg = "#00d26a", "black"
            elif ref.strip() == "HEAD":
                label  = "HEAD"
                bg, fg = COULEUR_HEAD, "black"
            elif "tag:" in ref:
                nom    = ref.replace("tag: ", "")
                nom    = nom[:20] + "…" if len(nom) > 20 else nom
                label  = "◆ " + nom
                bg, fg = "#9b59b6", "white"
            else:
                label  = ref[:22] + "…" if len(ref) > 22 else ref
                bg, fg = couleur, "black"

            ax.text(
                x + RAYON + 0.15,
                y + 0.30 - i * 0.55,
                f" {label} ",
                ha="left", va="center",
                fontsize=11, fontweight="bold",
                color=fg,
                bbox=dict(
                    boxstyle="round,pad=0.30",
                    facecolor=bg,
                    edgecolor="white",
                    linewidth=1.2,
                ),
                zorder=5,
            )


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def afficher_graphique(tree: GitTree, titre: str = "Arbre Git") -> None:
    """Affiche l'arbre Git sous forme de graphe visuel avec matplotlib.

    Chaque branche (colonne) a une couleur distincte, inspiré du style
    GitKraken / learngitbranching.js.org.
    Le graphe est scrollable et zoomable grâce à la barre d'outils matplotlib :
    utiliser le bouton loupe ou la molette pour naviguer sur les grands dépôts.

    Args:
        tree: L'arbre Git à afficher.
        titre: Titre de la fenêtre matplotlib.

    Example:
        tree = read_repo(".")
        afficher_graphique(tree, titre="Mon dépôt")
    """
    positions, colonnes = _compute_layout(tree)

    if not positions:
        print("  Dépôt vide — rien à afficher.")
        return

    n_cols = max(colonnes.values()) + 1 if colonnes else 1
    n_rows = len(positions)
    fig_w  = max(6, n_cols * 4.0)
    fig_h  = max(6, n_rows * 1.8)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_facecolor(COULEUR_FOND)
    fig.patch.set_facecolor(COULEUR_FOND)

    # Dessin dans l'ordre : flèches d'abord, nœuds par-dessus
    _dessiner_fleches(ax, tree, positions, colonnes)
    _dessiner_noeuds(ax, tree, positions, colonnes)

    all_x = [p[0] for p in positions.values()]
    all_y = [p[1] for p in positions.values()]

    ax.set_xlim(min(all_x) - 0.8,  max(all_x) + 3.5)
    ax.set_ylim(min(all_y) - 1.0,  max(all_y) + 1.0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titre, color=COULEUR_TEXTE, fontsize=14,
                 fontweight="bold", pad=15)

    plt.tight_layout()
    plt.show()
