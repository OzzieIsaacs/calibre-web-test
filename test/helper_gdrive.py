from google.oauth2.credentials import Credentials
from fs.googledrivefs import GoogleDriveFS
from fs.osfs import OSFS
from fs.copy import copy_fs
from fs.errors import ResourceNotFound

import json
import os
from config_test import base_path, TEST_DB

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
    credentials = get_credentials()
    fs = GoogleDriveFS(credentials=credentials)
    try:
        test = fs.getinfo('test')
        fs.removetree('test')
    except ResourceNotFound:
        # old path not found on googledrive
        pass

    # copy database from local to gdrive
    test = fs.makedir('test')
    #fs.makedir('test')
    #info = fs.getinfo('test')
    #root_id = info.raw['sharing']['id']
    copy_fs(OSFS('./Calibre_db'), test) # GoogleDriveFS(credentials=get_credentials(), rootId=root_id))
    # fs.removedir('/test/New Folder')
    fs.close()


def remove_gdrive():
    pass
    #fs = _remove_gdrive()
    #fs.close()

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

# prepare_gdrive()