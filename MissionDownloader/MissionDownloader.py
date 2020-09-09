url = input("GitHub repo URL:")
mode = int(input("Select mode: [1] - Download, [2] - Download & pack\n"))

import requests
import re
import os

def DownalodAndUnzipFiles(url):
    print("Getting Readme.md...")

    urlReadme = "https://raw.githubusercontent.com/" + url.rsplit('/',2)[1] + "/" + url.rsplit('/',2)[2] + "/master/README.md"

    readmeRequest = requests.get(urlReadme, allow_redirects=True)
    readmeText = readmeRequest.text

    versionRXP = re.compile('(Version: (\d[A-Za-z]))')
    version = versionRXP.search(readmeText)[2]

    print("Version: " + version)

    print("Getting mission archive...")

    urlZip = url + "/archive/master.zip"

    filename = url.rsplit('/',1)[1] + "-master"
    zipFilename = filename + "-master.zip"
    zipRequest = requests.get(urlZip, allow_redirects=True)
    open(zipFilename, "wb").write(zipRequest.content)

    print("Mission archive downloaded - " + zipFilename)

    print("Unzipping archive...")

    from zipfile import ZipFile
    with ZipFile(zipFilename,'r') as zipObj:
        zipObj.extractall()
        
    os.remove(zipFilename)
        
    print("Unzipped to " + filename)

    print("Renaming folder...")

    rxp = re.compile('(.*)((\.)(.*)(-master))')
    filenameParts = (rxp.findall(filename))[0]
    filenameRenamed = filenameParts[0] + "_" + version + "." + filenameParts[3]
    os.rename(filename, filenameRenamed)

    print("Renamed to " + filenameRenamed)
    
    return filenameRenamed


def PackMission(filename):
    
    CleanMissionFiles(filename)
    
    print("Packing...")
    import subprocess
    subprocess.run(["MakePbo","-N", os.path.abspath(filename)])
    print("Packed!")


def CleanMissionFiles(filename):
    print("Cleaning mission files from " + filename + "...")
    
    """
    - Remove Helpers at:
        filename\init3DEN.sqf
        filename\README.md
        filename\tSF_FileSweeper.bat
        filename\dzn_tSFramework\tS_SettingsOverview.html
        filename\dzn_tSFramework\3DEN\*
        filename\dzn_tSFramework\Modules\Briefing\BriefingHelper\*
        filename\dzn_tSFramework\Modules\MissionConditions\EndingsHelper\*
        filename\dzn_dynai\tools
        
    - Read filename/dzn_tSFramework/dzn_tSFramework_Init.sqf
    - Find all 'tSF_module_<MODULE_NAME> = <BOOL>' and move in pairs
    - For each pair -- if <BOOL> = false --> remove filename/dzn_tSFramework/Modules/<MODULE_NAME> folder 
 
    """
    pass

### Start
if mode == 1:
    print("Executing mode - Download")
elif mode == 2:
    print("Executing mode - Download & Pack to PBO")

filename = DownalodAndUnzipFiles(url)
if mode == 2:
    PackMission(filename)

print("All done! Have a nice day!")
