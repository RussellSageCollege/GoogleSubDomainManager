#! /usr/bin/env python

from __future__ import print_function
from httplib2 import Http
import yaml
import json
import os
from io import open
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import logging
import time


class RemoveAlias:
    SERVICE = []
    CONFIG = []
    SCOPES = [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.user.alias'
    ]
    DATE = ''
    ALIAS_STORE = []

    @staticmethod
    def get_config():
        """
        Reads our config file
        :return: object
        """
        with open('config.yml', 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    @staticmethod
    def read_aliases():
        """
        Reads aliases from the JSON file
        :return: object
        """
        if os.path.isfile('alias_store.json'):
            with open('alias_store.json', 'r') as json_data:
                return json.load(json_data)
        else:
            return []

    def sync_alias_store(self, index):
        """
        Syncs the alias store array and JSON file
        :param entry:
        :return:
        """
        self.ALIAS_STORE.pop(index)
        with open("alias_store.json", 'w', encoding="utf-8") as alias_store_file:
            alias_store_file.write(unicode(json.dumps(self.ALIAS_STORE, ensure_ascii=False)))

    def get_credentials(self):
        """
        Gets credentials from OAuth provider and impersonates the designated super admin.
        :return: object
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CONFIG['key_file_path'], self.SCOPES)
        return credentials.create_delegated(self.CONFIG['super_admin_email'])

    def build_service(self):
        """
        Builds a google directory service
        :return: object
        """
        credentials = self.get_credentials()
        http = credentials.authorize(Http())
        return discovery.build('admin', 'directory_v1', http=http)

    def execute_aliases_service_action(self, index, entry, aliases_service, log):
        """
        Insert a new alias for the target user. The alias will be the user's old address
        :param index:
        :param entry:
        :param aliases_service:
        :param log:
        :return: bool
        """

        member = entry['primary']
        alias = entry['alias']

        try:
            aliases_service.delete(userKey=member, alias=alias).execute()
            log.info('Removed: ' + alias + ' ---x ' + member)
            print('Removed: ' + alias + ' ---x ' + member)
            self.sync_alias_store(index)
            return True
        except Exception as e:
            log.error('failed removing alias ' + alias + ' ---x ' + member + str(e))
            print('failed removing alias ' + alias + ' ---x ' + member + str(e))
            return False

    def remove_alias(self):
        """
        Removes the alias from an email
        :return: void
        """
        # Set up logging
        info_log = self.CONFIG['log_path'] + '/info-' + self.DATE + '.log'
        error_log = self.CONFIG['log_path'] + '/error-' + self.DATE + '.log'
        logging.basicConfig(level=logging.INFO, filename=info_log, format='%(asctime)s %(message)s')
        logging.basicConfig(level=logging.ERROR, filename=error_log, format='%(asctime)s %(message)s')
        # Get a users service object from google:
        # https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.users.html
        users_service = self.SERVICE.users()
        # Get an aliases service object from google:
        # https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.users.aliases.html
        aliases_service = users_service.aliases()
        for index, entry in enumerate(self.ALIAS_STORE):
            self.execute_aliases_service_action(index, entry, aliases_service, logging)

    def main(self):
        """
        # Entry point function
        :return: void
        """
        # Get the current date
        self.DATE = time.strftime("%m-%d-%Y")
        print('Reading config...')
        # Read the configuration file
        self.CONFIG = self.get_config()
        # Read the alias store
        print('Reading alias store')
        self.ALIAS_STORE = self.read_aliases()
        print('Building service...')
        # Build the Google directory service
        self.SERVICE = self.build_service()
        self.remove_alias()


# Starts here, runs the main function
RemoveAlias().main()
