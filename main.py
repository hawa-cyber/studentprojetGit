"""
main.py — Point d'entrée du projet GitQuest.

Modes d'utilisation :
    python main.py                                      -> demo avec données fictives
    python main.py <chemin_depot>                       -> affiche un vrai dépôt Git
    python main.py <chemin_depot> --loop                -> boucle interactive (question par défaut)
    python main.py <chemin_depot> --graph               -> visualisation graphique matplotlib
    python main.py <chemin_depot> --save-target <f.json>          -> [ENSEIGNANT] sauvegarde l'état comme question
    python main.py <chemin_depot> --save-target <f.json> --desc X -> [ENSEIGNANT] idem avec description
    python main.py <chemin_depot> --loop --target <f.json>        -> [ÉTUDIANT] résout une question

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


def boucle_interactive(repo_path: str, tree_cible: GitTree) -> None:
    """Lance une boucle interactive de visualisation Git avec comparaison d'états.

    À chaque tour, la boucle :
      1. Lit l'état actuel du dépôt.
      2. Affiche l'état actuel et l'état cible côte à côte.
      3. Vérifie si l'état cible est atteint.
      4. Demande une commande à l'utilisateur.
      5. Exécute la commande dans le dépôt.
      6. Répète jusqu'à 'exit' ou jusqu'à l'atteinte de l'état cible.

    Args:
        repo_path:   Chemin vers le dépôt Git à utiliser.
        tree_cible:  L'arbre Git cible à atteindre (question de l'enseignant).
    """
    from git_reader import read_repo

    print("\n" + "=" * 40)
    print("  Mode interactif")
    print("  Objectif : atteindre l'etat cible.")
    print("  Tapez 'exit' pour quitter.")
    print("=" * 40)

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
# FONCTIONNALITÉ ENSEIGNANT — Sauvegarde d'un état cible
# ─────────────────────────────────────────────────────────────────────────────

def sauvegarder_question(repo_path: str, fichier_sortie: str,
                         description: str = "") -> None:
    """Capture l'état actuel d'un dépôt et le sauvegarde comme question JSON.

    Workflow enseignant :
        1. Préparer un dépôt Git dans l'état que les étudiants doivent atteindre.
        2. Lancer : python main.py <depot> --save-target question.json
        3. Distribuer le fichier question.json aux étudiants.
        4. Les étudiants lancent : python main.py <leur_depot> --loop --target question.json

    Args:
        repo_path:      Chemin vers le dépôt Git à capturer.
        fichier_sortie: Chemin du fichier JSON à créer.
        description:    Description textuelle de l'objectif (optionnelle).
    """
    from git_reader import read_repo
    from question import sauvegarder_cible

    try:
        tree = read_repo(repo_path)
        afficher_encadre(tree, commande=f"état capturé depuis : {repo_path}")
        sauvegarder_cible(tree, fichier_sortie, description)
    except (ValueError, RuntimeError) as e:
        print(f"  [Erreur] {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def _afficher_aide() -> None:
    """Affiche l'aide complète avec tous les modes disponibles."""
    print("""
Usage :
  python main.py                                           demo (données fictives)
  python main.py <depot>                                   afficher un dépôt
  python main.py <depot> --loop                            mode interactif (question par défaut)
  python main.py <depot> --graph                           visualisation graphique

  [Enseignant]
  python main.py <depot> --save-target <fichier.json>      sauvegarder l'état comme question
  python main.py <depot> --save-target <f.json> --desc X   idem avec une description

  [Étudiant]
  python main.py <depot> --loop --target <fichier.json>    résoudre une question
""")


def main() -> None:
    """Analyse les arguments et lance le mode correspondant."""
    args = sys.argv[1:]

    # ── Aucun argument → démo ─────────────────────────────────────────────
    if not args:
        demo_arbre_arbitraire()
        _afficher_aide()
        return

    depot = args[0]

    # ── --save-target <fichier> [--desc <texte>] ──────────────────────────
    if "--save-target" in args:
        idx = args.index("--save-target")
        if idx + 1 >= len(args):
            print("  [Erreur] --save-target requiert un nom de fichier.")
            print("  Exemple : python main.py <depot> --save-target question.json")
            return
        fichier = args[idx + 1]
        description = ""
        if "--desc" in args:
            idx_desc = args.index("--desc")
            if idx_desc + 1 < len(args):
                description = args[idx_desc + 1]
        sauvegarder_question(depot, fichier, description)
        return

    # ── --loop [--target <fichier>] ───────────────────────────────────────
    if "--loop" in args:
        if "--target" in args:
            idx = args.index("--target")
            if idx + 1 >= len(args):
                print("  [Erreur] --target requiert un nom de fichier JSON.")
                print("  Exemple : python main.py <depot> --loop --target question.json")
                return
            from question import charger_cible
            try:
                tree_cible = charger_cible(args[idx + 1])
            except (FileNotFoundError, ValueError) as e:
                print(f"  [Erreur] {e}")
                return
        else:
            # Question par défaut (état cible codé dans comparaison.py)
            tree_cible = creer_arbre_cible()
        boucle_interactive(depot, tree_cible)
        return

    # ── --graph ───────────────────────────────────────────────────────────
    if "--graph" in args:
        from git_graph import afficher_graphique
        from git_reader import read_repo
        try:
            tree = read_repo(depot)
            afficher_graphique(tree, titre=f"Git — {depot}")
        except (ValueError, RuntimeError) as e:
            print(f"  [Erreur] {e}")
        return

    # ── Affichage simple d'un dépôt ───────────────────────────────────────
    if len(args) == 1:
        afficher_depot(depot)
        return

    # ── Argument inconnu ──────────────────────────────────────────────────
    print(f"  [Erreur] Option inconnue : {args[1:]}")
    _afficher_aide()


if __name__ == "__main__":
    main()
