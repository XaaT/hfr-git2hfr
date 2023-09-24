# git2hfr

* Réécriture from scratch en Python 3 pour être utilisé avec GitHub Actions

## Finalité

* TODO

## Méthode

### Exécution

* git2hfr utilise les variables d'environnement pour comprendre sa configuration
    * `HFR_LOGIN` et `HFR_PASSWD` pour l'authentification
    * Régler ces variables (exécution locale) :
        ```bash
        export HFR_LOGIN=Cule
        export HFR_PASSWD=UnMouton
        ```
    > [!NOTE]
    > Pour ne pas garder en mémoire (`history`) un secret : ajouter un espace avant la commande `export`. Exemple : ` export HFR_PASSWD=UnMouton`

### Options

* TODO
