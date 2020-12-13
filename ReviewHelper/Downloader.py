import os
import shutil
import requests
from zipfile import ZipFile


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
