#!/usr/bin/env python3
# coding: utf-8
#
# Nautilus script that sends AMC annotated papers to Owncloud/Nextcloud
# Copyright (C) 2017-2018 Rémi GROLLEAU
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
import requests  # for owncloud behind SSO only
import lxml.html  # for owncloud behind SSO only
import math
import datetime
import shutil
from pathlib import Path
import pyshorteners
from pyshorteners import Shortener

######### Implementation


class Student:
    """Student object"""

    def __init__(self,
                 name="",
                 surname="",
                 group="",
                 number="",
                 email="",
                 owncloud="",
                 quiz="",
                 link="",
                 shortlink=""):
        """Defines a Student and stores all the corresponding attributes

        - name
        - surname
        - group (or class)
        - identification number
        - email
        - owncloud username
        - quiz path
        - folder link
        - shortened link
        """
        self.name = name
        self.surname = surname
        self.group = group
        self.number = number
        self.email = email
        self.owncloud = owncloud
        self.quiz = quiz
        self.link = link

    def __str__(self):
        """To display Student attributes using print()"""
        return(f" {self.surname:15.15}"
               f" {self.name:15.15}"
               f" {self.group:5.5}"
               f" {self.number:4.4}"
               f" {self.owncloud:10.10}"
               f" {self.quiz}"
               f" {self.link}"
               f" {self.shortlink}"
               f" {self.email}")


