import json
import os
import io


class AliasStore(object):
    def __init__(self, path):
        self.path = path
        self.store = self.read()

    def read(self):
        """
        Reads aliases from the JSON file
        :return: object
        """
        if os.path.isfile(self.path):
            with open(self.path, 'r') as json_data:
                data = json.load(json_data)
                self.store = data
                return data
        else:
            self.store = []
            return []

    def append_entry(self, entry):
        """
        Syncs the alias alias_store array and JSON file after appending an entry
        :param entry: str
        :return:
        """
        self.store.append(entry)
        with io.open(self.path, 'w', encoding="utf-8") as alias_store_file:
            alias_store_file.write(unicode(json.dumps(self.store, ensure_ascii=False)))

    def pop_entry(self, index):
        """
        Syncs the alias alias_store array and JSON file by removing the index passed in from the ALIAS_STORE array and then writes the new contents as a JSON file.
        :param index: int
        :return:
        """
        self.store.pop(index)
        with io.open(self.path, 'w', encoding="utf-8") as alias_store_file:
            alias_store_file.write(unicode(json.dumps(self.store, ensure_ascii=False)))
