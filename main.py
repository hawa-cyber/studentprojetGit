"""
main.py — Point d'entrée du projet GitQuest.

Modes d'utilisation :
    python main.py                         -> demo avec donnees fictives
    python main.py <chemin_depot>          -> affiche un vrai depot Git
    python main.py <chemin_depot> --loop   -> boucle interactive
    python main.py <chemin_depot> --graph  -> visualisation graphique matplotlib

Note :
    git_reader est importé en lazy dans chaque fonction qui en a besoin :
    la démo (étape 1) n'appelle pas git et ne doit pas en avoir besoin.
    git_graph est importé en lazy uniquement pour le mode --graph afin
    d'éviter de charger matplotlib (~3 secondes) inutilement.
"""

import io
import subprocess
import sys

from comparaison import creer_arbre_cible, etats_identiques
from display import afficher_deux_colonnes, afficher_encadre
from git_tree import GitTree

# Forcer l'encodage UTF-8 sur Windows (évite les erreurs cp1252 dans le terminal)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 1 — Données arbitraires (test de l'affichage)
# ─────────────────────────────────────────────────────────────────────────────

def demo_arbre_arbitraire() -> None:
    """Affiche l'arbre cible comme démonstration de l'outil.

    Réutilise creer_arbre_cible() pour éviter de dupliquer les données.
    """
    tree = creer_arbre_cible()
    afficher_encadre(tree, commande="demo -- donnees fictives")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 2 — Lecture d'un vrai dépôt Git
# ─────────────────────────────────────────────────────────────────────────────

def afficher_depot(chemin: str) -> None:
    """Lit un dépôt Git existant et affiche son arbre en 3 colonnes.

    Args:
        chemin: Chemin vers le dépôt Git à lire.
    """
    from git_reader import read_repo
    try:
        tree = read_repo(chemin)
        afficher_encadre(tree, commande=f"depot : {chemin}")
    except (ValueError, RuntimeError) as e:
        print(f"  [Erreur] {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 3 — Boucle interactive
# ─────────────────────────────────────────────────────────────────────────────

def executer_commande(commande: str, repo_path: str) -> None:
    """Exécute une commande shell dans le dépôt donné et affiche le résultat.

    Args:
        commande: La commande shell à exécuter (ex : "git commit -m 'fix'").
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
    """Lance une boucle interactive de visualisation Git avec comparaison d'états.

    À chaque tour, la boucle :
      1. Lit l'état actuel du dépôt.
      2. Affiche l'état actuel et l'état cible côte à côte.
      3. Vérifie si l'état cible est atteint.
      4. Demande une commande à l'utilisateur.
      5. Exécute la commande dans le dépôt.
      6. Répète jusqu'à 'exit' ou jusqu'à l'atteinte de l'état cible.

    Args:
        repo_path: Chemin vers le dépôt Git à utiliser.
    """
    from git_reader import read_repo

    print("\n" + "=" * 40)
    print("  Mode interactif")
    print("  Objectif : atteindre l'etat cible.")
    print("  Tapez 'exit' pour quitter.")
    print("=" * 40)

    tree_cible = creer_arbre_cible()
    derniere_commande = ""

    while True:
        print()
        try:
            tree_actuel = read_repo(repo_path)
            afficher_deux_colonnes(tree_actuel, tree_cible, commande=derniere_commande)
        except (ValueError, RuntimeError) as e:
            print(f"  [Erreur lecture depot] {e}")
            tree_actuel = GitTree()

        # Vérifier si l'objectif est atteint
        if etats_identiques(tree_actuel, tree_cible):
            print()
            print("  Objectif atteint ! L'etat du depot correspond a la cible.")
            break

        print()
        commande = input(">>> Commande (ou 'exit') : ").strip()

        if commande.lower() == "exit":
            print("  Fin de la session interactive.")
            break

        if not commande:
            continue

        print()
        executer_commande(commande, repo_path)
        derniere_commande = commande


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Analyse les arguments et lance le mode correspondant."""

    if len(sys.argv) == 1:
        demo_arbre_arbitraire()
        print("\n  python main.py <depot>          -> vrai depot")
        print("  python main.py <depot> --loop   -> mode interactif")
        print("  python main.py <depot> --graph  -> graphique matplotlib\n")

    elif len(sys.argv) == 2:
        afficher_depot(sys.argv[1])

    elif len(sys.argv) == 3 and sys.argv[2] == "--loop":
        boucle_interactive(sys.argv[1])

    elif len(sys.argv) == 3 and sys.argv[2] == "--graph":
        # Imports lazy : matplotlib (~3s) et git_reader chargés seulement ici
        from git_graph import afficher_graphique
        from git_reader import read_repo
        try:
            tree = read_repo(sys.argv[1])
            afficher_graphique(tree, titre=f"Git — {sys.argv[1]}")
        except (ValueError, RuntimeError) as e:
            print(f"  [Erreur] {e}")

    else:
        print("Usage :")
        print("  python main.py                        -> demo")
        print("  python main.py <depot>                -> afficher depot")
        print("  python main.py <depot> --loop         -> mode interactif")
        print("  python main.py <depot> --graph        -> graphique")


if __name__ == "__main__":
    main()
