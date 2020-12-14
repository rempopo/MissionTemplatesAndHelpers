# -------------------------
# tSF Review Helper v0.2
# -------------------------

from zipfile import ZipFile
import os
import shutil
import re
import requests
import sys
import filecmp
import time
import yaml



class Reporter:
    """
        Logs execution details and writes Review file with valuable data
    """

    def __init__(self):
        self.verbose = True
        self.config = None
        self.reviewLogFile = None
        self.msg_prefix = ""
        self.logFile = "log.log"
        self.log("START", "--------------------------------", "w+")

    def setup(self, config):
        self.config = config
        self.reviewLogFile = "Review.log"
        self.write_review("-------- Review started ------", "w+")

    def set_msg_prefix(self, prefix):
        self.msg_prefix = " " + prefix

    def write_review(self, message, mode="a"):
        try:
            with open(self.reviewLogFile, mode) as f:
                f.write(message + "\n")
                f.close()
        except:
            self.fatal("Error happened during log writing!")

    def log(self, msg_type, message, mode="a"):
        try:
            with open(self.logFile, mode) as f:
                msg = "{} [{}]{} {}\n".format(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    msg_type,
                    self.msg_prefix,
                    message
                )
                print(msg)
                f.write(msg)
                f.close()
        except:
            print("Error happened during log writing!")

    def info(self, message):
        self.log("INFO", message)

    def warn(self, message):
        self.log("WARN", message)

    def error(self, message):
        self.log("ERROR", message)

    def fatal(self, message):
        self.log("FATAL ERROR", message)

    def format_review_msg(self, type, code, arg1="", arg2="", arg3="", arg4=""):
        return "[{}] {}".format(type, self.config.get(type.lower() + str(code)).format(arg1, arg2, arg3, arg4))

    def review_info(self, code, arg1="", arg2="", arg3="", arg4=""):
        if not self.verbose:
            return ()
        self.write_review(self.format_review_msg("INFO", code, arg1, arg2, arg3, arg4))

    def review_warn(self, code, arg1="", arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("WRN", code, arg1, arg2, arg3, arg4))

    def review_error(self, code, arg1="", arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("ERR", code, arg1, arg2, arg3, arg4))




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




class Downloader:
    """
        Downloads mission archive from GitHub website, unzips and rename folder (removing branch suffix)
    """

    BRANCH_MAIN = "main"
    BRANCH_MASTER = "master"
    URL_FORMAT = "{}/archive/{}.zip"

    def __init__(self, reporter):
        self.reporter = reporter

    def download(self, url):
        # Validates URL (is reachable) and downloads mission, unzip it
        # Returns: Created mission folder name (STRING)

        self.reporter.info("Downloading mission: " + url)

        file_url = self.get_file_url(url)
        if not file_url:
            return ""

        zip_request = requests.get(file_url, allow_redirects=True)
        file_name_parts = file_url.rsplit('/', 3)
        filename = "{}-{}".format(file_name_parts[1], file_name_parts[3])

        if os.path.isfile(filename):
            os.remove(filename)

        with open(filename, "wb") as file:
            file.write(zip_request.content)
            file.close()

        self.reporter.info("Mission repo downloaded, unzipping.")
        self.unzip(filename)
        dir_name = self.rename_folder(filename)
        self.reporter.info("Mission repo unpacked.")

        return dir_name

    def get_file_url(self, repo_url):
        # Tries to get mission archive URL, as it may have -main or -master suffix - check both and return valid one
        # Returns: Reachable URL of empty string (STRING)
        url = self.URL_FORMAT.format(repo_url, self.BRANCH_MAIN)
        if self.validate_repo(url):
            return url

        url = self.URL_FORMAT.format(repo_url, self.BRANCH_MASTER)
        if self.validate_repo(url):
            return url

        return ""

    def validate_repo(self, url):
        # Checks that given URL is reachable
        request = requests.get(url)
        return request.status_code == 200

    def unzip(self, filename):
        # Unzips given archive
        try:
            with ZipFile(filename, "r") as file:
                file.extractall()
            os.remove(filename)
        except:
            self.reporter.fatal("Unzipping failed!")

    def rename_folder(self, filename):
        # Rename unzipped folder and remove branch suffix (main or master)
        # Returns: new folder name (STRING)

        old_name = filename.rstrip(".zip")
        new_name = (old_name.split("-{}".format(self.BRANCH_MAIN))[0]).split("-{}".format(self.BRANCH_MASTER))[0]
        if os.path.isdir(new_name):
            shutil.rmtree(new_name)

        os.rename(old_name, new_name)

        return new_name




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






