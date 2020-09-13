#!/bin/python3

"""
Date:   Sun Sep 13 10:48:32 UTC 2020
Author: Lucian Maly
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
        soup1 = BeautifulSoup(s.get(loginURL).text, 'html.parser')
        headers = {
            'Origin': 'https://login.manning.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        }
        data = {
            'username': username,
            'password': password,
            'lt': soup1.find('input', {'name': 'lt'}).get('value'),
            'execution': 'e1s1',
            '_eventId': 'submit',
            'submit': ''
        }
        s.post(loginURL, cookies=s.cookies, headers=headers, data=data)
        dashboard = s.get(dashboardURL)
        soup2 = BeautifulSoup(dashboard.text, 'html.parser')
        div_container = soup2.find('table', {'id': 'productTable'})
        for product in div_container.find_all('tr', {'class': 'license-row'}):
            try:
                # example: Understanding API Security
                title = str(product.find(
                    'div', {'class': 'product-title'}).text.strip())
                # example: richer2
                user = str(product.find(
                    'form', {'class': 'download-form'})['name']).split('-')[1]
                # example: richer2-restrictedDownloadIds
                checkbox = str(user + '-restrictedDownloadIds')
                # example: 1607
                pdf_id = product.find('input', {'name': checkbox})['value']
                # example: 4539985
                pdf_value = product.find('input', {'id': pdf_id})['value']
                # example: 1608
                epub_id = str(int(pdf_id) + 1)
                # example: 4539986
                epub_value = str(int(pdf_value) + 1)
                # example: 1609
                kindle_id = str(int(pdf_id) + 2)
                # example: 4539987
                kindle_value = str(int(pdf_value) + 2)
                download_payload = [
                    ('dropbox', 'false'),
                    (checkbox, pdf_id),
                    (pdf_id, pdf_value),
                    (checkbox, epub_id),
                    (epub_id, epub_value),
                    (checkbox, kindle_id),
                    (kindle_id, kindle_value),
                    ('productExternalId', user)
                ]
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
                downloadURL = 'https://www.manning.com/dashboard/download?id=downloadForm-' + user
                dl = s.post(downloadURL, cookies=s.cookies,
                            headers=headers, data=download_payload)
                filename = path + '/' + subfolder + '.zip'
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
