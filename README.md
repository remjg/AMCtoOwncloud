# AMCtoOwncloud
*AMCtoOwncloud* is a *Nautilus script* that sends *[Auto Multiple Choice](http://auto-multiple-choice.net/)* (*AMC*) annotated sheets to *Owncloud/Nextcloud* and share them with students.

Each quiz file is uploaded to a remote folder unique to the corresponding student:

    /OWNCLOUD_FOLDER/Group/Surname - Name (Number) - Interros Maths/
    
Then the folder is shared (if not already) with the student who can be a local user or a remote user on another federated server.

## Installation
Copy `AMCtoOwncloud.sh` and `.AMCtoOwncloud.py` in the Nautilus scripts folder: `~.local/share/nautilus/scripts/`

<img src="/docs/InstallingScript.png" width="600x">

In order to make it work, you need to install the following Python modules:
`os`, `csv`, `re`, `owncloud`, `getpass`, `requests`, `lxml.html`

You also need `gnome-terminal` or you need to change the `AMCtoOwncloud.sh` script file.

## Configuration

Edit the `.AMCtoOwncloud.py` and change parameters at the beginning:
    
    CSV_FILE_PATH = '/home/username/students.csv' # students information
    OWNCLOUD_FOLDER = 'Interro Maths/' # default folder for uploading files
    OWNCLOUD_ADDRESS = 'http://MyOwnCloudProvider.com/'
    OWNCLOUD_USERNAME = 'MyUserName'
    
The CSV file containg all your student information must use colons `:` as separators and the following headers (of course you can edit the script to change this behaviour):

    group:surname:name:number:email:owncloud
    4emeA:MOUSE:Mickey:401:mmouse@domain.com:mmouse
    3emeB:DUCK:Donald:304:dduck@domain.com:dduck@AnotherOwncloudServer.com/owncloud
    
Finally, **annotated sheets must contain the student number** in their name
(the first number of the file name is extracted to associate each quiz to the corresponding student). Don't forget to configure auto-multiple-choice!
    
## Use
*Right click* on the annotated sheets (or on folders) and go to the submenu *scripts*:

<img src="/docs/UsingScript.png" width="600x">

## Special use case
If your Owncloud server is behind a Central Authentication Service (CAS), you might want to use `connect_owncloud_behind_sso()` instead of `connect_owncloud()`.
If that is the case, you just have to comment/uncomment the following lines as follow:

    #owncloud_client = connect_owncloud(OWNCLOUD_ADDRESS, OWNCLOUD_USERNAME)
    owncloud_client = connect_owncloud_behind_sso(OWNCLOUD_ADDRESS, OWNCLOUD_USERNAME)
    
Tested with the Virtual Learning Environment [Envole](https://envole.ac-dijon.fr) of a school that use CAS fo authentication.
