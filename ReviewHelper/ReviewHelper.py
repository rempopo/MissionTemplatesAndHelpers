import os
import sys
import shutil
import yaml
import filecmp

from Reporter import Reporter
from Downloader import Downloader
from tSFSettings import tSFSettings
from GearSettings import GearSettings
from ConfigReader import ConfigReader


class Reviewer:
    USE_TEST_MISSION = True

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

        self.reporter.info("-- Copy file -- from {} to {}".format(path, new_name))
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

print("Exec")
