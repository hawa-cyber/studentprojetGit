"""
git_graph.py — Affichage graphique de l'arbre Git avec matplotlib.
Inspiré de learngitbranching.js.org : cercles, flèches, étiquettes colorées.
"""

import matplotlib.pyplot as plt

from git_tree import GitTree


# ─────────────────────────────────────────────
# Constantes visuelles
# ─────────────────────────────────────────────

COULEUR_FOND     = "#4db8e8"   # bleu vif identique à learngitbranching
COULEUR_NOEUD    = "#6ab0c8"   # cercle bleu-gris (commits normaux)
COULEUR_HEAD     = "#3d5a6b"   # cercle plus sombre pour HEAD
COULEUR_TEXTE    = "white"
COULEUR_FLECHE   = "#1a5f7a"   # flèches bleu foncé

RAYON            = 0.30        # rayon des cercles
ESPACEMENT_Y     = 1.6         # espace vertical entre commits
ESPACEMENT_X     = 1.8         # espace horizontal entre colonnes


# ─────────────────────────────────────────────
# Calcul des positions
# ─────────────────────────────────────────────

def _compute_positions(tree: GitTree) -> dict[str, tuple[float, float]]:
    """Calcule la position graphique (x, y) de chaque commit.

    Utilise le même algorithme de colonnes que l'affichage texte :
    chaque branche occupe une colonne (axe x).
    Le commit le plus ancien est en haut (y maximal).

    Args:
        tree: L'arbre Git à positionner.

    Returns:
        Dictionnaire hash -> (x, y) en coordonnées matplotlib.
    """
    commits = tree._topological_sort()   # newest first
    positions: dict[str, tuple[float, float]] = {}
    lanes: list[str | None] = []

    for idx, commit in enumerate(commits):
        # y = idx → newest (idx=0) en bas, oldest en haut
        y = float(idx) * ESPACEMENT_Y

        # Trouver ou assigner la colonne du commit
        col = next((i for i, v in enumerate(lanes) if v == commit.hash), None)
        if col is None:
            col = len(lanes)
            lanes.append(commit.hash)

        positions[commit.hash] = (float(col) * ESPACEMENT_X, y)

        # Mettre à jour les colonnes
        if not commit.parents:
            lanes[col] = None
        else:
            lanes[col] = commit.parents[0]
            for extra in commit.parents[1:]:
                placed = False
                for i, val in enumerate(lanes):
                    if val is None:
                        lanes[i] = extra
                        placed = True
                        break
                if not placed:
                    lanes.append(extra)

        while lanes and lanes[-1] is None:
            lanes.pop()

    return positions


# ─────────────────────────────────────────────
# Dessin des éléments
# ─────────────────────────────────────────────

def _dessiner_fleches(ax: plt.Axes, tree: GitTree, positions: dict) -> None:
    """Dessine les flèches entre commits (enfant → parent).

    Args:
        ax: L'axe matplotlib sur lequel dessiner.
        tree: L'arbre Git.
        positions: Dictionnaire hash -> (x, y).
    """
    for commit in tree.commits.values():
        if commit.hash not in positions:
            continue
        cx, cy = positions[commit.hash]

        for parent_hash in commit.parents:
            if parent_hash not in positions:
                continue
            px, py = positions[parent_hash]

            # Courbure si branches différentes (x différents)
            courbure = "arc3,rad=0.2" if cx != px else "arc3,rad=0.0"

            ax.annotate(
                "",
                xy=(px, py - RAYON),        # pointe → parent
                xytext=(cx, cy + RAYON),     # queue  → commit
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=COULEUR_FLECHE,
                    lw=2.0,
                    connectionstyle=courbure,
                ),
                zorder=2,
            )


def _dessiner_noeuds(ax: plt.Axes, tree: GitTree, positions: dict) -> None:
    """Dessine les cercles et étiquettes de chaque commit.

    Args:
        ax: L'axe matplotlib sur lequel dessiner.
        tree: L'arbre Git.
        positions: Dictionnaire hash -> (x, y).
    """
    for commit in tree.commits.values():
        if commit.hash not in positions:
            continue
        x, y = positions[commit.hash]

        is_head = any("HEAD" in ref for ref in commit.refs)

        # ── Cercle du commit ─────────────────────────────────────────────────
        cercle = plt.Circle(
            (x, y), RAYON,
            color=COULEUR_HEAD if is_head else COULEUR_NOEUD,
            zorder=3,
            linewidth=2,
            edgecolor="white",
        )
        ax.add_patch(cercle)

        # Hash court affiché dans le cercle
        ax.text(
            x, y,
            commit.hash[:4],
            ha="center", va="center",
            color=COULEUR_TEXTE,
            fontsize=7, fontweight="bold",
            zorder=4,
        )

        # ── Étiquettes (branches, tags, HEAD) ────────────────────────────────
        for i, ref in enumerate(commit.refs):

            if "HEAD ->" in ref:
                # Branche courante → étiquette verte
                label    = ref.replace("HEAD -> ", "") + "  ✦"
                bg       = "#00d26a"
                fg       = "black"
            elif ref.strip() == "HEAD":
                # HEAD détaché
                label    = "HEAD"
                bg       = "#f39c12"
                fg       = "black"
            elif "tag:" in ref:
                # Tag → étiquette violette
                label    = ref.replace("tag: ", "◆ ")
                bg       = "#9b59b6"
                fg       = "white"
            else:
                # Autre branche → étiquette bleue claire
                label    = ref
                bg       = "#87ceeb"
                fg       = "black"

            ax.text(
                x + RAYON + 0.12,
                y + 0.20 - i * 0.38,
                f" {label} ",
                ha="left", va="center",
                fontsize=9, fontweight="bold",
                color=fg,
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor=bg,
                    edgecolor="white",
                    linewidth=0.8,
                ),
                zorder=5,
            )


# ─────────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────────

def afficher_graphique(tree: GitTree, titre: str = "Arbre Git") -> None:
    """Affiche l'arbre Git sous forme de graphe visuel avec matplotlib.

    Style inspiré de learngitbranching.js.org :
    - Cercles bleus pour les commits
    - Flèches grises vers les parents
    - Étiquettes colorées pour les branches
    - Fond bleu foncé

    Args:
        tree: L'arbre Git à afficher.
        titre: Titre de la fenêtre.

    Example:
        tree = read_repo(".")
        afficher_graphique(tree, titre="Mon dépôt")
    """
    commits = tree._topological_sort()

    if not commits:
        print("  Dépôt vide — rien à afficher.")
        return

    positions = _compute_positions(tree)

    # Taille de la figure selon le nombre de commits et colonnes
    n_cols = max(int(p[0] / ESPACEMENT_X) for p in positions.values()) + 1
    n_rows = len(commits)
    fig_w  = max(5, n_cols * 3.5)
    fig_h  = max(5, n_rows * 1.8)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_facecolor(COULEUR_FOND)
    fig.patch.set_facecolor(COULEUR_FOND)

    # Dessin dans l'ordre : flèches → nœuds → étiquettes
    _dessiner_fleches(ax, tree, positions)
    _dessiner_noeuds(ax, tree, positions)

    # Mise en page
    all_x = [p[0] for p in positions.values()]
    all_y = [p[1] for p in positions.values()]

    ax.set_xlim(min(all_x) - 0.8,  max(all_x) + 2.8)
    ax.set_ylim(min(all_y) - 0.8,  max(all_y) + 0.8)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titre, color=COULEUR_TEXTE, fontsize=13,
                 fontweight="bold", pad=12)

    plt.tight_layout()
    plt.show()
