"""
display.py — Affichage encadré et coloré de l'arbre Git avec rich.
Gère le rendu visuel : cadre, couleurs, deux colonnes côte à côte.
"""

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box
from rich.text import Text

from git_tree import GitTree

# Console globale utilisée pour tout l'affichage
console = Console()


# ─────────────────────────────────────────────
# Affichage encadré — une seule colonne
# ─────────────────────────────────────────────

def afficher_encadre(tree: GitTree, commande: str = "") -> None:
    """Affiche un arbre Git dans un cadre bordé avec la commande en haut.

    Rendu attendu :
        ╭─ $ git commit -m "fix" ──────────────────╮
        │  ●  a1b2c3d  (HEAD → main)  Fix bug      │
        │  │  ●  b2c3d4e  (feature)  Nouvelle fn   │
        │  │╱                                       │
        │  ●  c3d4e5f  Initial commit               │
        ╰────────────────────────────────────────────╯

    Args:
        tree: L'arbre Git à afficher.
        commande: La commande exécutée (affichée dans le titre du cadre).
    """
    lignes = tree.to_lines()

    # Assembler le contenu du panel
    contenu = Text()
    for i, ligne in enumerate(lignes):
        contenu.append_text(Text.from_markup(ligne))
        if i < len(lignes) - 1:
            contenu.append("\n")

    # Titre du cadre
    titre = f"[bold cyan]$ {commande}[/bold cyan]" if commande else "[bold cyan]Git Tree[/bold cyan]"

    panel = Panel(
        contenu,
        title=titre,
        title_align="left",
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(panel)


# ─────────────────────────────────────────────
# Affichage encadré — deux colonnes côte à côte
# ─────────────────────────────────────────────

def afficher_deux_colonnes(
    tree_actuel: GitTree,
    tree_cible: GitTree,
    commande: str = "",
) -> None:
    """Affiche deux arbres Git côte à côte dans un cadre bordé.

    Colonne gauche : état actuel du dépôt.
    Colonne droite : état cible à atteindre.

    Rendu attendu :
        ╭─ $ git commit -m "fix" ──────────────────────────────────────╮
        │  ┌─────── Etat actuel ────────┬────── Etat cible ──────────┐ │
        │  │  ●  a1b2c3d  (HEAD) Fix   │  ●  d4e5f6g  (HEAD) Fix   │ │
        │  │  ●  b2c3d4e  commit       │  ●  e5f6g7h  commit        │ │
        │  └───────────────────────────┴────────────────────────────┘ │
        ╰────────────────────────────────────────────────────────────────╯

    Args:
        tree_actuel: L'arbre représentant l'état actuel du dépôt.
        tree_cible: L'arbre représentant l'état cible à atteindre.
        commande: La commande qui vient d'être exécutée.
    """
    lignes_g = tree_actuel.to_lines() or ["[dim](vide)[/dim]"]
    lignes_d = tree_cible.to_lines()  or ["[dim](vide)[/dim]"]

    # Égaliser les hauteurs des deux colonnes
    hauteur = max(len(lignes_g), len(lignes_d))
    lignes_g += [""] * (hauteur - len(lignes_g))
    lignes_d += [""] * (hauteur - len(lignes_d))

    # Construire le tableau deux colonnes
    tableau = Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold magenta",
        show_edge=True,
        padding=(0, 1),
    )
    tableau.add_column("  Etat actuel", min_width=30)
    tableau.add_column("  Etat cible",  min_width=30)

    for lg, ld in zip(lignes_g, lignes_d):
        tableau.add_row(
            Text.from_markup(lg) if lg else Text(""),
            Text.from_markup(ld) if ld else Text(""),
        )

    # Titre du cadre
    titre = f"[bold cyan]$ {commande}[/bold cyan]" if commande else "[bold cyan]Git Tree[/bold cyan]"

    panel = Panel(
        tableau,
        title=titre,
        title_align="left",
        border_style="bright_blue",
        padding=(0, 1),
    )
    console.print(panel)
