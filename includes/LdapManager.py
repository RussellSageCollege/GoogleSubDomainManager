import ldap


class LdapManager(object):
    log_tag = 'LDAP'

    def __init__(self, config, logger):
        self.logger = logger
        self.tree_base = config['tree_base']
        self.connection = self.connect(config['bind_user']['principal_name'], config['bind_user']['password'],
                                       config['servers'])

    def connect(self, bind_user, bind_pass, hosts):
        connection = False
        for host in hosts:
            try:
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
                ldap.set_option(ldap.OPT_REFERRALS, 0)
                ldap.protocol_version = ldap.VERSION3
                if host['ldaps']:
                    connection = ldap.initialize('ldaps://' + host['host_or_ip'] + ':' + str(host['port']))
                else:
                    connection = ldap.initialize('ldap://' + host['host_or_ip'] + ':' + str(host['port']))
                connection.simple_bind_s(bind_user, bind_pass)
                if connection:
                    return connection
            except ldap.LDAPError, error_message:
                self.logger.log_error(
                    'Error connecting to LDAP server: ' + host['host_or_ip'] + ' -- ' + str(error_message),
                    self.log_tag
                )
        return connection

    def __perform_search(self, ldap_filter, attributes):
        try:
            results = self.connection.search_s(
                str(self.tree_base).strip(' \t\n\r'),
                ldap.SCOPE_SUBTREE,
                ldap_filter,
                attributes
            )
            if not results[0][0]:
                return False
            else:
                return results
        except ldap.LDAPError, error_message:
            self.logger.log_error('Error performing LDAP search: ' + ' -- ' + str(error_message), self.log_tag)
            return False

    def modify_object(self, dn, action):
        try:
            return self.connection.modify_s(dn, action)
        except ldap.LDAPError, error_message:
            self.logger.log_error('Error performing LDAP modify: ' + ' -- ' + str(error_message), self.log_tag)
            return False

    @staticmethod
    def form_set_account_control_action(account_control):
        return [(ldap.MOD_REPLACE, 'userAccountControl', str(account_control))]

    def __get_user(self, ldap_filter):
        attributes = ['objectGUID', 'cn', 'samAccountName', 'employeeID', 'distinguishedName', 'description',
                      'displayName',
                      'extensionName', 'givenName', 'homeDirectory', 'homeDrive', 'mail', 'middleName', 'name',
                      'objectCategory', 'objectClass', 'primaryGroupID', 'sAMAccountName', 'sAMAccountType', 'sn',
                      'initials', 'userAccountControl', 'userPrincipalName', ]
        return self.__perform_search(ldap_filter, attributes)

    def get_user(self, email, ):
        ldap_filter = '(&(objectClass=top)(objectClass=person)(objectClass=user)(userPrincipalName=' + email + '))'
        return self.__get_user(ldap_filter)

    def disable_account(self, dn):
        disable_account_action = self.form_set_account_control_action('514')
        result = self.modify_object(dn, disable_account_action)
        if result:
            self.logger.log_error('LDAP account disabled.', self.log_tag)
            return result
        else:
            self.logger.log_error('Error performing LDAP disable account.', self.log_tag)
            return False

    def move_user(self, email, ldap_org_dn, ldap_disable_accounts=False):
        if ldap_org_dn:
            user = self.get_user(email)
            if user:
                cn = user[0][1]['cn'][0]
                dn = user[0][0]
                new_dn = 'cn=' + cn + ',' + ldap_org_dn
                if ldap_disable_accounts:
                    self.connection.rename_s(dn, 'cn=' + cn, ldap_org_dn)
                    self.logger.log_error('LDAP account moved to: ' + ldap_org_dn, self.log_tag)
                    self.disable_account(new_dn)
                else:
                    self.logger.log_error('LDAP account moved to: ' + ldap_org_dn, self.log_tag)
                    self.connection.rename_s(dn, 'cn=' + cn, ldap_org_dn)
                return {'current': new_dn, 'previous': dn}
            else:
                self.logger.log_error('Error performing LDAP user move.', self.log_tag)
                return False
        else:
            return True
