"""
main.py — Point d'entrée du projet GitQuest.

Modes d'utilisation :
    python main.py                         → démo avec données fictives (étape 1)
    python main.py <chemin_depot>          → affiche un vrai dépôt Git (étape 2)
    python main.py <chemin_depot> --loop   → boucle interactive (étape 3)
"""

import io
import subprocess
import sys

from display import afficher_deux_colonnes, afficher_encadre
from git_graph import afficher_graphique
from git_reader import read_repo
from git_tree import Commit, GitTree

# Forcer l'encodage UTF-8 sur Windows (évite les erreurs cp1252 dans le terminal)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 1 — Données arbitraires (test de l'affichage)
# ─────────────────────────────────────────────────────────────────────────────

def demo_arbre_arbitraire() -> None:
    """Construit un arbre Git fictif à la main et l'affiche.

    Sert à valider la fonction d'affichage indépendamment d'un vrai dépôt.
    L'historique simulé est :

        C0  ←  C1  ←  C2  (main / HEAD)
                ↑
                C3  (feature)
    """
    print("\n" + "=" * 40)
    print("  ETAPE 1 -- Arbre fictif (test)")
    print("=" * 40 + "\n")

    tree = GitTree()

    tree.add_commit(Commit("d4e5f6g", "Initial commit",    parents=[],          refs=["tag: v1.0"]))
    tree.add_commit(Commit("c3d4e5f", "Ajout README",      parents=["d4e5f6g"], refs=[]))
    tree.add_commit(Commit("b2c3d4e", "Correction bug",    parents=["c3d4e5f"], refs=["HEAD -> main"]))
    tree.add_commit(Commit("a1b2c3d", "Nouvelle fonction", parents=["c3d4e5f"], refs=["feature"]))

    tree.display()


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 2 — Lecture d'un vrai dépôt Git
# ─────────────────────────────────────────────────────────────────────────────

def afficher_depot(chemin: str) -> GitTree:
    """Lit un dépôt Git existant et affiche son arbre.

    Args:
        chemin: Chemin vers le dépôt Git à lire.

    Returns:
        Le GitTree lu (réutilisable dans la boucle interactive).
    """
    print(f"\n{'=' * 40}")
    print(f"  ETAPE 2 -- Depot : {chemin}")
    print(f"{'=' * 40}\n")

    try:
        tree = read_repo(chemin)
        afficher_encadre(tree, commande=f"depot : {chemin}")
        return tree
    except (ValueError, RuntimeError) as e:
        print(f"  [Erreur] {e}")
        return GitTree()


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 3 — Boucle interactive
# ─────────────────────────────────────────────────────────────────────────────

def executer_commande(commande: str, repo_path: str) -> None:
    """Exécute une commande shell dans le dépôt donné et affiche le résultat.

    Args:
        commande: La commande shell à exécuter (ex: "git commit -m 'fix'").
        repo_path: Chemin vers le dépôt dans lequel exécuter la commande.
    """
    result = subprocess.run(
        commande,
        shell=True,
        cwd=repo_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(f"[stderr] {result.stderr.strip()}")


def boucle_interactive(repo_path: str) -> None:
    """Lance une boucle interactive de visualisation Git.

    À chaque tour, la boucle :
      1. Affiche l'arbre Git actuel du dépôt.
      2. Demande une commande à l'utilisateur.
      3. Exécute la commande dans le dépôt.
      4. Répète jusqu'à la saisie de 'exit'.

    Args:
        repo_path: Chemin vers le dépôt Git à utiliser.
    """
    print("\n" + "=" * 40)
    print("  ETAPE 3 -- Mode interactif")
    print("  Tapez 'exit' pour quitter.")
    print("=" * 40)

    derniere_commande = ""

    while True:
        # Afficher l'état actuel du dépôt dans un cadre
        print()
        try:
            tree = read_repo(repo_path)
            afficher_encadre(tree, commande=derniere_commande)
        except (ValueError, RuntimeError) as e:
            print(f"  [Erreur lecture depot] {e}")

        # Lire la commande utilisateur
        print()
        commande = input(">>> Commande (ou 'exit') : ").strip()

        if commande.lower() == "exit":
            print("  Fin de la session interactive.")
            break

        if not commande:
            continue

        # Exécuter la commande et afficher la sortie
        print()
        executer_commande(commande, repo_path)
        derniere_commande = commande


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Analyse les arguments et lance le mode correspondant."""
    print("=" * 40)
    print("      GitQuest -- Visualiseur Git")
    print("=" * 40)

    if len(sys.argv) == 1:
        # Aucun argument → démo données fictives
        demo_arbre_arbitraire()
        print("\n  Astuce : python main.py <depot>          → vrai depot")
        print("  Astuce : python main.py <depot> --loop   → mode interactif\n")

    elif len(sys.argv) == 2:
        # Un argument → lire un vrai dépôt
        afficher_depot(sys.argv[1])

    elif len(sys.argv) == 3 and sys.argv[2] == "--loop":
        # Deux arguments avec --loop → boucle interactive
        boucle_interactive(sys.argv[1])

    elif len(sys.argv) == 3 and sys.argv[2] == "--graph":
        # Mode graphique matplotlib (style learngitbranching)
        try:
            tree = read_repo(sys.argv[1])
            afficher_graphique(tree, titre=f"Git — {sys.argv[1]}")
        except (ValueError, RuntimeError) as e:
            print(f"  [Erreur] {e}")

    else:
        print("Usage :")
        print("  python main.py                         -> demo donnees fictives")
        print("  python main.py <depot>                 -> afficher un vrai depot")
        print("  python main.py <depot> --loop          -> mode interactif")
        print("  python main.py <depot> --graph         -> graphique (style learngitbranching)")


if __name__ == "__main__":
    main()
