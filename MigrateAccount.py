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


class MigrateAccount:
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

    def sync_alias_store(self, entry):
        """
        Syncs the alias store array and JSON file
        :param entry:
        :return:
        """
        self.ALIAS_STORE.append(entry)
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

    @staticmethod
    def form_new_address(member, destination):
        """
        Forms the new email address from the old one and the new sub domain
        :param member:
        :param destination:
        :return: string
        """
        return member.split('@')[0] + '@' + destination

    @staticmethod
    def get_members_from_local(mapping):
        """
        Get users from local file
        :param mapping:
        :return: array
        """
        return [line.rstrip('\n').strip('"').lower() for line in open(mapping['members'])]

    def execute_users_service_action(self, member, new_address, users_service, log):
        """
        Patch the user's google account by setting their primary email to the new address
        :param member:
        :param new_address:
        :param users_service:
        :param log:
        :return: bool
        """
        try:
            users_service.patch(userKey=member, body={'primaryEmail': new_address}).execute()

            log.info('Moved: ' + member + ' ---> ' + new_address)
            print('Moved: ' + member + ' ---> ' + new_address)
            self.sync_alias_store({'primary': new_address, 'alias': member, 'date': self.DATE})
            return True
        except Exception as e:
            log.error('fail ' + member + ' ' + str(e))
            print('fail ' + member + ' ' + str(e))
            return False

    def set_new_addresses(self, members, mapping):
        """
        Sets the new address for a list of users, may also create an alias of the old address to the new address
        :param members:
        :param mapping:
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
        for member in members:
            # form the new address
            new_address = self.form_new_address(member, mapping['destination'])
            # Move the address to the newly formed address
            self.execute_users_service_action(member, new_address, users_service, logging)

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
        # For each domain mapping
        for mapping in self.CONFIG['domain_source_map']:
            print('Gathering list of desired members from: \n - ' + mapping['members'] + '...')
            # Read the members from the local flat file
            members = self.get_members_from_local(mapping)
            # Set the new addresses for those users
            self.set_new_addresses(members, mapping)


# Starts here, runs the main function
MigrateAccount().main()
