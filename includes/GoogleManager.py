from __future__ import print_function
from httplib2 import Http
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from helpers import get_scopes


class GoogleManager(object):
    log_tag = 'GOOGLE'

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.scopes = get_scopes()
        self.credentials = self.get_credentials()
        self.service = self.build_service()
        self.user_service = self.service.users()
        self.alias_service = self.user_service.aliases()

    def get_credentials(self):
        """
        Gets credentials from OAuth provider and impersonates the designated super admin.
        :return: object
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.config['key_file_path'], self.scopes)
        return credentials.create_delegated(self.config['super_admin_email'])

    def build_service(self):
        """
        Builds a google directory service
        :return: object
        """
        http = self.credentials.authorize(Http())
        return discovery.build('admin', 'directory_v1', http=http)

    def move_account(self, member, new_address, org_unit_path, include_in_global_address_list):
        """
        :param member: str
        :param new_address: str
        :param org_unit_path: str
        :param include_in_global_address_list: bool
        :return: dict|bool
        """
        try:
            # Get the user's current state
            old_user = self.user_service.get(userKey=member).execute()
            old_org = old_user['orgUnitPath']
            # If there is an org unit path use it
            if org_unit_path:
                body = {
                    'primaryEmail': new_address,
                    'orgUnitPath': org_unit_path,
                    'includeInGlobalAddressList': include_in_global_address_list
                }
            else:
                body = {
                    'primaryEmail': new_address,
                    'includeInGlobalAddressList': include_in_global_address_list
                }
            # Patch the user's account and change their email and their org unit
            self.user_service.patch(
                userKey=member,
                body=body
            ).execute()
            # Get the user's state after modification
            new_user = self.user_service.get(userKey=new_address).execute()
            # Build a string to log
            message = 'Account moved ' + old_org + '/' + member + ' ---> ' + org_unit_path + '/' + new_address
            # Log it
            self.logger.log_info(message, self.log_tag)
            # Return the old user state and the current user state
            return {
                'previous': old_user,
                'current': new_user
            }
        except Exception as e:
            self.logger.log_error('Account move failure ' + member + ' ' + str(e), self.log_tag)
            return False

    def remove_alias(self, member, alias):
        """
        :param member: str
        :param alias: str
        :return: bool
        """
        try:
            self.alias_service.delete(userKey=member, alias=alias).execute()
            self.logger.log_info('Removed alias from account ' + alias + ' X ' + member, self.log_tag)
            return True
        except Exception as e:
            self.logger.log_error('Alias removal failure ' + alias + ' X ' + member + ' ' + str(e), self.log_tag)
            return False
