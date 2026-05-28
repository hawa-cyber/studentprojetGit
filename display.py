"""
display.py — Affichage encadré et coloré de l'arbre Git avec rich.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table, box
from rich.text import Text

from git_tree import GitTree

# Console rich — une seule instance pour tout le module
_console = Console()


def afficher_encadre(tree: GitTree, commande: str = "") -> None:
    """Affiche un arbre Git dans un cadre bordé avec 3 colonnes alignées.

    Colonne 1 (gauche)  : branches, tags, HEAD avec symboles UTF-8
    Colonne 2 (centre)  : l'arbre graphique (●, │, ╱)
    Colonne 3 (droite)  : hash + message du commit

    Rendu attendu :
        ╭─ $ git commit -m "fix" ───────────────────────────────────╮
        │  HEAD → main    ●        a1b2c3d   Fix bug                │
        │  ⎇ feature      │ ●      b2c3d4e   Nouvelle fonction      │
        │                 │╱                                         │
        │  ◆ v1.0         ●        c3d4e5f   Initial commit         │
        ╰───────────────────────────────────────────────────────────╯

    Args:
        tree: L'arbre Git à afficher.
        commande: La commande exécutée (affichée dans le titre du cadre).
    """
    # Tableau sans bordures internes : 3 colonnes alignées
    tableau = Table(
        show_header=False,
        box=None,
        padding=(0, 1),
        show_edge=False,
    )
    tableau.add_column("refs",  min_width=18, no_wrap=True)
    tableau.add_column("graph", min_width=6,  no_wrap=True)
    tableau.add_column("info",  min_width=20, no_wrap=True)

    for refs, graph, info in tree.to_columns():
        tableau.add_row(
            Text.from_markup(refs)  if refs  else Text(""),
            Text.from_markup(graph) if graph else Text(""),
            Text.from_markup(info)  if info  else Text(""),
        )

    titre = (
        f"[bold cyan]$ {commande}[/bold cyan]"
        if commande else
        "[bold cyan]Git Tree[/bold cyan]"
    )

    _console.print(Panel(
        tableau,
        title=titre,
        title_align="left",
        border_style="bright_blue",
        padding=(1, 2),
    ))


def afficher_deux_colonnes(
    tree_actuel: GitTree,
    tree_cible: GitTree,
    commande: str = "",
) -> None:
    """Affiche deux arbres Git côte à côte dans un cadre bordé.

    Le premier arbre représente l'état actuel du dépôt,
    le second représente l'état cible à atteindre.

    Args:
        tree_actuel: L'arbre représentant l'état actuel du dépôt.
        tree_cible: L'arbre représentant l'état cible à atteindre.
        commande: La dernière commande exécutée (affichée dans le titre).
    """
    def _construire_sous_tableau(tree: GitTree, titre_col: str) -> Table:
        """Construit un sous-tableau affichant un arbre sur une seule colonne."""
        t = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            padding=(0, 1),
            show_edge=False,
        )
        t.add_column(titre_col, min_width=45, no_wrap=True)

        for refs, graph, info in tree.to_columns():
            if refs and info:
                ligne = f"{refs}  {graph}  {info}"
            elif info:
                ligne = f"{graph}  {info}"
            else:
                ligne = graph
            t.add_row(Text.from_markup(ligne) if ligne else Text(""))

        return t

    # Tableau principal : 2 colonnes (état actuel | état cible)
    tableau = Table(
        show_header=False,
        box=box.SIMPLE_HEAD,
        padding=(0, 2),
    )
    tableau.add_column("Etat actuel", min_width=45)
    tableau.add_column("Etat cible",  min_width=45)

    tableau.add_row(
        _construire_sous_tableau(tree_actuel, "  Etat actuel"),
        _construire_sous_tableau(tree_cible,  "  Etat cible"),
    )

    titre = (
        f"[bold cyan]$ {commande}[/bold cyan]"
        if commande else
        "[bold cyan]Git Tree — Comparaison[/bold cyan]"
    )

    _console.print(Panel(
        tableau,
        title=titre,
        title_align="left",
        border_style="bright_blue",
        padding=(0, 1),
    ))
