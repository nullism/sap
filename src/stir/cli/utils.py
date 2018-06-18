import os
import json
import logging
import re
import sys
import zipfile

logger = logging.getLogger("stir")


class Version(object):
    def __init__(self, version_string):
        parts = version_string.split(".")
        if len(parts) != 3:
            raise Exception("Invalid version %s" % version_string)

        self.major = int(parts[0])
        self.minor = int(parts[1])
        self.tiny = int(parts[2])

    def __repr__(self):
        return self.string

    def __cmp__(self, other):
        # allows comparing strings
        if not isinstance(other, Version):
            other = Version(other)

        def normalize(v):
            return [
                int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")
            ]
        return cmp(normalize(self.string), normalize(other.string))

    @property
    def string(self):
        return "%s.%s.%s" % (self.major, self.minor, self.tiny)

    def increment(self, major=0, minor=0, tiny=0):
        self.major += major
        self.minor += minor
        self.tiny += tiny


def cmp(a, b):
    """ trick to get python3 working with cmp """
    return (a > b) - (a < b)

def clean_package_name(name):
    return name.strip().lower().replace(" ", "-")


def find_files(path, patterns, excludes=[]):
    """ Custom find function that handles patterns like "**" and "*" """

    logger.debug(
        "finding files at %s (CWD: %s) with pats %s",
        path, os.getcwd(), patterns)
    path = get_linux_path(path)
    file_list = []
    star_re = r"([^/]+)"
    rec_re = r"(.*)"
    re_pats = []
    re_excs = []

    for pat in patterns:
        pat_e = re.escape(get_relpath(get_linux_path(pat)))
        pat_e = pat_e.replace("\*\*", rec_re).replace("\*", star_re) + "$"
        cmp_re = re.compile(pat_e)
        re_pats.append(cmp_re)

    for pat in excludes:
        pat_e = re.escape(get_relpath(get_linux_path(pat)))
        pat_e = pat_e.replace("\*\*", rec_re).replace("\*", star_re) + "$"
        cmp_re = re.compile(pat_e)
        re_excs.append(cmp_re)

    for root, _, files in os.walk(path):
        logger.debug("found: %s", get_linux_path(root))
        # get_globs(root)
        for f in files:
            exclude_m = None
            fname = get_relpath(get_linux_path(os.path.join(root, f)))
            # print(fname)
            for pre in re_excs:
                exclude_m = pre.match(fname)
                print(pre, fname, exclude_m)
                if exclude_m:
                    break
            if exclude_m:
                continue
            for pre in re_pats:
                # print(pre, fname)
                m = pre.match(fname)
                if m:
                    if fname not in file_list:
                        file_list.append(fname)
                    logger.debug("MATCH: %s", fname)

    return file_list


def find_files_chroot(path, patterns, excludes=[]):

    curdir = get_curdir()
    os.chdir(path)
    files = find_files(".", patterns, excludes)
    os.chdir(curdir)
    return files


def get_curdir():

    return os.path.abspath(os.curdir)


def get_input(message, default=None):
    if default:
        message = "%s (%s) " % (message, default)
    try:
        # Python 2.7 compatibility
        inp = raw_input(message)  # pylint: disable=E0602
    except:
        inp = input(message)
    inp = inp.strip()
    if not inp:
        return default
    return inp


def get_linux_path(path):
    return path.replace("\\", "/")


def get_relpath(path):
    if path.startswith("./"):
        return path[2:]
    return path


def get_source_file_path(file_path):

    if not file_path:
        file_path = os.path.join(get_curdir(), "stir-source.json")

    return get_linux_path(file_path)

def get_stir_file_path(root_dir=None):

    if not root_dir:
        root_dir = get_curdir()
    return os.path.join(root_dir, "stir.json")

def get_stir_packages(root_dir=None):

    if not root_dir:
        root_dir = get_curdir()

    package_files = find_files(root_dir, ["**/stir.json"])
    packages = []
    for pf in package_files:
        data = json_load(pf)
        data["stir_file"] = pf
        packages.append(data)

    return packages

def get_valid_package_names(package_names, file_data_list):
    package_names = [clean_package_name(p) for p in package_names]
    pnames = []
    for fdata in file_data_list:
        for pdata in fdata["packages"]:
            if pdata["name"] in package_names:
                pnames.append(pdata["name"])
    not_found = [n for n in package_names if n not in pnames]
    if len(not_found) > 0:
        raise Exception("could not find packages: %s" % not_found)
    return pnames

def get_yn(message, exit_on_n=False):
    message = "%s [Y/n]" % message
    yn = get_input(message, default="n").lower()
    if yn in ["y", "yes"]:
        return True
    if exit_on_n:
        sys.exit()
    return False

def increment_tiny(version_string, amount=1):
    vo = Version(version_string)
    vo.increment(tiny=1)
    return vo.string

def json_load(path):
    with open(path, "r") as fh:
        return json.load(fh)


def json_save(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)

def zipfile_create_chroot(chdir, output_path, file_paths):

    curdir = get_curdir()
    os.chdir(chdir)
    zipfile_create(output_path, file_paths)
    os.chdir(curdir)

def zipfile_create(output_path, file_paths):
    # Exclude stir.json

    for fn in file_paths:
        if os.path.basename(fn) == "stir.json":
            file_paths.remove(fn)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zfh:
        for fp in file_paths:
            zfh.write(fp)


def zipfile_extract(output_path, zip_path):

    with zipfile.ZipFile(zip_path, "r") as zfh:
        zfh.extractall(output_path)
