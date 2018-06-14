import os
import json
import logging
import re
import sys
import zipfile

logger = logging.getLogger("stir")


class Version(object):

    def __init__(self, version_string):
        self.string = version_string

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


def cmp(a, b):
    """ trick to get python3 working with cmp """
    return (a > b) - (a < b)

def clean_package_name(name):
    return name.strip().lower().replace(" ", "-")


def find_files(path, patterns):
    """ Custom find function that handles patterns like "**" and "*" """

    logger.debug(
        "finding files at %s (CWD: %s) with pats %s",
        path, os.getcwd(), patterns)
    path = get_linux_path(path)
    file_list = []
    star_re = r"([^/]+)"
    rec_re = r"(.+)"
    re_pats = []

    for pat in patterns:
        pat_e = re.escape(get_relpath(get_linux_path(pat)))
        pat_e = pat_e.replace("\*\*", rec_re).replace("\*", star_re) + "$"
        cmp_re = re.compile(pat_e)
        re_pats.append(cmp_re)

    for root, _, files in os.walk(path):
        logger.debug("found: %s", get_linux_path(root))
        # get_globs(root)
        for f in files:
            fname = get_relpath(get_linux_path(os.path.join(root, f)))
            # print(fname)
            for pre in re_pats:
                # print(pre, fname)
                m = pre.match(fname)
                if m:
                    if fname not in file_list:
                        file_list.append(fname)
                    logger.debug("MATCH: %s", fname)

    return file_list


def find_files_chroot(path, patterns):

    curdir = get_curdir()
    os.chdir(path)
    files = find_files(".", patterns)
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


def get_yn(message, exit_on_n=False):
    message = "%s [Y/n]" % message
    yn = get_input(message, default="n").lower()
    if yn in ["y", "yes"]:
        return True
    if exit_on_n:
        sys.exit()
    return False


def json_load(path):
    with open(path, "r") as fh:
        return json.load(fh)


def json_save(path, data):
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def zipfile_create(output_path, file_paths):

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zfh:
        for fp in file_paths:
            zfh.write(fp)


def zipfile_extract(output_path, zip_path):

    with zipfile.ZipFile(zip_path, "r") as zfh:
        zfh.extractall(output_path)
