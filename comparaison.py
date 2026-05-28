"""
comparaison.py — Définition de l'état cible et comparaison d'arbres Git.
"""

from git_tree import Commit, GitTree


# ─────────────────────────────────────────────
# État cible
# ─────────────────────────────────────────────

def creer_arbre_cible() -> GitTree:
    """Crée l'arbre Git que l'utilisateur doit reproduire en mode interactif.

    L'historique cible représente :
        - un commit racine tagué v1.0
        - une branche main (3 commits)
        - une branche feature qui diverge depuis le second commit

    Schéma :
                    ●   Initial commit  (tag: v1.0)
                    │
                    ●   Ajout README
                   ╱ ╲
                  ●   ●
        HEAD→main     feature

    Returns:
        Un GitTree représentant l'état cible.
    """
    tree = GitTree()
    tree.add_commit(Commit("d4e5f6g", "Initial commit",    parents=[],          refs=["tag: v1.0"]))
    tree.add_commit(Commit("c3d4e5f", "Ajout README",      parents=["d4e5f6g"], refs=[]))
    tree.add_commit(Commit("b2c3d4e", "Correction bug",    parents=["c3d4e5f"], refs=["HEAD -> main"]))
    tree.add_commit(Commit("a1b2c3d", "Nouvelle fonction", parents=["c3d4e5f"], refs=["feature"]))
    return tree


# ─────────────────────────────────────────────
# Comparaison
# ─────────────────────────────────────────────

def _extraire_branches(tree: GitTree) -> dict[str, str]:
    """Retourne les branches nommées et le hash de leur commit de tête.

    Ignore HEAD détaché (ref == "HEAD") et les tags.

    Args:
        tree: L'arbre Git à analyser.

    Returns:
        Dictionnaire {nom_branche: hash_du_commit_de_tête}.
    """
    branches: dict[str, str] = {}
    for commit in tree.commits.values():
        for ref in commit.refs:
            if "HEAD ->" in ref:
                nom = ref.replace("HEAD -> ", "").strip()
                branches[nom] = commit.hash
            elif "tag:" not in ref and ref.strip() != "HEAD":
                branches[ref.strip()] = commit.hash
    return branches


def _formes_canoniques(tree: GitTree) -> dict[str, tuple]:
    """Calcule la forme canonique de chaque commit, indépendante des hashes.

    La forme d'un commit encode son message ET la structure de tout son
    historique parent, de manière récursive :

        forme(commit) = (message, (forme(parent_1), forme(parent_2), ...))

    Les formes des parents sont triées pour que l'ordre dans lequel git
    liste les parents n'influence pas le résultat.

    Le calcul est itératif (du plus ancien au plus récent) pour éviter
    tout dépassement de la pile de récursion sur de gros dépôts.

    Args:
        tree: L'arbre Git à analyser.

    Returns:
        Dictionnaire {hash: forme_canonique} pour tous les commits.
    """
    formes: dict[str, tuple] = {}

    # reversed(topological_sort()) donne les commits du plus ancien au plus
    # récent : quand on traite un commit, tous ses parents le sont déjà.
    for commit in reversed(tree.topological_sort()):
        parent_forms = tuple(sorted(
            formes.get(p, ("?",)) for p in commit.parents
        ))
        formes[commit.hash] = (commit.message, parent_forms)

    return formes


def etats_identiques(tree_actuel: GitTree, tree_cible: GitTree) -> bool:
    """Compare deux arbres Git par leurs branches et leur topologie.

    Deux arbres sont considérés identiques si :
        1. Ils ont exactement les mêmes noms de branches.
        2. Pour chaque branche, la forme canonique de son historique
           (messages + relations parent-enfant) est identique.

    Les hashes ne sont PAS comparés : ils diffèrent naturellement entre
    deux dépôts ayant pourtant le même historique. Seuls les messages
    et la structure des parentés comptent.

    Args:
        tree_actuel: L'arbre Git représentant l'état courant du dépôt.
        tree_cible: L'arbre Git représentant l'état à atteindre.

    Returns:
        True si les deux arbres ont les mêmes branches et la même structure.

    Example:
        cible  = creer_arbre_cible()
        actuel = read_repo(".")
        if etats_identiques(actuel, cible):
            print("Objectif atteint !")
    """
    branches_actuel = _extraire_branches(tree_actuel)
    branches_cible  = _extraire_branches(tree_cible)

    # Vérifier que les noms de branches sont identiques
    if set(branches_actuel.keys()) != set(branches_cible.keys()):
        return False

    formes_actuel = _formes_canoniques(tree_actuel)
    formes_cible  = _formes_canoniques(tree_cible)

    # Vérifier que chaque branche pointe vers un historique identique
    for nom in branches_cible:
        if formes_actuel.get(branches_actuel[nom]) != formes_cible.get(branches_cible[nom]):
            return False

    return True
