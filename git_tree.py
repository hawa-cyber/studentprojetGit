"""
git_tree.py — Structure de données et rendu visuel de l'arbre Git.
"""

from collections import deque
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# Symboles Unicode et couleurs rich
# ─────────────────────────────────────────────

SYMBOLE_COMMIT   = "●"    # U+25CF — nœud commit
SYMBOLE_BRANCHE  = "│"    # U+2502 — ligne verticale
SYMBOLE_CONVERGE = "╱"    # U+2571 — convergence de deux branches

COULEUR_COMMIT  = "bold green"
COULEUR_BRANCHE = "blue"
COULEUR_HASH    = "red"

# Chaînes rich markup précompilées au niveau du module.
# Évite de reconstruire les mêmes f-strings à chaque commit affiché.
_MARKUP_COMMIT   = f"[{COULEUR_COMMIT}]{SYMBOLE_COMMIT}[/{COULEUR_COMMIT}]"
_MARKUP_BRANCHE  = f"[{COULEUR_BRANCHE}]{SYMBOLE_BRANCHE}[/{COULEUR_BRANCHE}]"
_MARKUP_CONVERGE = f"[{COULEUR_BRANCHE}]{SYMBOLE_CONVERGE}[/{COULEUR_BRANCHE}]"


# ─────────────────────────────────────────────
# Structure de données
# ─────────────────────────────────────────────

@dataclass
class Commit:
    """Représente un commit Git.

    Attributes:
        hash: Identifiant court du commit (ex : "a1b2c3d").
        message: Première ligne du message de commit.
        parents: Hashes des commits parents. Vide pour le commit initial.
        refs: Références pointant ici (branches, tags, HEAD).
              Ex : ["HEAD -> main", "origin/main", "tag: v1.0"].
    """

    hash: str
    message: str
    parents: list[str] = field(default_factory=list)
    refs: list[str]    = field(default_factory=list)


# ─────────────────────────────────────────────
# Arbre Git
# ─────────────────────────────────────────────

