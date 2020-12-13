import os
import re
from ConfigReader import strip_re


class GearSettings:
    def __init__(self, config, target_dir):
        self.cfg = config
        self.section = "dzn_Gear"
        self.tgt_dir = target_dir

        filepath = os.path.join(target_dir, self.get("kits_file"))
        pattern = self.get_re("kitname_pattern")
        self.kits = self.read_kits(filepath, pattern)

    def read_kits(self, file, pattern):
        # Returns: Set of kitnames (STRINGs) or {} if file not found
        kits = set()
        if not os.path.isfile(file):
            return kits

        with open(file, 'r') as f:
            for line in f:
                r = re.search(pattern, line, re.I)
                if r:
                    kits.add(r[0].lower())

        print("Found {} kits:".format(len(kits)))
        print(kits)

        return kits

    def get(self, key):
        return self.cfg.get((self.section, key))

    def get_re(self, key):
        return self.cfg.get_regexp((self.section, key))

    def get_gat(self):
        # Getter for GAT file path
        return self.get("gat_file")

    def get_checklist(self):
        # Getter for checklist
        return self.get("checklist")

    def check_kit_exists(self, kitname):
        # Checks that given kitname exists
        # Return True if exists
        return kitname.lower() in self.kits

    def get_gat_kits(self, file):
        # Return list of kits mentioned in GAT
        kits = set()
        pattern = self.get_re("gat_table_pattern")
        with open(file, 'r') as f:
            for line in f:
                r = re.search(pattern, line, re.I)
                if r:
                    name = r[2].lower()
                    if name[0] != "@":
                        kits.add(r[2].lower())

        return kits

    def check_kit_in_file(self, file, pattern):
        # Open file
        # Find pattern match
        # Check kit exists
        # Return dict in form of: {"kitname": STRING, "isValid": BOOL}

        kits_found = list()
        if not pattern:
            pattern = self.get_re("kitname_pattern")
        else:
            pattern = strip_re(pattern)

        print("> Pattern: " + pattern)

        with open(file,'r') as f:
            for line in f:
                r = re.search(pattern, line, re.I)
                if r:
                    print("Something found")
                    print(r)

                    name = r[1].lower()
                    if not name:
                        continue
                    is_valid = self.check_kit_exists(name)
                    kits_found.append({"name": name, "valid": is_valid})

        return kits_found

