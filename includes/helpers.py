from __future__ import print_function
import time
import yaml


def read_config():
    """
    Reads our config file
    :return: dict
    """
    with open('config.yml', 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def get_scopes():
    """
    returns Google OAuth Scopes
    :return: list
    """
    return [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.user.alias'
    ]


def form_new_address(member, destination):
    """
    Forms the new email address from the old one and the new sub domain
    :param member: str
    :param destination: str
    :return: str
    """
    return member.split('@')[0] + '@' + destination


def get_members_from_input_file(member_file_path):
    """
    Get users from local file
    :param member_file_path: str
    :return: list
    """
    return [line.rstrip('\n').strip('"').lower() for line in open(member_file_path)]


def get_date():
    """
    Returns the current date
    :return: str
    """
    return time.strftime("%d-%m-%Y")
