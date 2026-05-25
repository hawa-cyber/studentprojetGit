"""
git_tree.py — Structure de données et affichage de l'arbre Git.
Étape 1 du projet : représenter et afficher un arbre Git visuellement.
"""

from collections import deque
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# Symboles Unicode pour l'arbre
# ─────────────────────────────────────────────

SYMBOLE_COMMIT   = "●"    # U+25CF — nœud commit
SYMBOLE_BRANCHE  = "│"    # U+2502 — ligne verticale
SYMBOLE_CONVERGE = "╱"    # U+2571 — ligne diagonale (convergence)

# Couleurs rich (markup)
COULEUR_COMMIT  = "bold green"
COULEUR_BRANCHE = "blue"
COULEUR_REF     = "bold yellow"
COULEUR_HASH    = "red"


# ─────────────────────────────────────────────
# Structure de données
# ─────────────────────────────────────────────

@dataclass
class Commit:
    """Représente un commit Git.

    Attributes:
        hash: Identifiant unique du commit (ex: "a1b2c3d").
        message: Message du commit (première ligne).
        parents: Hashes des commits parents. Vide pour le commit initial.
        refs: Références pointant ici (branches, tags, HEAD).
              Ex: ["HEAD -> main", "origin/main", "tag: v1.0"].
    """

    hash: str
    message: str
    parents: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# Arbre Git
# ─────────────────────────────────────────────

class GitTree:
    """Représente un dépôt Git : ensemble de commits reliés par leurs parents."""

    def __init__(self) -> None:
        self.commits: dict[str, Commit] = {}   # hash -> Commit

    def add_commit(self, commit: Commit) -> None:
        """Ajoute un commit à l'arbre.

        Args:
            commit: Le commit à ajouter.
        """
        self.commits[commit.hash] = commit

    # ── Tri topologique ──────────────────────────────────────────────────────

    def _topological_sort(self) -> list[Commit]:
        """Trie les commits du plus récent au plus ancien.

        Utilise l'algorithme de Kahn basé sur les degrés entrants.
        Garantit que chaque commit apparaît toujours avant ses parents.

        Returns:
            Liste de commits dans l'ordre topologique (newest first).
        """
        in_degree: dict[str, int] = {h: 0 for h in self.commits}
        for commit in self.commits.values():
            for parent_hash in commit.parents:
                if parent_hash in in_degree:
                    in_degree[parent_hash] += 1

        # deque : popleft() en O(1) au lieu de O(n) avec une list
        queue: deque[str] = deque(h for h, deg in in_degree.items() if deg == 0)
        result: list[Commit] = []

        while queue:
            h = queue.popleft()
            result.append(self.commits[h])
            for parent_hash in self.commits[h].parents:
                if parent_hash in in_degree:
                    in_degree[parent_hash] -= 1
                    if in_degree[parent_hash] == 0:
                        queue.append(parent_hash)

        return result

    # ── Construction des lignes ───────────────────────────────────────────────

    def _build_convergence(
        self,
        lanes: list[str | None],
        col: int,
        merging_col: int,
        commit_hash: str,
    ) -> str:
        """Construit la ligne de convergence "│╱" entre deux colonnes.

        Args:
            lanes: État actuel des colonnes.
            col: Colonne principale (celle qui reste).
            merging_col: Colonne qui converge vers col.
            commit_hash: Hash du commit de convergence.

        Returns:
            La ligne de convergence sous forme de chaîne rich markup.
        """
        parts: list[str] = []
        for i in range(max(col, merging_col) + 1):
            if i == col:
                parts.append(f"[{COULEUR_BRANCHE}]{SYMBOLE_BRANCHE}[/{COULEUR_BRANCHE}]")
            elif i == merging_col:
                parts.append(f"[{COULEUR_BRANCHE}]{SYMBOLE_CONVERGE}[/{COULEUR_BRANCHE}]")
            elif lanes[i] is not None and lanes[i] != commit_hash:
                parts.append(f"[{COULEUR_BRANCHE}]{SYMBOLE_BRANCHE}[/{COULEUR_BRANCHE}]")
            else:
                parts.append(" ")
        return " ".join(parts)

    def _build_commit_line(
        self,
        lanes: list[str | None],
        col: int,
        commit: Commit,
    ) -> str:
        """Construit la ligne d'affichage d'un commit.

        Args:
            lanes: État actuel des colonnes.
            col: Colonne du commit à afficher.
            commit: Le commit à afficher.

        Returns:
            La ligne du commit sous forme de chaîne rich markup.
        """
        graph: list[str] = []
        for i in range(len(lanes)):
            if i == col:
                graph.append(f"[{COULEUR_COMMIT}]{SYMBOLE_COMMIT}[/{COULEUR_COMMIT}]")
            elif lanes[i] is not None:
                graph.append(f"[{COULEUR_BRANCHE}]{SYMBOLE_BRANCHE}[/{COULEUR_BRANCHE}]")
            else:
                graph.append(" ")

        refs_str = ""
        if commit.refs:
            refs_affichees = commit.refs[0].replace("->", "→")
            refs_str = f"  [{COULEUR_REF}]({refs_affichees})[/{COULEUR_REF}]"

        hash_str = f"[{COULEUR_HASH}]{commit.hash[:7]}[/{COULEUR_HASH}]"
        return f"{' '.join(graph)}  {hash_str}{refs_str}  {commit.message}"

    def _update_lanes(
        self,
        lanes: list[str | None],
        col: int,
        parents: list[str],
    ) -> None:
        """Met à jour les colonnes après l'affichage d'un commit.

        Args:
            lanes: État actuel des colonnes (modifié en place).
            col: Colonne du commit qui vient d'être affiché.
            parents: Liste des hashes des parents du commit.
        """
        if not parents:
            lanes[col] = None
            return

        lanes[col] = parents[0]

        for extra_parent in parents[1:]:
            placed = False
            for i, val in enumerate(lanes):
                if val is None:
                    lanes[i] = extra_parent
                    placed = True
                    break
            if not placed:
                lanes.append(extra_parent)

    # ── API publique ─────────────────────────────────────────────────────────

    def to_lines(self) -> list[str]:
        """Retourne l'arbre Git sous forme de liste de chaînes rich markup.

        Returns:
            Liste de lignes prêtes à être rendues par rich.
        """
        commits = self._topological_sort()

        if not commits:
            return ["[dim]  (depot vide -- aucun commit)[/dim]"]

        output: list[str] = []
        lanes: list[str | None] = []

        for commit in commits:
            col = next((i for i, v in enumerate(lanes) if v == commit.hash), None)
            if col is None:
                lanes.append(commit.hash)
                col = len(lanes) - 1

            merging = [i for i, v in enumerate(lanes) if v == commit.hash and i != col]
            for m in merging:
                output.append(self._build_convergence(lanes, col, m, commit.hash))
                lanes[m] = None

            output.append(self._build_commit_line(lanes, col, commit))
            self._update_lanes(lanes, col, commit.parents)

            while lanes and lanes[-1] is None:
                lanes.pop()

        return output

    def display(self) -> None:
        """Affiche l'arbre Git dans le terminal (sans cadre)."""
        from rich.console import Console
        from rich.text import Text
        console = Console()
        for line in self.to_lines():
            console.print(line)
