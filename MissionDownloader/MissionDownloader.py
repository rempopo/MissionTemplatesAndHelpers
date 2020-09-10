url = input("GitHub repo URL:")
mode = int(input("Select mode: [1] - Download, [2] - Download & pack\n"))
steps = "6"

import requests
import re
import os
import shutil
import sys

def DownalodAndUnzipFiles(url):
    print("[1/" + steps + "] Getting Readme.md...")

    urlReadme = "https://raw.githubusercontent.com/" + url.rsplit('/',2)[1] + "/" + url.rsplit('/',2)[2] + "/master/README.md"

    readmeRequest = requests.get(urlReadme, allow_redirects=True)
    readmeText = readmeRequest.text

    version = "1A"    
    versionRXP = re.compile('(Version: (\d[A-Za-z]))')
    versionSearched = versionRXP.search(readmeText)
    if versionSearched:
        version = versionSearched[2]

    print("Version: " + version)

    print("[2/" + steps + "] Getting mission archive...")

    urlZip = url + "/archive/master.zip"

    filename = url.rsplit('/',1)[1] + "-master"
    zipFilename = filename + "-master.zip"
    zipRequest = requests.get(urlZip, allow_redirects=True)
    
    if os.path.exists(zipFilename):
        os.remove(zipFilename)
    
    open(zipFilename, "wb").write(zipRequest.content)

    print("Mission archive downloaded - " + zipFilename)

    print("[3/" + steps + "] Unzipping archive...")

    from zipfile import ZipFile
    with ZipFile(zipFilename,'r') as zipObj:
        zipObj.extractall()
        
    os.remove(zipFilename)

    print("Unzipped to " + filename)

    print("[4/" + steps + "] Renaming folder...")
    
    if (re.search(r'(\d[a-zA-Z].)', filename, re.I)):
        filenameRenamed = filename.replace("-master","")
    else:
        rxp = re.compile('(.*)((\.)(.*)(-master))')
        filenameParts = (rxp.findall(filename))[0]
        filenameRenamed = filenameParts[0] + "_" + version + "." + filenameParts[3]
    
    if os.path.exists(filenameRenamed):
        print("" + filenameRenamed + " already exists!")
        dialog = input("\nRemove existing directory? [Y] [N] -> ")
        if dialog.lower() == 'y':
            shutil.rmtree(filenameRenamed)
        else:
            sys.exit("Directory already exists")
   
    os.rename(filename, filenameRenamed)
    print("Renamed to " + filenameRenamed)
    
    return filenameRenamed


def PackMission(filename):
    
    CleanMissionFiles(filename)
    
    print("[6/" + steps + "] Packing...")
    import subprocess
    subprocess.run(["MakePbo","-N", os.path.abspath(filename)])
    print("Packed!")


def CleanMissionFiles(filename):
    print("[5/" + steps + "] Cleaning mission files from " + filename + "...")
    
    ### Remove files 
    files = [
        os.path.join(filename, "init3DEN.sqf"),
        os.path.join(filename, "README.md"),
        os.path.join(filename, "tSF_FileSweeper.bat"),
        os.path.join(filename, "tSF_FS_log.txt"),
        os.path.join(filename, ".gitattributes"),
        os.path.join(filename, "dzn_tSFramework\\tS_SettingsOverview.html")
    ]
    dirs = [
        os.path.join(filename, "dzn_tSFramework\\3DEN\\"),
        os.path.join(filename, "dzn_tSFramework\\Modules\\Briefing\\BriefingHelper\\"),
        os.path.join(filename, "dzn_tSFramework\\Modules\\MissionConditions\\EndingsHelper\\"),
        os.path.join(filename, "dzn_dynai\\tools\\")
    ]
    
    for f in files:
        if os.path.exists(f):
            print("    Deleting " + f)
            os.remove(f)
    
    for d in dirs:
        if os.path.exists(d):
            print("    Deleting directory " + d)
            shutil.rmtree(d)
    
    print("\nRemoving unused tSF Modules...")
   
    tSDir = os.path.join(filename, "dzn_tSFramework\\Modules\\")
    tSFFile = open(os.path.join(filename, "dzn_tSFramework\\dzn_tSFramework_Init.sqf"), "r")
    for line in tSFFile:
        r = re.search(r'(tSF_module_)([a-zA-Z\_]*)([\s=]+)(false|true)', line, re.I)
        if r:
            moduleDir = r[2]
            moduleEnabled = r[4].lower() == 'true'
            modulePath = os.path.join(tSDir, moduleDir)
            
            if not moduleEnabled and os.path.exists(modulePath):
                print("    Module " + moduleDir + " is disabled: removing " + os.path.join(tSDir, moduleDir))
                shutil.rmtree(modulePath)
    
    tSFFile.close()


### Start
print("Execution mode - Download") if mode == 1 else print("Execution mode - Download & Pack to PBO")

filename = DownalodAndUnzipFiles(url)
if mode == 2:
    PackMission(filename)

print("All done! Have a nice day!")
