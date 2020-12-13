import os
import yaml


def strip_re(expression):
    return expression.strip('/')


class ConfigReader:
    def __init__(self, file):
        self.cfg = self.read_config(file)

    def read_config(self, filename):
        # Check that config file exists and reads it data to dictionary
        # Returns: Dictionary or stops execution if none found
        if not os.path.isfile(filename):
            raise FileNotFoundError()

        try:
            with open(filename, "r") as yamlfile:
                cfg = yaml.load(yamlfile, Loader=yaml.BaseLoader)
                return cfg
        except:
            raise ValueError("Could not read config file! File is malformed!") from None

    def get_by_key(self, key):
        if isinstance(key, str):
            if key in self.cfg:
                return self.cfg.get(key)
            raise ValueError("Key [{}] not found!".format(key))
        elif isinstance(key, tuple):
            value = None
            for k in key:
                if not value:
                    cfg = self.cfg
                else:
                    cfg = value

                if k in cfg:
                    value = cfg.get(k)
                else:
                    raise ValueError("Key [{}] not found!".format(key))
            return value
        else:
            raise ValueError("Key format [{}] is not supported!".format(type(key)))

    def get(self, key):
        return self.get_by_key(key)

    def get_regexp(self, key):
        # Get value by key and strip regex from escape symbols
        return strip_re(self.get_by_key(key))