class GitTree:
    """Représente un dépôt Git : ensemble de commits reliés par leurs parents."""

    def __init__(self) -> None:
        self.commits: dict[str, Commit] = {}

    def add_commit(self, commit: Commit) -> None:
        """Ajoute un commit à l'arbre.

        Args:
            commit: Le commit à ajouter.
        """
        self.commits[commit.hash] = commit

    # ── Tri topologique ──────────────────────────────────────────────────────

    def topological_sort(self) -> list[Commit]:
        """Trie les commits du plus récent au plus ancien (algorithme de Kahn).

        Principe : les commits sans enfant (in-degree = 0) sont les plus
        récents (têtes de branches). On les traite en premier, puis on
        décrémente le compteur de leurs parents.
        Complexité : O(n + m), avec n commits et m relations parent-enfant.

        Returns:
            Liste de commits dans l'ordre topologique (plus récent en premier).
        """
        # Comptage des enfants de chaque commit
        in_degree: dict[str, int] = {h: 0 for h in self.commits}
        for commit in self.commits.values():
            for parent_hash in commit.parents:
                if parent_hash in in_degree:
                    in_degree[parent_hash] += 1

        # deque : popleft() en O(1) (plus efficace que list.pop(0) en O(n))
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

    # ── Méthodes privées de construction du rendu ────────────────────────────

    def _build_refs_str(self, refs: list[str]) -> str:
        """Construit la colonne gauche : branches, tags et HEAD en rich markup.

        Args:
            refs: Liste des références du commit.

        Returns:
            Chaîne rich markup avec les symboles UTF-8 appropriés.
        """
        if not refs:
            return ""

        parts: list[str] = []
        for ref in refs:
            if "HEAD ->" in ref:
                branch = ref.replace("HEAD -> ", "")
                parts.append(f"[bold green]HEAD → {branch}[/bold green]")
            elif ref.strip() == "HEAD":
                parts.append("[bold yellow]⬡ HEAD[/bold yellow]")
            elif "tag:" in ref:
                tag = ref.replace("tag: ", "")
                parts.append(f"[bold magenta]◆ {tag}[/bold magenta]")
            else:
                parts.append(f"[bold cyan]⎇ {ref}[/bold cyan]")

        return "  ".join(parts)

    def _build_graph_str(self, lanes: list[str | None], col: int) -> str:
        """Construit la colonne centrale : le graphe de l'arbre pour une ligne.

        Args:
            lanes: État courant des colonnes (hash attendu, ou None si libre).
            col: Indice de la colonne du commit courant.

        Returns:
            Chaîne rich markup avec les symboles ●, │ et espaces.
        """
        parts: list[str] = []
        for i in range(len(lanes)):
            if i == col:
                parts.append(_MARKUP_COMMIT)
            elif lanes[i] is not None:
                parts.append(_MARKUP_BRANCHE)
            else:
                parts.append(" ")
        return " ".join(parts)

    def _build_convergence(
        self,
        lanes: list[str | None],
        col: int,
        merging_col: int,
        commit_hash: str,
    ) -> str:
        """Construit la ligne de convergence │╱ entre deux colonnes.

        Le symbole ╱ est placé entre les deux colonnes sans espace,
        ce qui donne │╱ et non │ ╱.

        Args:
            lanes: État courant des colonnes.
            col: Colonne principale (celle qui reste après la fusion).
            merging_col: Colonne qui converge vers col.
            commit_hash: Hash du commit de convergence.

        Returns:
            Chaîne rich markup de la ligne de convergence.
        """
        parts: list[str] = []
        for i in range(max(col, merging_col) + 1):
            if i == col:
                parts.append(_MARKUP_BRANCHE)
            elif i == merging_col:
                parts.append(_MARKUP_CONVERGE)
            elif lanes[i] is not None and lanes[i] != commit_hash:
                parts.append(_MARKUP_BRANCHE)
            else:
                parts.append(" ")
        # "".join et non " ".join : les symboles │╱ doivent se toucher
        return "".join(parts)

    def _update_lanes(
        self,
        lanes: list[str | None],
        col: int,
        parents: list[str],
    ) -> None:
        """Met à jour le tableau des colonnes après l'affichage d'un commit.

        Le premier parent reste dans la même colonne.
        Les parents supplémentaires (commits de fusion) occupent
        la première colonne libre, ou une nouvelle colonne en fin de liste.

        Args:
            lanes: État courant des colonnes (modifié en place).
            col: Colonne du commit qui vient d'être affiché.
            parents: Hashes des parents du commit.
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

    def lane_assignments(self) -> list[tuple[Commit, int]]:
        """Retourne chaque commit avec son indice de colonne dans le graphe.

        Assigne une colonne à chaque commit dans l'ordre topologique.
        Utilisée par git_graph.py pour calculer les positions graphiques
        sans dupliquer la logique d'attribution des colonnes.

        Returns:
            Liste de tuples (commit, indice_colonne), plus récent en premier.
        """
        commits = self.topological_sort()
        result: list[tuple[Commit, int]] = []
        lanes: list[str | None] = []

        for commit in commits:
            # Trouver la colonne du commit (ou en créer une nouvelle)
            col = next((i for i, v in enumerate(lanes) if v == commit.hash), None)
            if col is None:
                lanes.append(commit.hash)
                col = len(lanes) - 1

            result.append((commit, col))
            self._update_lanes(lanes, col, commit.parents)

            # Supprimer les colonnes vides en fin de liste
            while lanes and lanes[-1] is None:
                lanes.pop()

        return result

    def to_columns(self) -> list[tuple[str, str, str]]:
        """Retourne l'arbre sous forme de 3 colonnes alignées pour l'affichage.

        Chaque élément du résultat est un tuple (refs, graph, info) :
            refs  : branches, tags, HEAD   (colonne gauche)
            graph : l'arbre graphique       (colonne centrale)
            info  : hash court + message    (colonne droite)

        Les lignes de convergence (│╱) ont uniquement graph rempli.

        Returns:
            Liste de tuples (refs_markup, graph_markup, info_markup).
        """
        commits = self.topological_sort()

        if not commits:
            return [("", "[dim]  (depot vide -- aucun commit)[/dim]", "")]

        output: list[tuple[str, str, str]] = []
        lanes: list[str | None] = []

        for commit in commits:
            # Parcours unique de lanes pour trouver la colonne du commit
            # et détecter les convergences (même hash en plusieurs colonnes).
            col: int | None = None
            merging: list[int] = []
            for i, v in enumerate(lanes):
                if v == commit.hash:
                    if col is None:
                        col = i          # première occurrence → colonne principale
                    else:
                        merging.append(i)  # occurrences suivantes → convergence

            if col is None:
                lanes.append(commit.hash)
                col = len(lanes) - 1

            # Insérer les lignes de convergence (│╱) avant le nœud du commit
            for m in merging:
                output.append(("", self._build_convergence(lanes, col, m, commit.hash), ""))
                lanes[m] = None

            refs_str  = self._build_refs_str(commit.refs)
            graph_str = self._build_graph_str(lanes, col)
            hash_str  = f"[{COULEUR_HASH}]{commit.hash[:7]}[/{COULEUR_HASH}]"
            info_str  = f"{hash_str}  {commit.message}"

            output.append((refs_str, graph_str, info_str))
            self._update_lanes(lanes, col, commit.parents)

            while lanes and lanes[-1] is None:
                lanes.pop()

        return output
