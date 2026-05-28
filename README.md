# GitQuest — Visualiseur d'arbres Git

Outil de visualisation d'arbres Git développé en Python dans le cadre d'un projet
tutoré (IUT Clermont-Auvergne, BUT Science des Données, 2eme annee).

Deux modes d'affichage :
- Terminal encadré avec 3 colonnes alignées (références, arbre, hash + message)
- Fenêtre graphique avec cercles colorés par branche, flèches et étiquettes

---

## Structure du projet

```
Dossier/
├── main.py           Point d'entree — gere les 4 modes d'utilisation
├── git_tree.py       Structure de donnees GitTree, tri topologique (algorithme de Kahn)
├── git_reader.py     Lecture d'un vrai depot Git via subprocess
├── display.py        Affichage encadre dans le terminal avec rich
├── git_graph.py      Affichage graphique avec matplotlib (une couleur par branche)
├── comparaison.py    Etat cible et comparaison topologique d'arbres Git
├── requirements.txt  Dependances Python
└── .gitignore
```

---

## Installation

```
pip install -r requirements.txt
```

---

## Utilisation

Le chemin du depot peut etre absolu ou relatif.
Si le terminal est déjà dans le dossier du depot, utiliser `.` comme chemin.

### Mode demo (donnees fictives)

```
python main.py
```

Affiche un arbre Git fictif avec 4 commits et 2 branches.
Ne necessite pas de depot Git ni de git installe sur la machine.

### Afficher un depot existant

```
python main.py <chemin_depot>
```

Exemples :

```
python main.py C:/projets/mon-projet
python main.py .
```

### Mode interactif

```
python main.py <chemin_depot> --loop
```

Affiche l'etat actuel du depot et l'etat cible cote a cote dans le terminal.
L'utilisateur entre des commandes Git une par une.
La session se termine automatiquement quand l'etat cible est atteint,
ou manuellement avec la commande `exit`.

### Affichage graphique

```
python main.py <chemin_depot> --graph
```

Ouvre une fenetre matplotlib avec :
- Fond sombre, une couleur distincte par branche (violet, bleu, vert, orange...)
- Cercles colores contenant le hash court du commit
- Fleches colorees vers les commits parents
- Etiquettes de branches et tags visibles uniquement sur les commits portant des references
- Message court affiché uniquement pour les commits importants (branch tips, merges)
- Noms de branches tronques a 20 caracteres pour la lisibilite

Le graphe est scrollable et zoomable avec la barre d'outils matplotlib
(molette ou bouton loupe).

---

## Format d'affichage terminal

L'affichage terminal utilise 3 colonnes :

```
  HEAD -> main    ●          a1b2c3d   Correction bug
  feature         | ●        b2c3d4e   Nouvelle fonction
                  |/
  tag: v1.0       ●          c3d4e5f   Initial commit
```

- Colonne gauche  : branches, tags et HEAD avec symboles UTF-8
- Colonne centre  : graphe de l'arbre (noeuds, lignes verticales, convergences)
- Colonne droite  : hash court (7 caracteres) et message du commit

Symboles utilises :

| Symbole  | Signification               |
|----------|-----------------------------|
| HEAD ->  | Branche courante (HEAD)     |
| branch   | Autre branche nommee        |
| tag:     | Tag Git                     |
| /        | Convergence de deux branches|

---

## Dependances

- **rich** >= 13.0.0 : affichage encadre et colore dans le terminal
- **matplotlib** >= 3.7.0 : affichage graphique (mode --graph uniquement)

`git_reader` et `git_graph` sont importes en lazy : ils ne sont charges
que quand le mode correspondant est demande. La demo ne necessite donc
ni git installe ni matplotlib.

---

## Algorithmes

### Tri topologique — git_tree.py

Algorithme de Kahn (BFS avec degres entrants) : garantit que chaque commit
apparait avant ses parents dans la liste resultante.
Complexite : O(n + m) avec n commits et m relations parent-enfant.

### Attribution des colonnes — git_tree.py

Un tableau `lanes` maintient l'etat des colonnes actives.
Chaque entree contient le hash attendu dans cette colonne.
Le premier parent d'un commit reste dans sa colonne ; les parents
supplementaires (fusions) occupent les premieres colonnes libres.
Cette logique est exposee via `lane_assignments()` pour que `git_graph.py`
puisse l'utiliser sans dupliquer le code.

### Comparaison d'etats — comparaison.py

La fonction `etats_identiques` compare deux arbres Git en deux etapes :
1. Verifier que les noms de branches sont identiques.
2. Pour chaque branche, comparer la forme canonique de son historique.

La forme canonique d'un commit est definie de facon recursive :
    forme(commit) = (message, (forme(parent_1), forme(parent_2), ...))

Les parents sont tries pour que l'ordre de listing ne compte pas.
Le calcul est iteratif (du plus ancien au plus recent) pour eviter
tout depassement de pile sur les grands depots.
Les hashes ne sont jamais compares : deux depots ayant le meme historique
mais des hashes differents sont correctement identifies comme identiques.

---

## Auteur

Projet tutoré — IUT Clermont-Auvergne, BUT Science des Données, 2eme annee.
