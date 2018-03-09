# AMCtoOwncloud
*AMCtoOwncloud* is a *Nautilus script* that sends *[Auto Multiple Choice](http://auto-multiple-choice.net/)* (*AMC*) annotated papers to *Owncloud/Nextcloud* and share them with the corresponding students.

Each quiz file is uploaded to a remote folder unique to each student. Then each folder is:
 * shared with the student who can be a local user or a remote user on another federated server
 * shared by link

Eventually, shared links are saved to a newly created `.csv` file (default behaviour) or to the current `.csv` file.

In the end, the remote folder structure will look like this:

    Quizzes/
    ├── 3emeE/
    |   ├── MOUSE Mickey (3998) - Maths Quizzes/
    │   │   └── Quiz 1 - MOUSE Mickey (3998).pdf
    │   └── MOUSE Minnie (3999) - Maths Quizzes/
    │       └── Quiz 1 - MOUSE Minnie (3999).pdf
    └── 4emeE/
        └── DUCK Donald (4999) - Maths Quizzes/
            └── Quiz 1 - DUCK Donald (3999).pdf

But the root folder `Quizzes/`, `Quiz 1`, and `Maths Quizzes` are configurable, and the other fields come from the `.csv` file. For instance, If you don't have groups specified in you `.csv` file, and you leave the root folder empty `''`, it can also look like this: 

    MOUSE Mickey (3998) - Maths Quizzes/
        └── Quiz 1 - MOUSE Mickey (3998).pdf
    MOUSE Minnie (3999) - Maths Quizzes/
        └── Quiz 1 - MOUSE Minnie (3999).pdf
    DUCK Donald (4999) - Maths Quizzes/
        └── Quiz 1 - DUCK Donald (3999).pdf

## Installation
Copy `AMCtoOwncloud.sh` and `.AMCtoOwncloud.py` in the Nautilus scripts folder: `~/.local/share/nautilus/scripts/`

<img src="/docs/InstallingScript.png" width="600x">

In order to make it work, you need to install the following Python modules:

`requests`, `lxml.html`, `owncloud` (see [pyocclient](https://github.com/owncloud/pyocclient)).

You also need `gnome-terminal` or you will have to edit the `AMCtoOwncloud.sh` script file to use another terminal.

## Configuration

Edit the `.AMCtoOwncloud.py` and change the parameters at the end:
    
    CSV = '/path/to/csv/students.csv'
    FOLDER = 'Quizzes/'
    ADDRESS = 'https://ncloud.zaclys.com'
    USERNAME = 'MyUserName'
    
The CSV file containing all your student information must use colons `:` as separators and the following headers (there are optional parameters in method `identify_students()` to change this behaviour, see [below](https://github.com/remjg/AMCtoOwncloud/blob/master/README.md#special-use-case)):

    group:surname:name:number:owncloud:email
    3emeE:MOUSE:Mickey:3998:cabitzmil:mickeymouse@domain.com
    3emeE:MOUSE:Minnie:3999:agrevet:minniemouse@domain.com
    4emeE:DUCK:Donald:4999:prenaud@aFederatedServer.com:donaldduck@domain.com
    
Finally, **annotated papers must contain the student number** in their name
(the first number of the file name is extracted to associate each quiz to the corresponding student). Don't forget to configure *auto-multiple-choice* using the column headers of your `.csv` file:

<img src="/docs/RenamingAnnotatedPapers.png" width="400x">
    
## Use
*Right click* on the annotated papers (or on folders) and go to the submenu *scripts*:

<img src="/docs/UsingScript1-Menu.png" width="600x">

Then enter your *Owncloud* password, the name of the quiz, and wait:

<img src="/docs/UsingScript2-Output.png" width="800x">

Every encountered issue should be displayed (unmatched files, login error, uploading or sharing errors).

## Special use cases

To change the script behaviour, you can edit the last four lines:

    amcsend = AMCtoOwncloud()
    amcsend.identify_students(csv_filepath=CSV)
    amcsend.connect_owncloud(address=ADDRESS, username=USERNAME, SSO=False)
    amcsend.upload_and_share(folder_root=FOLDER, replace_csv=False)

For instance, if your *Owncloud* server is behind a *Central Authentication Service (CAS)*, you might want to use the parameter `SSO=True`. It has been tested with the Virtual Learning Environment [Envole](https://envole.ac-dijon.fr) of a school that use CAS fo authentication.

You can also save shared links to the current `.csv` file with `replace_csv=True`. Make sure to backup before and be aware that *comment lines starting with a `#` are lost in the process*.

More options are available, see below for a full list of parameters with default values:

    amcsend = AMCtoOwncloud(list_of_paths=None, verbose=False)
    amcsend.identify_students(csv_filepath=CSV, verbose=False, debug=False,
                              csv_delimiter=":",
                              csv_comment="#",
                              name_header="name",
                              surname_header="surname",
                              group_header="group",
                              number_header="number",
                              email_header="email",
                              owncloud_header="owncloud",
                              link_header="link")
    amcsend.connect_owncloud(address=ADDRESS, username=USERNAME, password=None, SSO=False)
    amcsend.upload_and_share(folder_root=FOLDER, folder_name=" - Maths Quizzes",
                                                 quiz_name=None,
                                                 share_with_user=True,
                                                 share_by_link=True,
                                                 replace_csv=False)
