import re

build_name = "tSF_ReviewHelper"
build_version = "0.2"
project_files = [
    "Reporter.py",
    "ConfigReader.py",
    "Downloader.py",
    "tSFSettings.py",
    "GearSettings.py",
    "ReviewHelper.py"
]

import_pattern = "import (.+)"
import_excluded_keywords = ("Reporter", "Downloader", "tSFSettings", "GearSettings", "ConfigReader")


def get_imports_from_line(line):
    r = re.search(import_pattern, line, re.I)
    if r:
        return line
    return ""


def write_from_file(file_from, file_to):
    with open(file_from, "r") as src:
        for line in src:
            import_line = get_imports_from_line(line)
            if import_line:
                continue
            file_to.write(line)


def get_imports(file):
    imports = set()
    with open(file, 'r') as f:
        for line in f:
            line = get_imports_from_line(line)
            if not line:
                continue

            exclude = False
            for ex_word in import_excluded_keywords:
                if ex_word in line:
                    exclude = True

            if exclude:
                continue

            imports.add(line)

    return imports


# Start execution
build_name = "{}_v{}.py".format(build_name, build_version)

# Write imports
with open(build_name, "w") as f:
    f.write("# -------------------------\n")
    f.write("# tSF Review Helper v{}\n".format(build_version))
    f.write("# -------------------------\n\n")
    imports = set()
    for pf in project_files:
        imports.update(get_imports(pf))

    for iml in imports:
        f.write(iml)

    f.write("\n")

# Write file content
with open(build_name, "a") as build_file:
    for pf in project_files:
        write_from_file(pf, build_file)
        build_file.write("\n\n")
