"""
question.py — Outil enseignant : création et chargement d'états cibles.

Un état cible (ou "question") représente la structure Git que l'étudiant
doit reproduire. Ce module permet à l'enseignant de :

    1. Capturer l'état actuel d'un dépôt Git et l'enregistrer dans un
       fichier JSON (--save-target) → création de la question.
    2. Charger un fichier JSON comme état cible pour le mode interactif
       (--loop --target <fichier.json>) → distribution de la question.

Format du fichier JSON
──────────────────────
{
    "description": "Texte libre décrivant l'objectif à atteindre",
    "commits": [
        {
            "hash":    "a1b2c3d",
            "message": "Initial commit",
            "parents": [],
            "refs":    ["tag: v1.0"]
        },
        ...
    ]
}

Utilisation rapide
──────────────────
# Enseignant — créer une question depuis un dépôt :
    python main.py <depot> --save-target question1.json

# Enseignant — créer une question depuis un dépôt avec description :
    python main.py <depot> --save-target question1.json --desc "Créer 2 branches"

# Étudiant — résoudre une question :
    python main.py <depot> --loop --target question1.json
"""

import json
from pathlib import Path

from git_tree import Commit, GitTree


# ─────────────────────────────────────────────
# Sérialisation / Désérialisation
# ─────────────────────────────────────────────

def sauvegarder_cible(tree: GitTree, chemin_fichier: str,
                      description: str = "") -> None:
    """Sérialise un GitTree en fichier JSON (état cible / question).

    Seuls les champs utiles à la comparaison sont exportés : hash, message,
    parents et refs. Les données d'affichage (positions, couleurs) ne sont
    pas incluses.

    Args:
        tree:           L'arbre Git à sauvegarder comme état cible.
        chemin_fichier: Chemin du fichier JSON à créer ou écraser.
        description:    Texte libre décrivant l'objectif de la question.
                        Laissé vide si non renseigné.

    Raises:
        OSError: Si le fichier ne peut pas être créé (droits insuffisants).

    Example:
        from git_reader import read_repo
        from question import sauvegarder_cible

        tree = read_repo("/chemin/vers/mon-depot")
        sauvegarder_cible(tree, "question1.json", "Créer une branche feature")
    """
    # Trier les commits du plus ancien au plus récent pour un JSON lisible
    commits_tries = list(reversed(tree.topological_sort()))

    payload = {
        "description": description,
        "commits": [
            {
                "hash":    c.hash,
                "message": c.message,
                "parents": c.parents,
                "refs":    c.refs,
            }
            for c in commits_tries
        ],
    }

    chemin = Path(chemin_fichier)
    chemin.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                      encoding="utf-8")

    nb_commits  = len(payload["commits"])
    nb_branches = sum(
        1 for c in payload["commits"]
        for r in c["refs"]
        if "HEAD ->" in r or ("tag:" not in r and r.strip() not in ("HEAD", ""))
    )
    print(f"  Question sauvegardée : {chemin_fichier}")
    print(f"  {nb_commits} commits  |  description : {description or '(aucune)'}")


def charger_cible(chemin_fichier: str) -> GitTree:
    """Désérialise un fichier JSON en GitTree (état cible / question).

    Args:
        chemin_fichier: Chemin vers le fichier JSON créé par sauvegarder_cible.

    Returns:
        Un GitTree représentant l'état cible à atteindre.

    Raises:
        FileNotFoundError: Si le fichier est introuvable.
        ValueError:        Si le JSON est malformé ou incomplet.

    Example:
        from question import charger_cible

        tree_cible = charger_cible("question1.json")
    """
    chemin = Path(chemin_fichier)
    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier de question introuvable : {chemin_fichier}\n"
            "Vérifiez le chemin ou créez-en un avec --save-target."
        )

    try:
        payload = json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Fichier JSON invalide ({chemin_fichier}) : {e}") from e

    commits_data = payload.get("commits")
    if not isinstance(commits_data, list):
        raise ValueError(
            f"Format de fichier invalide : clé 'commits' manquante ou incorrecte."
        )

    tree = GitTree()
    for item in commits_data:
        try:
            commit = Commit(
                hash    = item["hash"],
                message = item["message"],
                parents = item.get("parents", []),
                refs    = item.get("refs", []),
            )
            tree.add_commit(commit)
        except KeyError as e:
            raise ValueError(
                f"Commit invalide dans {chemin_fichier} : clé {e} manquante."
            ) from e

    description = payload.get("description", "")
    if description:
        print(f"  Question chargée : {chemin_fichier}")
        print(f"  Objectif : {description}")

    return tree
