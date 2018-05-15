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
    SCOPES = [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.user.alias'
    ]
    DATE = ''

    def get_config(self):
        """
        Reads our config file
        :return: object
        """
        with open('config.yml', 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

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

    @staticmethod
    def execute_users_service_action(member, new_address, users_service, log):
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
            return True
        except Exception as e:
            log.error('fail ' + member + ' ' + str(e))
            return False

    @staticmethod
    def execute_aliases_service_action(member, new_address, aliases_service, log):
        """
        Insert a new alias for the target user. The alias will be the user's old address
        :param member:
        :param new_address:
        :param aliases_service:
        :param log:
        :return: bool
        """
        try:
            aliases_service.insert(userKey=new_address, body={'alias': member}).execute()
            log.info('Aliased: ' + member + ' ---> ' + new_address)
            return True
        except Exception as e:
            log.error('failed setting alias ' + member + ' ---> ' + new_address + str(e))
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
        # Get an aliases service object from google:
        # https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/admin_directory_v1.users.aliases.html
        aliases_service = users_service.aliases()
        # Iterate over each member
        for member in members:
            # form the new address
            new_address = self.form_new_address(member, mapping['destination'])
            # Move the address to the newly formed address
            user_action_result = self.execute_users_service_action(member, new_address, users_service, logging)
            # If the result was successful AND we want to create aliases for this sub-domain
            if user_action_result and mapping['alias_previous']:
                # Create an alias old_address --> new_address
                self.execute_aliases_service_action(member, new_address, aliases_service, logging)

    def main(self):
        """
        # Entry point function
        :return: void
        """
        # Get the current date
        self.DATE = time.strftime("%d-%m-%Y")
        print('Reading config...')
        # Read the configuration file
        self.CONFIG = self.get_config()
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
DomainManager().main()
