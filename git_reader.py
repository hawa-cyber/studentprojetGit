"""
git_reader.py — Lecture d'un dépôt Git existant.
Étape 2 du projet : extraire l'état d'un vrai dépôt et remplir un GitTree.
"""

import shutil
import subprocess
from pathlib import Path

from git_tree import Commit, GitTree

# Emplacements classiques de Git sur Windows
_GIT_CHEMINS_WINDOWS = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
]


def _trouver_git() -> str:
    """Trouve le chemin de l'exécutable git sur la machine.

    Cherche d'abord dans le PATH, puis dans les emplacements
    classiques de Git for Windows.

    Returns:
        Le chemin complet vers git.exe (ou "git" si trouvé dans le PATH).

    Raises:
        RuntimeError: Si git est introuvable sur la machine.
    """
    # 1. Chercher git dans le PATH système
    git_dans_path = shutil.which("git")
    if git_dans_path:
        return git_dans_path

    # 2. Chercher dans les emplacements classiques Windows
    for chemin in _GIT_CHEMINS_WINDOWS:
        if Path(chemin).exists():
            return chemin

    raise RuntimeError(
        "Git est introuvable sur cette machine.\n"
        "Installe Git depuis https://git-scm.com/download/win\n"
        "puis redémarre le terminal."
    )


# Résoudre le chemin de git une seule fois au démarrage
_GIT_EXE = _trouver_git()


def _run_git(command: list[str], repo_path: str) -> str:
    """Exécute une commande git dans le dépôt donné et retourne sa sortie.

    Args:
        command: Liste des arguments git (sans le mot "git").
                 Ex: ["log", "--oneline"].
        repo_path: Chemin absolu vers le dépôt Git.

    Returns:
        La sortie standard de la commande git (stripped).

    Raises:
        RuntimeError: Si la commande git retourne un code d'erreur non nul.
    """
    result = subprocess.run(
        [_GIT_EXE] + command,
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Erreur git : {result.stderr.strip()}")
    return result.stdout.strip()


def read_repo(repo_path: str = ".") -> GitTree:
    """Lit un dépôt Git existant et retourne un GitTree prêt à être affiché.

    Utilise `git log --all --topo-order` pour récupérer tous les commits
    de toutes les branches dans l'ordre topologique.

    Args:
        repo_path: Chemin vers le dépôt Git. Défaut : répertoire courant.

    Returns:
        Un objet GitTree rempli avec tous les commits du dépôt.

    Raises:
        ValueError: Si le chemin donné n'est pas un dépôt Git valide.
        RuntimeError: Si une commande git échoue.

    Example:
        tree = read_repo("C:/mon/projet")
        tree.display()
    """
    # Vérifier que le chemin est un dépôt Git valide
    path = Path(repo_path).resolve()
    if not (path / ".git").exists():
        raise ValueError(f"'{path}' n'est pas un dépôt Git (dossier .git introuvable)")

    # Format de chaque ligne : hash|parents|sujet|refs
    # %h  = hash court        ex: a1b2c3d
    # %P  = parents courts    ex: b2c3d4e c3d4e5f  (vide si commit racine)
    # %s  = sujet (1re ligne) ex: Fix bug
    # %D  = refs              ex: HEAD -> main, tag: v1.0
    raw = _run_git(
        ["log", "--all", "--topo-order", "--pretty=format:%h|%P|%s|%D"],
        str(path),
    )

    if not raw:
        return GitTree()  # dépôt vide, aucun commit

    tree = GitTree()

    for line in raw.splitlines():
        parts = line.split("|", maxsplit=3)
        if len(parts) < 4:
            continue  # ligne malformée, on l'ignore

        commit_hash, parents_raw, message, refs_raw = parts

        # Les parents sont séparés par des espaces (vide si commit racine)
        # On tronque à 7 caractères pour rester cohérent avec les hash courts
        parents = [p[:7] for p in parents_raw.split() if p]

        # Les refs sont séparées par des virgules : "HEAD -> main, origin/main"
        refs = [r.strip() for r in refs_raw.split(",") if r.strip()]

        tree.add_commit(Commit(
            hash=commit_hash,
            message=message,
            parents=parents,
            refs=refs,
        ))

    return tree
