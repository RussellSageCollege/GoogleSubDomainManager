from __future__ import print_function
import logging


class Logger(object):
    def __init__(self, path):
        self.log_path = path
        debug_log = self.log_path + '/debug.log'
        info_log = self.log_path + '/info.log'
        error_log = self.log_path + '/error.log'
        warn_log = self.log_path + '/warning.log'
        logging.basicConfig(level=logging.DEBUG, filename=debug_log, format='%(asctime)s %(message)s')
        logging.basicConfig(level=logging.INFO, filename=info_log, format='%(asctime)s %(message)s')
        logging.basicConfig(level=logging.ERROR, filename=error_log, format='%(asctime)s %(message)s')
        logging.basicConfig(level=logging.WARNING, filename=warn_log, format='%(asctime)s %(message)s')
        self.log = logging

    def log_debug(self, message, tag, print_out=True):
        """
        :param message: str
        :param tag: str
        :param print_out: bool
        :return:
        """
        if print_out:
            print('[DEBUG][' + tag + '] ' + message)
        self.log.debug(message)

    def log_info(self, message, tag, print_out=True):
        """
        :param message: str
        :param tag: str
        :param print_out: bool
        :return:
        """
        if print_out:
            print('[INFO][' + tag + '] ' + message)
        self.log.info(message)

    def log_warn(self, message, tag, print_out=True):
        """
        :param message: str
        :param tag: str
        :param print_out: bool
        :return:
        """
        if print_out:
            print('[WARN][' + tag + '] ' + message)
        self.log.error(message)

    def log_error(self, message, tag, print_out=True):
        """
        :param message: str
        :param tag: str
        :param print_out: bool
        :return:
        """
        if print_out:
            print('[ERROR][' + tag + '] ' + message)
        self.log.error(message)
