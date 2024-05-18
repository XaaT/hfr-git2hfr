# git2hfr

* Réécriture en Python avec compatibilité GitHub Actions et ajout de fonctionnalités

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

## Legacy

* Le script PHP antérieur est disponible sur la [branche legacy](https://github.com/XaaT/hfr-git2hfr/tree/legacy)
