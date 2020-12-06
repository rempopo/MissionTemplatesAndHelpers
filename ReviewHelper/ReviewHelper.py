VERBOSE = True


import os
import sys
import shutil
import time
import yaml
import requests
from zipfile import ZipFile
import filecmp
import re

class Reviewer:

    def __init__(self):
        self.reporter = Reporter()
        self.comparator = Comparator()

        self.configName = "config.yaml"
        self.config = None
        self.targetDir = None
        self.reviewDir = None
        self.refDir = None


    def prepare(self):
        self.reporter.info("---------- App Started ----------")
        self.reporter.info("Initializiation")

        self.config = self.read_config(self.configName);
        self.reporter.setup(self.config)
        self.reporter.info("Config read successfully")

        self.refDir = self.config["reference_path"]
        if not self.refDir or not os.path.isdir(self.refDir):
            self.fatal_and_exit("Error: Could not find reference directory!")

        self.targetDir = self.get_mission_dir()
        self.reviewDir = self.create_review_dir(self.config["review_directory_name"])
        
        self.reporter.info("| Reference | " + self.refDir)
        self.reporter.info("| Revivewed | " + self.targetDir)
        self.reporter.info("| Review to | " + self.reviewDir)

        self.reporter.info("Initialized")


    def review(self, listname):
        self.reporter.info("(Review) Review started for {}".format(listname))
        filelist = self.config["Checklist"][listname]

        istSFModules = listname == "tSF_modules"
        pathPrefix = ""
        tSFModulesSettings = None

        if istSFModules:
            pathPrefix = self.config["tSF_config"]["path"]
            tSFModulesSettings = self.get_tsf_settings(self.config["tSF_config"])
            if not tSFModulesSettings:
                self.reporter.error("No dzn_tSFFramework_Init.sqf file found in reviewed mission!")
                return

        for fileInfo in filelist:
            filename = os.path.join(pathPrefix, fileInfo.get("file",""))
            alertIdentic = fileInfo.get("alert", False)
            
            self.reporter.info("(Review) Reviewing file {}".format(filename))
            
            moduleActive = False
            if istSFModules:
                module = os.path.split(fileInfo.get("file",""))[0]
                moduleActive = tSFModulesSettings.get(module, False)
                
                alertIdentic = alertIdentic and moduleActive
           
            path = self.get_changed_file(filename, alertIdentic)
        
            if not path:
                continue

            if istSFModules:
                if not moduleActive:
                    self.reporter.review_error(3, filename)
                    continue

            self.copy_reviewed_file(path, filename, self.reviewDir)
            self.reporter.review_info(2, filename)
            
        
        self.reporter.info("(Review) {} reviewed".format(listname))


    def read_config(self, filename):
        if not os.path.isfile(filename):
            self.fatal_and_exit("Could not find config file [" + filename + "]!")

        cfg = {}
        try:
            with open(filename,"r") as yamlfile:
                cfg = yaml.load(yamlfile, Loader=yaml.BaseLoader)
        except:
            self.fatal_and_exit("Could not read config file!")
        return cfg


    def get_mission_dir(self):
        # Promt GitHub URL or full path to mission
        msg = "GitHub repo URL or path to mission:"
        url = input(msg)
        while not url:
            print("Warning! Empty URL/path is given. Please, profive valid URL/path!")
            url = input(msg)

        dir = ""
        if url.startswith("http"):
            self.reporter.info("Mission repo URL is provided. Downloading attemp...")
            downloader = Downloader(self.reporter)
            dir = downloader.download(url)
            if not dir:
                self.fatal_and_exit("Repo URL is unreachable (non-existing?)!")
            
            self.reporter.info("Mission repo downloaded successfully")
        else:
            self.reporter.info("Mission local path was provided. Checking...")
            dir = url
            if not os.path.isdir(dir):
                self.fatal_and_exit("Local mission path is unreachable (non-existing?)!")
            self.reporter.info("Mission local path exists.")
            
        print(dir)
        return dir


    def create_review_dir(self, name):
        dir = None
        try:
            if os.path.isdir(name):
                shutil.rmtree(name)
            os.mkdir(name)
            dir = name
        except OSError:
            self.fatal_and_exit("Failed to create review directory!")

        return dir


    def get_changed_file(self, filename, alertIdentic):
        self.reporter.info("Check file for difference [{}], alert?: {}".format(filename, alertIdentic))
        refFile = self.get_file_path(self.refDir, filename)
        if not refFile:
            self.reporter.review_error(1, filename)
            return ""

        tgtFile = self.get_file_path(self.targetDir, filename)
        if not tgtFile:
            self.reporter.review_warn(1, filename)
            return ""

        areIdentic = self.comparator.compare(refFile, tgtFile)
        if areIdentic:
            if alertIdentic:
                self.reporter.review_error(2, filename)
            else:
                self.reporter.review_info(1, filename)
            return ""

        return tgtFile


    def get_file_path(self, targetDir, filename):
        path = os.path.join(targetDir, filename)
        if not os.path.isfile(path):
            return ""
        return path


    def get_tsf_settings(self, config):
        file = os.path.join(self.targetDir, config.get("config"))
        if not os.path.isfile(file):
            return {}

        settings = {}
        with open(os.path.join(self.targetDir, config.get("config")), "r") as tSFFile:
            for line in tSFFile:
                r = re.search(config.get("pattern"), line, re.I)
                if r:
                    settings[r[1]] = r[2].lower() == 'true'

        return settings


    def copy_reviewed_file(self, path, file, to):
        newName = os.path.join(to, "_".join(file.split(os.sep)))
        
        self.reporter.info("-- Copy file --")
        self.reporter.info("Path: " + path)
        self.reporter.info("File: " + file)
        self.reporter.info("To: " + to)
        self.reporter.info("Dest: " + newName)
        try:
            shutil.copyfile(path, newName)
        except:
            self.reporter.error("Failed to copy file {} to review directory".format(path))


    def fatal_and_exit(self, msg):
        self.reporter.fatal(msg)
        sys.exit(msg)


