# LEGACY

* Script antérieur à la réécriture en python.

---

# git2hfr

**git2hfr** est un script écrit en PHP qui permet de mettre à jour automatiquement un ou plusieurs posts sur hfr à partir d'un contenu disponible en ligne.

La fonctionalité première de git2hfr est d'être appelé via un [webhook](https://developer.github.com/webhooks/) lorsqu'un post colaboratif (géré sur GitHub) est mis à jour.

## Installation
**git2hfr** a besoin d'un interpréteur PHP pour fonctionner et d'un serveur web accessible depuis les internets pour être appelé depuis un webhook. Et il nécessite au moins l'extension php-xml.

Vous pouvez aussi demander à XaTriX d'héberger vos scripts, voir [le topic idoine](https://forum.hardware.fr/hfr/Programmation/Divers-6/automatique-participative-posts-sujet_146781_1.htm).

## Configuration
**git2hfr** doit être configuré avant de pouvoir être utilisé, il y a trois paramètres à renseigner dans la section `/* les paramètres */` du script :
- le tableau des posts à mettre à jour, voir la section dédiée au [tableau des posts](README.md#le-tableau-des-posts)
- les cookies d'identification, voir la section sur la récupération des [cookies d'identification](README.md#les-cookies-didentification)
- la clé de sécurisation du webhook qui est oprionnelle, voir la section sur la [sécurisation du script](README.md#la-s%C3%A9curisation-du-script)

## Le tableau des posts
Le tableau des posts est un [tableau de tableaux en PHP](http://php.net/manual/en/language.types.array.php) qui regroupe les paramètres de chaque post à mettre à jour, pour chaque post il y a trois paramètres :
- `"source"` : le lien vers le contenu qui doit remplacer le contenu actuel du post
- `"formulaire"` : le lien vers la page d'édition normale du post
- `"message"` : qui est **optionnel**, le contenu, directement en BBCode dans le script, du message d'annonce de la mise à jour du post, voir aussi la section sur le [message du commit](README.md#le-message-du-commit)

Dans le script, deux posts sont configurés pour l'exemple, il peut n'y en avoir qu'un ou beaucoup plus mais attention au temps d'execution du script dans ce cas.

## Les cookies d'identification
Les cookies d'identification sont les deux cookies envoyés par le forum : `md_user` et `md_pass`.

Pour récupérer ces cookies il s'uffit de regarder les entêtes d'une page du forum en étant connecté en utilisant les outils de développement du navigateur par exemple.

Les cookies d'identification doivent évidement correspondre a l'auteur du ou des posts à mettre à jour.

## La sécurisation du script
Le serveur web du script peut être configuré pour limiter l'accès au script aux [urls de GitHub](https://api.github.com/meta) par exemple pour Apache : `Require ip 192.30.252.0/22 185.199.108.0/22 140.82.112.0/20`

Le webhook peut aussi être sécurisé avec une clé dans le champ "secret" du webhook, il suffit dans ce cas de remmetre cette même clé dans la clé de sécurisation du script (`$key`).

Si la clé de sécurisation dans le script est vide il n'y a pas de vérification de la clé envoyée ou non par GitHub.

## Le message du commit
Le champ `"message"` du [tableau des posts](README.md#le-tableau-des-posts) permet d'insérrer le message du dernier commit inclus dans le push, pour cela il suffit de mettre la chaine `COMMIT_MESSAGE` qqpart dans le contenu du message d'annonce.

## Limitations
Le script ne gère que le content-type `application/json`. Il n'analyse pas non plus le message envoyé par GitHub (uniquement [la clé de sécurisation](README.md#la-s%C3%A9curisation-du-script) et [le message du commit](README.md#le-message-du-commit)) il est donc inutile de le faire s'executer sur autre chose que le `push event` par défaut.

## La réponse du script
Le script retourne une page HTML contenant soit les erreurs PHP rencontrées soit les informations suivantes :
- la sécurisation : soit `pas de clé de sécurisation` si la clé n'est pas renseignée , soit `pas de signature` ou `sécurisation caca` si la comparaison des clés échoue ou n'est pas possible (la clé n'est pas envoyée dans les entêtes) ou soit `sécurisation ok` quand la comparaison des clés réussit
- puis, pour autant de méssages édités ou postés : `Votre message a été édité avec succès !` ou `Votre réponse a été postée avec succès !` tel que renvoyé par hfr ou, le cas échéant, le message d'erreur renvoyé par hfr
