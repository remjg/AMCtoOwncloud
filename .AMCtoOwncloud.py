#!/usr/bin/python3
#
# Nautilus script that sends AMC annotated papers to Owncloud
# Copyright (C) 2017 Rémi GROLLEAU
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import csv
import re
import owncloud
import getpass
import requests # for owncloud behind SSO only
import lxml.html # for owncloud behind SSO only


### Parameters to tweak


CSV_FILE_PATH = '/home/username/students.csv'
OWNCLOUD_FOLDER = 'QuizzesFolder/'
OWNCLOUD_ADDRESS = 'http://ncloud.zaclys.com/'
OWNCLOUD_USERNAME = 'MyUserName'


### class and functions


class Student:
    """Student object"""
    
    def __init__(self,  name='', surname='', group='', number = '',
                 email='', owncloud='', quiz=''):
        """Define a Student and stores all the corresponding attributes.
        
        - name
        - surname
        - group (or class)
        - identification number
        - email
        - owncloud username
        - quiz path
        """
        self.name = name
        self.surname = surname
        self.group = group
        self.number = number
        self.email = email
        self.owncloud = owncloud
        self.quiz = quiz


    def print(self):
        """Display Student attributes."""
        print(' {0:15} {1:15} {2:5} {3:4} {4:40} {5:40} {6}'.format(
                                                             self.surname,
                                                             self.name,
                                                             self.group,
                                                             self.number,
                                                             self.email,
                                                             self.owncloud,
                                                             self.quiz))


def get_files_paths_from_nautilus():
    """Get paths of files selected in Nautilus file manager.
    
    Look also into selected folders (but not in subfolders).
    Returns a list of file paths that are not symbolic links.
    """ 
    # Retrieve paths selected in Nautilus
    if 'NAUTILUS_SCRIPT_SELECTED_FILE_PATHS' in os.environ:
        selection = os.environ['NAUTILUS_SCRIPT_SELECTED_FILE_PATHS']

    # Parse selection and folders and keep files which are not sym link
    list_of_files = []
    for path in selection.splitlines():
        # path is a file: keep if not sym link
        if os.path.isfile(path): 
            if not os.path.islink(path):
                list_of_files.append(path) 
        # path is a folder: parse it and keep if not sym link
        else: 
            for f in os.listdir(path):
                newpath = os.path.join(path,f)
                if os.path.isfile(newpath) and not os.path.islink(newpath):
                    list_of_files.append(newpath)

    print( '{0} files selected:'.format( len(list_of_files) ) )
    print( ' '+'\n '.join( list_of_files ) )
    return list_of_files


def get_students_from_csv(  csv_file_path, csv_delimiter=':', csv_comment='#', 
                            name_header="name",
                            surname_header="surname",
                            group_header="group",
                            number_header = "number",
                            email_header="email",
                            owncloud_header="owncloud",
                            verbose=False):
    """Extract student information from a CSV file.
    
    Returns a dictionary of all students (key = number, value = student object)
    """
    dict_of_students = {}
    with open(csv_file_path, newline='') as csv_file:
        tab = csv.DictReader((row for row in csv_file
                              if not row.startswith(csv_comment)),
                             delimiter=csv_delimiter)
        for row in tab: 
            student = Student(  name = row[name_header], 
                                surname = row[surname_header],
                                group = row[group_header],
                                number = row[number_header],
                                email = row[email_header],
                                owncloud = row[owncloud_header])
            dict_of_students[student.number] = student
    
    print('\nFound {} students in {}.'.format( len(dict_of_students),
                                                csv_file_path
                                              ))
    if verbose:
        for student in dict_of_students.values():
            student.print()
    return dict_of_students
    

def associate_quiz_to_student(list_of_quiz, dict_of_students, verbose=False):
    """Associate each quiz to a student.
    
    Update quiz attribute of each student with the corresponding file path.
    Returns a list of students that matched quizzes.
    """ 
    matched_students = []
    unmatched_quiz = []
    
    for quiz_path in list_of_quiz:
        # extract the first number in the file name
        quiz_name = os.path.basename(quiz_path)
        regular_expression = re.compile('[0-9]+')
        student_number = re.search(regular_expression,quiz_name).group()
        try:
            # update the quiz attribute with file path
            dict_of_students[student_number].quiz = quiz_path
            matched_students.append(dict_of_students[student_number])
        except:
            # store unmatched files
            unmatched_quiz.append(quiz_path)                
    
    print('\n{}/{} quizzes matched'.format(len(matched_students),
                                        len(list_of_quiz)))
    if verbose:
        for student in matched_students:
            print(' {:15} {:15} n°{:3} {}'.format(student.surname,
                                                  student.name,
                                                  student.number,
                                                  student.quiz))
    if len(matched_students) != len(list_of_quiz):
        print('Unmatched file(s):')
        for quiz_path in unmatched_quiz:
            print(' {}'.format( quiz_path ))
        cancel = input('Do you want to continue? (y/n) ')
        if cancel.lower() == 'n':
            quit('\nScript cancelled !')
    return matched_students


