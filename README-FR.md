# AMCtoOwncloud

*AMCtoOwncloud* est un *script Nautilus* qui permet d'envoyer simplement les copies corrigées avec *[Auto Multiple Choice (AMC)](http://auto-multiple-choice.net/)* sur un serveur *Owncloud/Nextcloud*.

Chaque copie est téléversée dans un dossier unique créé pour chaque étudiant qui sera :
 * *partagé avec l'étudiant* (qui peut être un utilisateur local ou distant sur un serveur fédéré) ;
 * *partagé par lien*.

Les liens partagés sont ensuite sauvegardés dans un nouveau fichier `.csv` (comportement par défaut) ou dans le fichier `.csv` courant.

Après exécution du programme, la hiérarchie des fichiers est la suivante :

    Contrôles/
    ├── 3emeE/
    |   ├── MOUSE Mickey (3998) - Interros Maths/
    │   │   └── Interro 1 - MOUSE Mickey (3998).pdf
    │   └── MOUSE Minnie (3999) - Interros Maths/
    │       └── Interro 1 - MOUSE Minnie (3999).pdf
    └── 4emeE/
        └── DUCK Donald (4999) - Interros Maths/
            └── Interro 1 - DUCK Donald (3999).pdf

Les noms `Contrôles/`, `Interro 1`, et `Interros Maths` sont modifiables, et les autres champs sont extraits du fichier `.csv` des étudiants. Par exemple, si vous n'avez pas de classes saisies dans votre fichier `.csv`, et si vous dossier racine est vide `''`, l'organisation des fichiers deviendra : 

    MOUSE Mickey (3998) - Interros Maths/
        └── Interro 1 - MOUSE Mickey (3998).pdf
    MOUSE Minnie (3999) - Interros Maths/
        └── Interro 1 - MOUSE Minnie (3999).pdf
    DUCK Donald (4999) - Interros Maths/
        └── Interro 1 - DUCK Donald (3999).pdf

## Utilisation

Faire un *clic droit* sur les copies corrigées (ou sur les dossiers les contenant) et se rendre dans le menu *scripts* :

<img src="/docs/UsingScript1-Menu.png" width="600x">

Saisir le mot de passe *Owncloud* , le nom du contrôle, et attendre :

<img src="/docs/UsingScript2-Output.png" width="800x">

Les éventuels problèmes recontrés devraient être indiqués (erreurs d'identification, d'envoi ou de partage, fichiers non associés à des étudiants).

## Installation

Copier `AMCtoOwncloud.sh` and `.AMCtoOwncloud.py` dans le répertoire des scripts Nautilus : `~/.local/share/nautilus/scripts/`

<img src="/docs/InstallingScript.png" width="600x">

Installer les modules Python suivants :

`requests`, `lxml.html`, `owncloud` (voir [pyocclient](https://github.com/owncloud/pyocclient)).

Vérifier que `gnome-terminal` est installé ou éditer le fichier `AMCtoOwncloud.sh` pour utiliser un autre terminal.

## Configuration

Éditer le fichier `.AMCtoOwncloud.py` et changer les paramètres suivants à la fin du programme :
    
    CSV = '/chemin/vers/csv/etudiants.csv'
    FOLDER = 'Contrôles/'
    ADDRESS = 'https://ncloud.zaclys.com'
    USERNAME = 'NomUtilisateur'
    
Le fichier `.csv` contenant les informations des étudiants doit utiliser des points-virgules `;` comme séparateurs ainsi que les en-têtres de colonnes suivants (il y a des paramètres optionnels dans la méthode `identify_students()` pour personnaliser ce comportement, voir [plus bas](https://github.com/remjg/AMCtoOwncloud/blob/master/README-FR.md#cas-particuliers-dutilisation)):

    group;surname;name;id;owncloud;email
    3emeE;MOUSE;Mickey;3998;cabitzmil;mickeymouse@domain.com
    3emeE;MOUSE;Minnie;3999;agrevet;minniemouse@domain.com
    4emeE;DUCK;Donald;4999;prenaud@aFederatedServer.com;donaldduck@domain.com
    
Enfin, **les copies corrigées doivent comporter le numéro d'étudiant** dans leur nom de fichier
(le premier nombre est extrait pour associer chaque copie à l'étudiant correspondant). Pour ce faire, ne pas oublier de configurer *auto-multiple-choice* avec les mêmes en-têtes que dans votre fichier `.csv` :

<img src="/docs/RenamingAnnotatedPapers.png" width="400x">

## Cas particuliers d'utilisation

Pour personnaliser le comportement du script, vous pouvez éditer les 4 dernières lignes du fichier `.AMCtoOwncloud.py` :

    amcsend = AMCtoOwncloud()
    amcsend.identify_students(csv_filepath=CSV)
    amcsend.connect_owncloud(address=ADDRESS, username=USERNAME, SSO=False)
    amcsend.upload_and_share(folder_root=FOLDER, replace_csv=False)

Par exemple, si votre serveur *Owncloud* se trouve derrière un *portail d'authentification unique*, vous pouvez utiliser l'option `SSO=True`. Testé avec un espace numérique de travail [Envole](https://envole.ac-dijon.fr) qui utilise *[CAS](https://fr.wikipedia.org/wiki/Central_Authentication_Service)* comme portail d'authentification unique.

Vous pouvez aussi sauvegarder les liens partagés dans le fichier `.csv` courant avec l'option `replace_csv=True`. Pensez à faire une sauvegarde avant et notez que *les lignes commençant par un `#` (commentaires) seront perdues lors du processus*.

Plus d'options sont disponibles, vous pouvez trouver ci-dessous une liste complète de toutes les options avec les paramètres par défaut :

    amcsend = AMCtoOwncloud(list_of_paths=None, verbose=False)
    amcsend.identify_students(csv_filepath=CSV, verbose=False, debug=False,
                              csv_delimiter=";",
                              csv_comment="#",
                              name_header="name",
                              surname_header="surname",
                              group_header="group",
                              number_header="id",
                              email_header="email",
                              owncloud_header="owncloud",
                              link_header="link")
    amcsend.connect_owncloud(address=ADDRESS, username=USERNAME, password=None, SSO=False)
    amcsend.upload_and_share(folder_root=FOLDER, folder_name=" - Maths Quizzes",
                                                 quiz_name=None,
                                                 share_with_user=True,
                                                 share_by_link=True,
                                                 replace_csv=False)

## Générer des courriers d'informations

Un document LaTeX est aussi présent dans le dossier `/information letters/` pour imprimer les liens partagés ainsi que le QC code correspondant pour chaque étudiant :

<img src="/docs/InformationLetter.png" width="600x">
