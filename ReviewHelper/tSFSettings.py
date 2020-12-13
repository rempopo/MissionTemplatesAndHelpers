import os
import re


class tSFSettings:
    """
        Gather tSF settings info and provide API for accessing them and other tSF-related stuff
    """

    SHORTCUT = "_tsf_"

    def __init__(self, config, target_dir):
        self.cfg = config
        self.section = "tSF_config"
        self.modulesPath = self.get("path")

        pattern = self.get_re("pattern")
        filepath = os.path.join(target_dir, self.get("config"))
        self.modules = self.read_tsf_settings(filepath, pattern)

    def get(self, key):
        return self.cfg.get((self.section, key))

    def get_re(self, key):
        return self.cfg.get_regexp((self.section, key))

    def get_module_from_path(self, path):
        # Extract module name from given piece of path in format "_tSF_\IntroText\Settings.sqf"
        path = self.strip_shortcut(path)
        return os.path.split(path)[0]

    def is_module_active(self, module_name):
        # Returns: True if tSf module is activated in tSF init
        return self.modules.get(module_name.lower(), False);

    def read_tsf_settings(self, file, pattern):
        # Parse given file and compose dict of module settings
        # Returns: Dict of modules state (BOOLS) or {} if file not found
        settings = {}
        if not os.path.isfile(file):
            return settings

        with open(file, "r") as tSFFile:
            for line in tSFFile:
                r = re.search(pattern, line, re.I)
                if r:
                    settings[r[1].lower()] = r[2].lower() == 'true'

        return settings

    def check_is_shortcut(self, filename):
        # Checks for tsf shortcut in the path
        return filename[0:len(self.SHORTCUT)].lower() == self.SHORTCUT

    def strip_shortcut(self, filename):
        # Removes tsf shortcut from the path
        return filename[len(self.SHORTCUT) + 1:]

    def get_file(self, filename):
        # Returns full path to file including tSF dir + module\file
        if self.check_is_shortcut(filename):
            filename = self.strip_shortcut(filename)

        return os.path.join(self.modulesPath, filename)
