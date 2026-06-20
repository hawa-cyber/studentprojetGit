# GitQuest — Visualiseur d'arbres Git

Outil de visualisation d'arbres Git développé en Python dans le cadre d'un projet
tutoré (IUT Clermont-Auvergne, BUT Science des Données, 2ème année).

Deux modes d'affichage :
- Terminal encadré avec 3 colonnes alignées (références, arbre, hash + message)
- Fenêtre graphique avec cercles colorés par branche, flèches et étiquettes

---

## Structure du projet

```
Dossier/
├── main.py           Point d'entrée — gère les 5 modes d'utilisation
├── git_tree.py       Structure de données GitTree, tri topologique (algorithme de Kahn)
├── git_reader.py     Lecture d'un vrai dépôt Git via subprocess
├── display.py        Affichage encadré dans le terminal avec rich
├── git_graph.py      Affichage graphique avec matplotlib (une couleur par branche)
├── comparaison.py    État cible par défaut et comparaison topologique d'arbres Git
├── question.py       [NOUVEAU] Outil enseignant : création et chargement de questions
├── requirements.txt  Dépendances Python
└── .gitignore
```

---

## Installation

```
pip install -r requirements.txt
```

---

## Utilisation

### Mode démo (données fictives)

```
python main.py
```

Affiche un arbre Git fictif avec 4 commits et 2 branches.

### Afficher un dépôt existant

```
python main.py <chemin_depot>
```

### Mode interactif (question par défaut)

```
python main.py <chemin_depot> --loop
```

Affiche l'état actuel du dépôt et l'état cible côte à côte dans le terminal.
La session se termine quand l'état cible est atteint ou avec `exit`.

### Affichage graphique

```
python main.py <chemin_depot> --graph
```

---

## Fonctionnalité Enseignant — Créer une question

### Étape 1 — Préparer le dépôt cible

L'enseignant prépare un dépôt Git dans l'état que les étudiants devront atteindre.
Par exemple : créer deux branches, effectuer des commits, créer un tag.

### Étape 2 — Sauvegarder l'état comme question

```
python main.py <chemin_depot> --save-target question1.json
```

Avec une description de l'objectif :

```
python main.py <chemin_depot> --save-target question1.json --desc "Créer une branche feature avec 2 commits"
```

Cela génère un fichier `question1.json` contenant la structure Git cible.

### Étape 3 — Distribuer la question aux étudiants

L'enseignant distribue le fichier `question1.json` aux étudiants.

### Étape 4 — L'étudiant résout la question

```
python main.py <chemin_depot_etudiant> --loop --target question1.json
```

L'outil affiche côte à côte l'état actuel du dépôt de l'étudiant et l'état cible.
Quand les deux états correspondent, la session se termine automatiquement.

---

## Format du fichier de question (JSON)

```json
{
  "description": "Créer une branche feature avec 2 commits",
  "commits": [
    {
      "hash": "a1b2c3d",
      "message": "Initial commit",
      "parents": [],
      "refs": ["tag: v1.0"]
    },
    {
      "hash": "b2c3d4e",
      "message": "Ajout README",
      "parents": ["a1b2c3d"],
      "refs": ["HEAD -> main"]
    }
  ]
}
```

Les fichiers JSON peuvent être créés manuellement ou via `--save-target`.

---

## Références

- Dépôt original : https://github.com/denis-migdal-Student-projects/GitQuest
- Fork personnel : https://github.com/hawa-cyber/studentprojetGit
- Documentation Git : https://git-scm.com/doc
