#! /usr/bin/env python

from __future__ import print_function
from httplib2 import Http
import yaml
from io import open
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import logging
import time


class DomainManager:
    SERVICE = []
    CONFIG = []
    SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']
    MEMBERS_TO_ADD = []
    SOURCE_FILE = ''
    TARGET_DOMAIN = ''
    DATE = ''

    # Reads our config file
    def get_config(self):
        with open('config.yml', 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    # Gets credentials from OAuth provider and impersonates the designated super admin.
    def get_credentials(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CONFIG['key_file_path'], self.SCOPES)
        return credentials.create_delegated(self.CONFIG['super_admin_email'])

    # Builds a google directory service
    def build_service(self):
        credentials = self.get_credentials()
        http = credentials.authorize(Http())
        return discovery.build('admin', 'directory_v1', http=http)

    # Get users from local file
    def get_members_from_local(self):
        self.MEMBERS_TO_ADD = [line.rstrip('\n').strip('"').lower() for line in open(self.SOURCE_FILE)]

    def set_new_addresses(self):
        info_log = self.CONFIG['log_path'] + '/info-' + self.DATE + '.log'
        error_log = self.CONFIG['log_path'] + '/error-' + self.DATE + '.log'
        logging.basicConfig(level=logging.INFO, filename=info_log, format='%(asctime)s %(message)s')
        logging.basicConfig(level=logging.ERROR, filename=error_log, format='%(asctime)s %(message)s')
        users = self.SERVICE.users()
        for member in self.MEMBERS_TO_ADD:
            new_address = member.split('@')[0] + '@' + self.TARGET_DOMAIN
            try:
                users.patch(userKey=member, body={'primaryEmail': new_address}).execute()
                logging.info(member + ' ---> ' + new_address)
            except Exception as e:
                logging.error('fail ' + member + ' ' + str(e))

    def main(self):
        self.DATE = time.strftime("%d-%m-%Y")
        print('Reading config...')
        self.CONFIG = self.get_config()
        print('Building service...')
        self.SERVICE = self.build_service()
        for mapping in self.CONFIG['domain_source_map']:
            self.SOURCE_FILE = mapping['members']
            self.TARGET_DOMAIN = mapping['destination']
            print('Gathering list of desired members from: \n - ' + self.SOURCE_FILE + '...')
            self.get_members_from_local()
            self.set_new_addresses()
            self.MEMBERS_TO_ADD = []
            self.SOURCE_FILE = ''
            self.TARGET_DOMAIN = ''


DomainManager().main()