class AMCtoOwncloud:
    """AMCtoOwncloud object"""

    def __init__(self, list_of_paths=None, verbose=False):
        """
        Looks in folders (but not subfolders) and keeps files (not symlinks).

        If no path is provided, get paths from Nautilus file manager.
        Create a _list_of_files attribute.
        """
        self._cloud_client = None
        self._csvfile = None
        self._dict_of_students = None
        self._matched_students = None
        self._list_of_files = []
        # Retrieve paths selected in Nautilus if files/folders not provided
        if not list_of_paths:
            try:
                list_of_paths = os.environ[
                                        'NAUTILUS_SCRIPT_SELECTED_FILE_PATHS']
            except:
                print(f"ERROR: no files/folders provided"
                      f" neither selected in Nautilus\n{e}")

        # Keep files which are not sym link and parse folders
        for path in list_of_paths.splitlines():
            # path is a file: keep if not sym link
            if os.path.isfile(path):
                if not os.path.islink(path):
                    self._list_of_files.append(path)
            # path is a folder: parse it and keep if not sym link
            else:
                for f in os.listdir(path):
                    newpath = os.path.join(path, f)
                    if os.path.isfile(newpath) and not os.path.islink(newpath):
                        self._list_of_files.append(newpath)

        print(f"{len(self._list_of_files)} files selected")
        if verbose:
            print(" " + "\n ".join(self._list_of_files))

    def identify_students(self, csv_filepath, verbose=False, **kwargs):
        """
        Link each file to the corresponding student.

        Create a _matched_students attribute which is a list of students.
        """
        self._get_students_from_csv(csv_filepath, verbose=verbose, **kwargs)
        self._associate_quiz_to_student(verbose=verbose)

    def _get_students_from_csv(self, csv_filepath, verbose,
                               csv_delimiter=";",
                               csv_comment="#",
                               name_header="name",
                               surname_header="surname",
                               group_header="group",
                               number_header="id",
                               email_header="email",
                               owncloud_header="owncloud",
                               link_header="link",
                               shortlink_header="shortlink",
                               debug=False):
        """Extract student information from a CSV file.

        Store students in a dictionary (key = number, value = student object).
        Save .csv file important details in a _csvfile attribute
        Create a _dict_of_students attribute.
        """
        # Save important .csv parameters for later
        self._csvfile = {}
        self._csvfile["csv_filepath"] = csv_filepath
        self._csvfile["csv_delimiter"] = csv_delimiter
        self._csvfile["csv_comment"] = csv_comment
        self._csvfile["number_header"] = number_header
        self._csvfile["link_header"] = link_header
        self._csvfile["shortlink_header"] = shortlink_header
        # Create dictionary
        self._dict_of_students = {}
        with open(csv_filepath, newline="") as csv_file:
            tab = csv.DictReader((row for row in csv_file
                                 if not row.startswith(csv_comment)),
                                 delimiter=csv_delimiter)
            for row in tab:
                try:
                    student = Student(name=row[name_header],
                                      surname=row.get(surname_header, ""),
                                      group=row.get(group_header, ""),
                                      number=row[number_header],
                                      email=row.get(email_header, ""),
                                      owncloud=row.get(owncloud_header, ""),
                                      link=row.get(link_header, ""),
                                      shortlink=row.get(shortlink_header, ""))
                except:
                    print(f"ERROR: Student without name or number in CSV file")
                self._dict_of_students[student.number] = student

        print(f'\n{len(self._dict_of_students)} students found'
              f' in "{csv_filepath}"')
        if debug:
            for student in self._dict_of_students.values():
                print(student)

    def _associate_quiz_to_student(self, verbose=False):
        """Associate each quiz to a student.

        Update quiz attribute of each student with the corresponding file path.
        Create a _matched_students attribute which is a list of students.
        """
        self._matched_students = []
        unmatched_quiz = []
        regular_expression = re.compile('[0-9]+')

        for quiz_path in self._list_of_files:
            # extract the first number in the file name
            quiz_name = os.path.basename(quiz_path)
            match = re.search(regular_expression, quiz_name)
            if match:
                student_number = match.group()
            try:
                # update the quiz attribute with file path
                self._dict_of_students[student_number].quiz = quiz_path
                self._matched_students.append(
                                        self._dict_of_students[student_number])
            except:
                # store unmatched files (no student number or incorrect number)
                unmatched_quiz.append(quiz_path)

        print(f"\n{len(self._matched_students)}/"
              f"{len(self._list_of_files)} files matched")
        if verbose:
            for student in self._matched_students:
                print(f" {student.surname:15.15} {student.name:15.15}"
                      f" n°{student.number:4.4} {student.quiz}")
        if len(self._matched_students) != len(self._list_of_files):
            print("Unmatched file(s):")
            for quiz_path in unmatched_quiz:
                print(f" {quiz_path}")
            cancel = input("Do you want to continue? (y/n) ")
            if cancel.lower() == "n":
                quit("\nScript cancelled !")

    def connect_owncloud(self, address, username, password=None, SSO=False):
        """Prompt for a password, connect to Owncloud.

        Create an _cloud_client attribute.
        """
        if password is None:
            password = getpass.getpass("\nEnter Owncloud password: ")
        print("Connecting to Owncloud... ", end="")
        try:
            if SSO:
                self._connect_owncloud_behind_sso(address, username, password)
            else:
                self._cloud_client = owncloud.Client(address)
                self._cloud_client.login(username, password)
        except Exception as e:
            print(f"Error logging in!\n{e}")
            retry = input("Try again? (y/n) ")
            if retry.lower() == "y":
                self._cloud_client = self.connect_owncloud(address, username,
                                                           password=None)
            else:
                quit()
        print('Connected !')

    def _connect_owncloud_behind_sso(self, address, username, password):
        """Hack to connect to Owncloud behind a SSO (single sign on).

        Why does it work? https://github.com/owncloud/pyocclient/issues/204
        """
        # Get the hidden form fields needed to log in (CSRF token)
        s = requests.session()
        sso_address = s.get(address).url  # follow redirection
        login = s.get(sso_address)
        login_html = lxml.html.fromstring(login.text)
        hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
        form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}

        # Fill out the form with username and password
        form['username'] = username
        form['password'] = password
        response = s.post(sso_address, data=form)
        # print(response.url) # to check if it worked

        # Connect
        self._cloud_client = owncloud.Client(address)
        self._cloud_client._session = s
        self._cloud_client._update_capabilities()
        self._cloud_client._session = requests.session()
        self._cloud_client._session.verify = self._cloud_client._verify_certs
        self._cloud_client._session.auth = (username, password)

    def upload_and_share(self, folder_root="",
                         folder_name=" - Maths Quizzes",
                         quiz_name=None,
                         share_with_user=True,
                         share_by_link=True,
                         shorten_link=True,
                         replace_csv=False):
        """Create remote folders, upload files, share with user and/or by link.

        - Create remote folders for each students (if not already there):
        "/folder_root/Group/Surname - Name (Number) - folder_name/"
        - Upload quizzes named like this:
        "User input - Surname Name (Number).ext"
        - Share folders with the corresponding students (if not already done)
        - Share folders by link
        - Shorten link
        - Save links to .csv (if replace_csv=True)
        """
        if quiz_name is None:
            quiz_name = input('\nEnter quiz name: ')

        # For display
        students_total = len(self._matched_students)
        nb_digits = math.floor(math.log10(students_total)+1)
        students_current = 0
        print('\nUploading files...')

        # Create root folder if necessary
        try:
            self._cloud_client.mkdir(folder_root)
            print(f'Root folder created at "{folder_root}"')
        except:
            pass

        for student in self._matched_students:
            students_current += 1
            display_counter = (f"{students_current:0>{nb_digits}d}/"
                               f"{students_total}")

            # Create remote folder if necessary
            folder_group = folder_root + student.group + "/"
            folder_student = (folder_group +
                              student.surname + " " +
                              student.name +
                              " (" + student.number + ")" +
                              folder_name + "/")
            try:
                self._cloud_client.mkdir(folder_group)
                print(f'{display_counter} Folder created at "{folder_group}"')
            except:
                pass
            try:
                self._cloud_client.mkdir(folder_student)
                print(f'{display_counter} Folder created'
                      f' at "{folder_student}"')
            except:
                pass

            # Define remote quiz name et send
            remote_quiz_name = (quiz_name + ' - ' +
                                student.surname + ' ' +
                                student.name + ' (' + student.number + ')' +
                                '.' + student.quiz.split(".")[-1])  # extension
            remote_quiz_path = folder_student + remote_quiz_name
            try:
                self._cloud_client.put_file(remote_quiz_path, student.quiz)
                print(f'{display_counter} File sent to "{remote_quiz_path}"')
            except Exception as e:
                print(f"ERROR: File couldn't be sent"
                      f' to "{remote_quiz_path}"\n{e}')

            # Share folders with user if necessary
            is_shared = False
            for file_share in self._cloud_client.get_shares(folder_student):
                if file_share.get_share_with() == student.owncloud:
                    is_shared = True
                    break
            if (not is_shared) and (share_with_user):
                try:
                    if '@' in student.owncloud:  # remote user
                        self._cloud_client.share_file_with_user(
                                folder_student,
                                student.owncloud + '/',  # bug pyocclient 0.4
                                remote_user=True)
                    else:  # local user
                        self._cloud_client.share_file_with_user(
                                                            folder_student,
                                                            student.owncloud)
                    print(f"{display_counter} Folder"
                          f' shared with user "{student.owncloud}"')
                except Exception as e:
                    print(f"ERROR: Folder {folder_student} couldn't be"
                          f' shared with user "{student.owncloud}"\n{e}')

            # Share folder by link if necessary
            if (share_by_link):
                link_tmp = ""
                for file_share in self._cloud_client.get_shares(folder_student):
                    if (file_share.get_link() is not None):
                        link = file_share.get_link()
                        # no link yet ? Let's take an existing one
                        if student.link == "":
                            student.link = link
                            break
                        # existing link same as in csv, nothing to do
                        elif student.link == link:
                            break
                        # another link as in csv, let's keep it in case
                        else:
                            link_tmp = link
                # csv link not found ? Let's take an existing one if not empty
                else:
                    student.link = link_tmp
                # share by link if empty string
                if (not student.link):
                    share_obj = self._cloud_client.share_file_with_link(
                                                                folder_student)
                    student.link = share_obj.get_link()
                print(f"{display_counter} Folder"
                      f' shared by link "{student.link}"')

            # Shorten shared link if necessary and if it exists (max 5 tries)
            if (shorten_link) and (student.link):
                shortener = Shortener('Tinyurl')
                for attempt in range(5):
                    try:                  
                        student.shortlink = shortener.short(student.link)
                    except:
                        pass
                    else:
                        print(f"{display_counter} Shared link"
                              f' shortened as "{student.shortlink}"')
                        break
                else:
                    print(f"ERROR: Link couldn't be shortened")

        if share_by_link:
            self._write_links_to_csv(replace_csv=replace_csv)

    def _write_links_to_csv(self, replace_csv=False):
        # Get .csv file details from _csvfile attribute
        csv_filepath = self._csvfile["csv_filepath"]
        csv_delimiter = self._csvfile["csv_delimiter"]
        csv_comment = self._csvfile["csv_comment"]
        number_header = self._csvfile["number_header"]
        link_header = self._csvfile["link_header"]
        shortlink_header = self._csvfile["shortlink_header"]

        # New temporary .csv file path
        new_filename = (Path(csv_filepath).stem + "-" +
                        datetime.datetime.now().isoformat(timespec="minutes") +
                        ".csv")
        new_filepath = Path(csv_filepath).with_name(new_filename)
        # Save links to the new temporary .csv file
        with open(csv_filepath, 'r', newline="") as csv_in, \
             open(new_filepath, 'w', newline="") as csv_out:
            tab_in = csv.DictReader((row for row in csv_in
                                     if not row.startswith(csv_comment)),
                                    delimiter=csv_delimiter,
                                    quoting=csv.QUOTE_MINIMAL)
            # Remove empty fields in original file
            tab_in.fieldnames = [i for i in tab_in.fieldnames if i]
            # Add "link" header and "shortlink" header at the end (if not there)
            fieldnames = tab_in.fieldnames.copy()
            if link_header not in fieldnames:
                fieldnames.append(link_header)
            if shortlink_header not in fieldnames:
                fieldnames.append(shortlink_header)
            tab_out = csv.DictWriter(csv_out, fieldnames=fieldnames,
                                     delimiter=csv_delimiter,
                                     quoting=csv.QUOTE_MINIMAL)
            tab_out.writeheader()
            # Write file with link and shortlink if not present or different
            # TODO: comment line starting with a '#' are lost in the process
            for row in tab_in:
                link = self._dict_of_students[row[number_header]].link
                shortlink = self._dict_of_students[row[number_header]].shortlink
                if row.get(link_header) != link:
                    row[link_header] = link
                if row.get(shortlink_header) != shortlink:
                    row[shortlink_header] = shortlink
                # Hack... If 2 or more unamed fields (stored in key None):
                # temporarily create fieldnames to save them separately
                # (and avoid quoting)
                if isinstance(row.get(None), list):
                    # remove the last empty fields
                    while row[None] and (not (row[None])[-1]):
                        del (row[None])[-1]
                    # Create additional fields for unamed fields
                    additional_fields = {"_Add" + str(i): new_field
                                         for i, new_field
                                         in enumerate(row.get(None))}
                    row.update(additional_fields)
                    tab_out.fieldnames.extend(additional_fields.keys())
                    # Delete field None and save CSV row
                    del row[None]
                    tab_out.writerow(row)
                    # Remove additional fields and restore field None
                    for i in range(len(additional_fields)):
                        del tab_out.fieldnames[-1]
                else:
                    tab_out.writerow(row)

        # Replace the original .csv file if asked
        if replace_csv:
            shutil.move(new_filepath, csv_filepath)
            print(f'Shared links saved to current .csv file "{csv_filepath}"')
        else:
            print(f'Shared links saved to new .csv file "{new_filepath}"')

######### Script and parameters to tweak

CSV = '/path/to/csv/students.csv'
FOLDER = 'Quizzes/'
FOLDER_SUFFIX = ' - Maths'
ADDRESS = 'https://ncloud.zaclys.com'
USERNAME = 'MyUserName'

amcsend = AMCtoOwncloud()
amcsend.identify_students(csv_filepath=CSV)
amcsend.connect_owncloud(address=ADDRESS, username=USERNAME, SSO=False)
amcsend.upload_and_share(folder_root=FOLDER, folder_name=FOLDER_SUFFIX, replace_csv=False,
                         share_with_user=False, share_by_link=True, shorten_link=True)
