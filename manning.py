#!/bin/python3

"""
Date:    Tue Sep 15 12:30:33 UTC 2020
Author:  Lucian Maly
License: MIT
"""

import requests
from bs4 import BeautifulSoup
import datetime
import os
import errno
import sys
import getopt

loginURL = 'https://login.manning.com/login?service=https://www.manning.com/login/cas'
dashboardURL = 'https://www.manning.com/dashboard/index?filter=book&max=999&order=lastUpdated&sort=desc'


def main(argv):
    global username
    global password
    username = ''
    password = ''
    try:
        opts, args = getopt.getopt(argv, "hu:p:", ["username=", "password="])
    except getopt.GetoptError:
        print('Usage: `manning.py -u <email> -p <password>`')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: `manning.py -u <email> -p <password>`')
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        else:
            print('Help: `manning.py -h`')
            sys.exit()


def create_folder():
    global folder
    datetime_object = datetime.date.today()
    folder = 'Manning_' + str(datetime_object)
    try:
        os.mkdir(folder)
        print('Created folder', folder)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print(f'Directory {folder} already exists.')
        else:
            raise


def get_list():
    with requests.Session() as s:
        # PURPOSE: Get the value of LT
        soup0 = BeautifulSoup(s.get(loginURL).text, 'html.parser')
        headers = {
            'Origin': 'https://login.manning.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        }
        data = {
            'username': username,
            'password': password,
            'lt': soup0.find('input', {'name': 'lt'}).get('value'),
            'execution': 'e1s1',
            '_eventId': 'submit',
            'submit': ''
        }
        # PURPOSE: Log in
        s.post(loginURL, cookies=s.cookies, headers=headers, data=data)
        dashboard = s.get(dashboardURL)
        # PURPOSE: Parse the dashboard with up to 999 products
        soup = BeautifulSoup(dashboard.text, 'html.parser')
        div_container = soup.find('table', {'id': 'productTable'})
        for product in div_container.find_all('tr', {'class': 'license-row'}):
            try:
                # EXAMPLE: Terraform in Action
                title = str(product.find(
                    'div', {'class': 'product-title'}).text.strip())
                # EXAMPLE: winkler
                author = str(product.find(
                    'form', {'class': 'download-form'})['name']).split('-')[1]
                restrictedDownloadIds = author + '-restrictedDownloadIds'
                download_payload = [
                    ('dropbox', 'false'),
                    ('productExternalId', author)
                ]
                # PURPOSE: Find all the restrictedDownloadIds and create a complete payload
                for downloadSelection in product.find_all('div', {'class': 'download-selection'}):
                    hidden = downloadSelection.find_all(
                        'input', {'type': 'hidden'})
                    for val in hidden:
                        checkbox1 = (val['id'], val['value'])
                        checkbox2 = (restrictedDownloadIds, val['id'])
                        download_payload.append(checkbox1)
                        download_payload.append(checkbox2)
                        # EXAMPLE: [('dropbox', 'false'), ('productExternalId', 'winkler'), ('1971', '7850702'), ('winkler-restrictedDownloadIds', '1971'), ('1972', '7850703'), ('winkler-restrictedDownloadIds', '1972'), ('1973', '7850704'), ('winkler-restrictedDownloadIds', '1973')]
                try:
                    subfolder = str(title.replace(' ', '_'))
                    path = os.path.join(folder, subfolder)
                    os.makedirs(path)
                    print('Created folder', path)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        print(f'Directory {path} already exists.')
                    else:
                        raise
                downloadURL = 'https://www.manning.com/dashboard/download?id=downloadForm-' + author
                print('Downloading', title, '...')
                dl = s.post(downloadURL, cookies=s.cookies,
                            headers=headers, data=download_payload)
                # PURPOSE: Some free titles are only in PDF format, this can be determined from the amount of hidden inputs
                if len(download_payload) <= 4:
                    extension = '.pdf'
                else:
                    extension = '.zip'
                filename = path + '/' + subfolder + extension
                file = open(filename, "wb")
                file.write(dl.content)
                file.close()
            except TypeError:
                pass


def end_script():
    print('Exiting the script...')
    sys.exit()


if len(sys.argv) > 1:
    main(sys.argv[1:])
    create_folder()
    get_list()
    end_script()
else:
    print('Help: `manning.py -h`')
    sys.exit()
