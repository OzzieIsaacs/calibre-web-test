from google.oauth2.credentials import Credentials
from fs.googledrivefs import GoogleDriveFS
from fs.osfs import OSFS
from fs.copy import copy_fs
from fs.errors import ResourceNotFound

import json
import os
import time
from config_test import base_path
import re


def get_credentials():
    with open(os.path.join(base_path, 'files', 'gdrive_credentials'), 'r') as f:
        fs_content = f.read()
    tokens = json.loads(fs_content)

    return Credentials(tokens['access_token'],
                       refresh_token=tokens['refresh_token'],
                       token_uri="https://www.googleapis.com/oauth2/v4/token",
                       client_id=tokens['client_id'],
                       client_secret=tokens['client_secret'])


def prepare_gdrive():
    print("Preparing GDrive")
    credentials = get_credentials()
    fs = GoogleDriveFS(credentials=credentials)
    try:
        test = fs.getinfo('test')
        fs.removetree('test')
        time.sleep(5)
    except ResourceNotFound:
        # old path not found on googledrive
        pass
    except RuntimeError as e:
        id = re.search(".*with id (.*) has more.*", str(e))[1]
        for ele in fs._childrenById(id):
            fs.google_resource().files().delete(fileId=ele['id']).execute()
        fs.removetree('test')

    # copy database from local to gdrive
    test = fs.makedir('test')
    copy_fs(OSFS(os.path.join(base_path, 'Calibre_db')), test)
    fs.close()


def remove_gdrive():
    pass


def connect_gdrive(path):
    credentials = get_credentials()
    fs = GoogleDriveFS(credentials=credentials)
    if check_path_gdrive(fs, path):
        return fs
    else:
        fs.close()
        return False


def check_path_gdrive(fs, path):
    try:
        return fs.isdir(path)
    except ResourceNotFound:
        return False


def _remove_gdrive():
    # delete old path on gdrive if applicable
    credentials = get_credentials()
    fs = GoogleDriveFS(credentials=credentials)
    try:
        test = fs.getinfo('test')
        edi = fs.removetree('test')
    except ResourceNotFound:
        # old path not found on googledrive
        pass
    return fs