class Reviewer:
    USE_TEST_MISSION = False

    def __init__(self):
        self.reporter = Reporter()
        self.comparator = Comparator()

        self.configName = "config.yaml"
        self.cfg = None
        self.target_dir = None
        self.review_dir = None
        self.ref_dir = None
        self.tSF = None
        self.Gear = None

    def prepare(self):
        # Read config, validate target and reference directories
        self.reporter.info("---------- App Started ----------")
        self.reporter.info("Initializiation")

        self.cfg = self.read_config(self.configName)
        self.reporter.setup(self.cfg.get("Reporter"))
        self.reporter.info("Config read successfully")

        self.ref_dir = self.cfg.get("reference_path")
        if not self.ref_dir or not os.path.isdir(self.ref_dir):
            self.fatal_and_exit("Error: Could not find reference directory!")

        if Reviewer.USE_TEST_MISSION:
            self.target_dir = self.cfg.get("test_path")
        else:
            self.target_dir = self.get_mission_dir()

        self.review_dir = self.create_review_dir(self.cfg.get("review_directory_name"))

        self.reporter.info("| Reference | " + self.ref_dir)
        self.reporter.info("| Revivewed | " + self.target_dir)
        self.reporter.info("| Review to | " + self.review_dir)

        self.tSF = tSFSettings(self.cfg, self.target_dir)
        if not self.tSF.modules:
            self.fatal_and_exit("Error: Could not find valid dzn_tSFramework_Init.sqf in reviewed mission!")

        self.Gear = GearSettings(self.cfg, self.target_dir)
        if not self.Gear.kits:
            self.reporter.warn("Error: Could not find any dzn_Gear kit!")

        self.reporter.info("Initialized")

    def review(self, list_name):
        # Validates files from Checklist
        self.reporter.set_msg_prefix("(Review)")
        self.reporter.info("Review started for {}".format(list_name))
        checklist = self.cfg.get(("Checklist", list_name))
        is_tsf_modules = list_name == "tSF_modules"

        for fileInfo in checklist:
            filename = fileInfo.get("file", "")
            alert_identical = fileInfo.get("alert", False)

            self.reporter.info("Reviewing file {}".format(filename))

            module_active = False
            if is_tsf_modules:
                # Ensures that not changed files in inactive modules won't be reported
                module = self.tSF.get_module_from_path(filename)
                module_active = self.tSF.is_module_active(module)
                alert_identical = alert_identical and module_active

            path = self.get_changed_file(filename, alert_identical)
            if not path:
                continue

            if is_tsf_modules:
                if not module_active:
                    self.reporter.review_error(3, filename)
                    continue

            self.copy_reviewed_file(path, filename, self.review_dir)
            self.reporter.review_info(2, filename)

        self.reporter.info("{} reviewed".format(list_name))

    def review_gear(self):
        # Get GAT and validate kits
        self.reporter.set_msg_prefix("(Gear)(GAT)")
        self.reporter.info("Validating GAT kits")

        dir_path = self.target_dir

        gat = self.get_file_path(dir_path, self.Gear.get_gat())
        if not gat:
            self.reporter.error("No Gear Assignment Table file found!")
            self.reporter.review_error(4)
            return

        gat_kits = self.Gear.get_gat_kits(gat)
        if not gat_kits:
            self.reporter.error("Failed to find kits in Gear Assignment Table!")
            self.reporter.review_error(5)
        else:
            self.reporter.info("There are {} kits in GAT file.".format(len(gat_kits)))
            for kit in gat_kits:
                if self.Gear.check_kit_exists(kit):
                    self.reporter.info("    Kit {} exists.".format(kit))
                else:
                    self.reporter.error("   Kit {} is missing!".format(kit))
                    self.reporter.review_error(6, kit)
        self.reporter.info("GAT validated")

        # Get files and check for kits
        self.reporter.set_msg_prefix("(Gear)(Checklist)")
        checklist = self.Gear.get_checklist()
        for fileInfo in checklist:
            file = fileInfo.get("file", "")
            pattern = fileInfo.get("pattern", "")
            self.reporter.info("Validating [{}] file".format(file))

            if self.tSF.check_is_shortcut(file):
                module = self.tSF.get_module_from_path(file)
                if not self.tSF.is_module_active(module):
                    self.reporter.info("Skipping checks for inactive module [{}]".format(module))
                    continue

            file = self.get_file_path(dir_path, file)

            if not os.path.isfile(file):
                self.reporter.error("Skip [{}] - file not found. ".format(file))
                continue

            kits_found = self.Gear.check_kit_in_file(file, pattern)
            if not kits_found:
                self.reporter.error("Failed to find kits in [{}] file!".format(file))
                self.reporter.review_error(8, file)
            else:
                for kitInfo in kits_found:
                    kit_name = kitInfo.get("name")
                    if kitInfo.get("valid"):
                        self.reporter.info("    Kit [{}] exists".format(kit_name))
                    else:
                        self.reporter.error("   Kit [{}] is missing in Kits.sqf".format(kit_name))
                        self.reporter.review_error(7, kit_name, file)

            self.reporter.info("Finished")

    def read_config(self, filename):
        # Check that config file exists and reads it data to dictionary
        # Returns: Dictionary or stops execution if none found
        try:
            return ConfigReader(filename)
        except FileNotFoundError:
            self.fatal_and_exit("Could not find config file [" + filename + "]!")
        except ValueError:
            self.fatal_and_exit("Could not read config file! File is malformed!")

    def get_mission_dir(self):
        # Prompt GitHub URL or full path to mission, then returns dir to mission if exists
        # Returns: Mission directory or empty string, if not exists (STRING)
        msg = "GitHub repo URL or path to mission:"
        url = input(msg)
        while not url:
            print("Warning! Empty URL/path is given. Please, profive valid URL/path!")
            url = input(msg)

        dir_path = ""
        if url.startswith("http"):
            self.reporter.info("Mission repo URL is provided. Downloading attemp...")
            downloader = Downloader(self.reporter)
            dir_path = downloader.download(url)
            if not dir_path:
                self.fatal_and_exit("Repo URL is unreachable (non-existing?)!")

            self.reporter.info("Mission repo downloaded successfully")
        else:
            self.reporter.info("Mission local path was provided. Checking...")
            dir_path = url
            if not os.path.isdir(dir_path):
                self.fatal_and_exit("Local mission path is unreachable (non-existing?)!")
            self.reporter.info("Mission local path exists.")

        # print(dir_path)
        return dir_path

    def create_review_dir(self, name):
        # Creates or re-creates review directory, removing all old files
        dir_path = None
        try:
            if os.path.isdir(name):
                shutil.rmtree(name)
            os.mkdir(name)
            dir_path = name
        except OSError:
            self.fatal_and_exit("Failed to create review directory!")

        return dir_path

    def get_changed_file(self, filename, alert_identical):
        # Validates and compare file from target and reference dirs, reports state to log and review
        # Returns: Changed file path or empty string otherwise (STRING)

        self.reporter.info("Check file for difference [{}], alert?: {}".format(filename, alert_identical))
        ref_file = self.get_file_path(self.ref_dir, filename)
        if not ref_file:
            self.reporter.review_error(1, filename)
            return ""

        tgt_file = self.get_file_path(self.target_dir, filename)
        if not tgt_file:
            self.reporter.review_warn(1, filename)
            return ""

        are_identical = self.comparator.compare(ref_file, tgt_file)
        if are_identical:
            if alert_identical:
                self.reporter.review_error(2, filename)
            else:
                self.reporter.review_info(1, filename)
            return ""

        return tgt_file

    def get_file_path(self, target_dir, filename):
        # Returns: Path to file or empty string, if file not exists (STRING)

        # print("\n## Get File Path invoked ##")
        # print("Init filename: " + filename)
        if self.tSF.check_is_shortcut(filename):
            filename = self.tSF.get_file(filename[6:])
        path = os.path.join(target_dir, filename)

        # print("Target dir: " + target_dir)
        # print("File: " + filename)
        # print("# Path: " + path)
        # print()

        if not os.path.isfile(path):
            return ""
        return path

    def copy_reviewed_file(self, path, file, to):
        # Copies and renames given file to format Dir1_Dir2_DirN_Filename
        new_name = os.path.join(to, "_".join(file.split(os.sep)))

        self.reporter.info("-- Copy changed file -- from {} to {}".format(path, new_name))
        try:
            shutil.copyfile(path, new_name)
        except:
            self.reporter.error("Failed to copy file {} to review directory".format(path))

    def fatal_and_exit(self, msg):
        # Reports Fatal error and stops execution
        self.reporter.fatal(msg)
        sys.exit(msg)


class Comparator:

    def compare(self, ref_file, review_file):
        return filecmp.cmp(ref_file, review_file)


def main():
    print("Start")

    reviewer = Reviewer()
    reviewer.prepare()
    reviewer.review("Core")
    reviewer.review("Dynai")
    reviewer.review("Gear")
    reviewer.review("tSF")
    reviewer.review("tSF_modules")
    reviewer.review_gear()


if __name__ == "__main__":
    main()

print("Done")