def connect_owncloud(address, username, password=None):
    """Prompt for a password, connect to Owncloud.
    
    Return a Client object.
    """
    oc = owncloud.Client(address)
    if password == None:
        password = getpass.getpass('\nEnter Owncloud password: ')
    print('\nConnecting to Owncloud... ', end="")
    try:
        oc.login(username, password)
    except Exception as e:
        print('Error logging in! {}'.format(e))
        retry = input('Try again? (y/n) ')
        if retry.lower() == 'y':
            oc = connect_owncloud(address, username, password=None)
        else:
            quit()
            
    print('Connected !')
    return oc
    

def connect_owncloud_behind_sso(owncloud_address, username, password=None):
    """Prompt for a password, connect to Owncloud behind SSO (single sign on).
    
    Return a Client object.
    """
    # Get the hidden form fields needed to log in (CSRF token)
    s = requests.session()
    sso_address = s.get(owncloud_address).url # follow redirection
    login = s.get(sso_address)
    login_html = lxml.html.fromstring(login.text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
    
    # Fill out the form with username and password
    if password == None:
        password = getpass.getpass('\nEnter Owncloud password: ')
    form['username'] = username
    form['password'] = password
    response = s.post(sso_address, data=form)
    # print(response.url) # to check if it worked
    print('\nConnecting to Owncloud... ', end="")
    oc = owncloud.Client(owncloud_address)
    oc._session = s
        
    # Connect
    try:        
        oc._update_capabilities()
        print('Ok !')
    except Exception as e:
        print('Error logging in! {}'.format(e))
        retry = input('Try again? (y/n) ')
        if retry.lower() == 'y':
            oc = connect_owncloud_behind_sso(   owncloud_address,
                                                login, password=None)
        else:
            quit()
    
    # Hack, why does it work? https://github.com/owncloud/pyocclient/issues/204
    oc._session = requests.session()
    oc._session.verify = oc._verify_certs
    oc._session.auth = (username, password)

    return oc


def upload_and_share_quiz(owncloud_client, list_of_students, folder_base,
                          quiz_name = None):
    """ Create and share students remote folders if necessary and upload quizzes
    
    Create remote folders for each students (if not already there):
    "/folder_base/Group/Surname - Name (Number) - Interros Maths/"
    
    Upload students quizzes:
    "User input - Surname Name (Number).ext"
    
    Share folders with the corresponding students (if not already done).   
    """
    if quiz_name == None:
        quiz_name = input('Enter quiz name: ')
    students_total = len(list_of_students)
    students_current = 0
    print('\nUploading files...')
    
    # Create remote folders if necessary 
    try:
        owncloud_client.mkdir(folder_base)
        print('Created folder ' + folder_base)
    except:
        pass
    for student in list_of_students:
        students_current += 1
        folder_group = student.group + '/'
        folder_student = ( student.surname 
                        + ' '  + student.name 
                        + ' (' + student.number + ')'
                        + ' - Interros Maths/')
        remote_folder = folder_base + folder_group + folder_student
        try:
            owncloud_client.mkdir(folder_base + folder_group)
            print(  ('{}/{} Created folder ' 
                    + folder_base 
                    + folder_group
                    ).format(students_current, students_total) )
        except:
            pass
        try:
            owncloud_client.mkdir(remote_folder)  
            print(  ('{}/{} Created folder ' 
                    + remote_folder
                    ).format(students_current, students_total) )
        except:
            pass
        
        # Define remote quiz name et send
        remote_quiz_name = ( quiz_name + ' - '
                            + student.surname 
                            + ' '  + student.name 
                            + ' (' + student.number + ')'
                            + '.'  + student.quiz.split(".")[-1]) # extension
        remote_quiz_path =  ( remote_folder
                            + remote_quiz_name)
        try:
            owncloud_client.put_file(remote_quiz_path, student.quiz)
            print(  ('{}/{} Sent file ' 
                    + remote_quiz_path
                    ).format(students_current, students_total) )
        except:
            print("ERROR: Can't send file " + remote_quiz_path)
            
        # Share folders if necessary
        is_shared = False
        for file_share in owncloud_client.get_shares(remote_folder):
            if file_share.get_share_with() == student.owncloud:
                is_shared = True
                break
        if is_shared == False:
            try:
                if '@' in student.owncloud: # remote user, bug in pyocclient 0.4
                    owncloud_client.share_file_with_user(   remote_folder, 
                                                            student.owncloud + '/', 
                                                            remote_user=True)
                else: # local user
                    owncloud_client.share_file_with_user(   remote_folder, 
                                                            student.owncloud)
                print(  ( "{}/{} "
                        + remote_folder 
                        + " shared with " 
                        + student.owncloud
                        ).format(students_current, students_total) )
            except Exception as e:
                print(  ("ERROR: Can't share folder " + remote_folder 
                        + " with " + student.owncloud
                        + "\n{}").format(e) )


### Script

list_of_quiz = get_files_paths_from_nautilus()
                
dict_of_students = get_students_from_csv(CSV_FILE_PATH, verbose=False)

list_of_students = associate_quiz_to_student(list_of_quiz, dict_of_students, verbose=True)

owncloud_client = connect_owncloud(OWNCLOUD_ADDRESS, OWNCLOUD_USERNAME)
#owncloud_client = connect_owncloud_behind_sso(OWNCLOUD_ADDRESS, OWNCLOUD_USERNAME)

upload_and_share_quiz(owncloud_client, list_of_students, OWNCLOUD_FOLDER)