class Reporter:

    def __init__(self):
        self.config = None
        self.reviewLogFile = None
        self.logFile = "log.log"
        self.log("START", "--------------------------------", "w+")

    def setup(self, config):
        self.config = config
        self.reviewLogFile = "Review.log"
        self.write_review("-------- Review started ------","w+")

    
    def write_review(self, message, mode="a"):
        try:
            with open(self.reviewLogFile, mode) as f:
                f.write(message + "\n")
                f.close()
        except:
            self.fatal("Error happened during log writing!")


    def log(self, type, message, mode="a"):
        try:
            with open(self.logFile, mode) as f:
                msg = time.strftime("%Y-%m-%d %H:%M:%S") + " [" + type + "] " + message + "\n"
                print(msg)
                f.write(msg)
                f.close()
        except:
            print("Error happened during log writing!")


    def info(self, message):
        self.log("INFO", message)


    def error(self, message):
        self.log("ERROR", message)


    def fatal(self, message):
        self.log("FATAL ERROR", message)


    def format_review_msg(self, type, code, arg1, arg2="", arg3="", arg4=""):
        return "[{}] {}".format(type, self.config["Reporter"][type.lower() + str(code)].format(arg1, arg2, arg3, arg4))


    def review_info(self, code, arg1, arg2="", arg3="", arg4=""):
        if not VERBOSE:
            return()
        self.write_review(self.format_review_msg("INFO", code, arg1, arg2, arg3, arg4))


    def review_warn(self, code, arg1, arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("WRN", code, arg1, arg2, arg3, arg4))


    def review_error(self, code, arg1, arg2="", arg3="", arg4=""):
        self.write_review(self.format_review_msg("ERR", code, arg1, arg2, arg3, arg4))


class Downloader:
    BRANCH_MAIN = "main"
    BRANCH_MASTER = "master"
    URL_FORMAT = "{}/archive/{}.zip"

    def __init__(self, reporter):
        self.reporter = reporter;


    def download(self, url):
        self.reporter.info("Downloading mission: " + url)

        fileURL = self.get_file_url(url)
        if not fileURL:
            return ""

        zipRequest = requests.get(fileURL, allow_redirects=True)
        fileNameParts = fileURL.rsplit('/',3);
        filename = "{}-{}".format(fileNameParts[1], fileNameParts[3])

        if os.path.isfile(filename):
            os.remove(filename)

        with open(filename, "wb") as file:
            file.write(zipRequest.content)
            file.close()

        self.reporter.info("Mission repo downloaded, unzipping.")
        self.unzip(filename)
        dir = self.rename_folder(filename)
        self.reporter.info("Mission repo unpacked.")

        return dir


    def validate_repo(self, url):
        request = requests.get(url)
        return request.status_code == 200


    def get_file_url(self, repoURL):
        url = self.URL_FORMAT.format(repoURL, self.BRANCH_MAIN)
        if self.validate_repo(url):
            return url

        url = self.URL_FORMAT.format(repoURL, self.BRANCH_MASTER)
        if self.validate_repo(url):
            return url

        return ""


    def unzip(self, filename):
        try:
            with ZipFile(filename,"r") as file:
                file.extractall()
            os.remove(filename)
        except:
            self.reporter.fatal("Unziping failed!")


    def rename_folder(self, filename):
        oldName = filename.rstrip(".zip")
        newName = filename.rstrip("-({}|{}).zip".format(self.BRANCH_MAIN, self.BRANCH_MASTER))
        if os.path.isdir(newName):
            shutil.rmtree(newName)

        os.rename(oldName, newName)
        
        return newName


class Comparator:

    def compare(self, refFile, reviewFile):
        return filecmp.cmp(refFile, reviewFile)



def main():
    print("Start")

    reviewer = Reviewer()
    reviewer.prepare()
    reviewer.review("Core")
    reviewer.review("Dynai")
    reviewer.review("Gear")
    reviewer.review("tSF")
    reviewer.review("tSF_modules")



if (__name__ == "__main__"):
    main()

print("Exec")