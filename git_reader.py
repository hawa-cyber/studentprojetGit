"""
git_reader.py — Lecture d'un dépôt Git existant via la ligne de commande.
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
    # Chercher dans le PATH en premier
    git_dans_path = shutil.which("git")
    if git_dans_path:
        return git_dans_path

    # Sinon, chercher dans les emplacements classiques Windows
    for chemin in _GIT_CHEMINS_WINDOWS:
        if Path(chemin).exists():
            return chemin

    raise RuntimeError(
        "Git est introuvable sur cette machine.\n"
        "Installe Git depuis https://git-scm.com/download/win\n"
        "puis redémarre le terminal."
    )


# Chemin de git résolu une seule fois au chargement du module
_GIT_EXE = _trouver_git()


def _run_git(command: list[str], repo_path: str) -> str:
    """Exécute une commande git dans le dépôt donné et retourne sa sortie.

    Args:
        command: Arguments git sans le mot "git". Ex : ["log", "--oneline"].
        repo_path: Chemin absolu vers le dépôt Git.

    Returns:
        Sortie standard de la commande git (stripped).

    Raises:
        RuntimeError: Si la commande git retourne une erreur.
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
    """
    path = Path(repo_path).resolve()
    if not (path / ".git").exists():
        raise ValueError(f"'{path}' n'est pas un dépôt Git (dossier .git introuvable)")

    # Format de chaque ligne : hash|parents|sujet|refs
    # maxsplit=3 permet au sujet (%s) de contenir des caractères '|'
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
            continue  # ligne malformée, ignorée

        commit_hash, parents_raw, message, refs_raw = parts

        # str.split() sans argument filtre les chaînes vides
        parents = [p[:7] for p in parents_raw.split()]
        refs     = [r.strip() for r in refs_raw.split(",") if r.strip()]

        tree.add_commit(Commit(
            hash=commit_hash,
            message=message,
            parents=parents,
            refs=refs,
        ))

    return tree
