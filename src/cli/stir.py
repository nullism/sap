#!/usr/bin/env python
import os
import re
import datetime
import time
import glob
import zipfile
import sys
import json
import argparse
import logging
import utils
#import raw_input

logger = logging.getLogger("stir")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

DEFAULT_VERSION = "0.0.1"
DEFAULT_PATTERNS = ["**"]


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


class Server():

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_best_version(self, version):
        return "0.0.1"

    def get_package_data(self, name, version):
        best_v = self.get_best_version(version)
        dpath = "%s-%s.json" % (name, best_v)
        return utils.json_load(dpath)

    def get_package_zip(self, name, version):
        best_v = self.get_best_version(version)
        zpath = "%s-%s.zip" % (name, best_v)
        return zpath


def command_commit(args):

    if args.file:
        args.file = utils.get_linux_path(args.file)
    else:
        args.file = utils.get_linux_path(
            os.path.join(utils.get_curdir(), "stir-source.json"))

    if not os.path.exists(args.file):
        if not args.yes:
            utils.get_yn(
                "stir-source.json not found, create it?", exit_on_n=True)
        utils.json_save(args.file, {"packages": []})

    commit(
        name=args.package,
        path=args.path,
        patterns=args.patterns,
        version=args.version,
        file_path=args.file)


def commit(name, path, patterns=None, version=None, file_path=None):

    patterns = patterns or DEFAULT_PATTERNS
    name = utils.clean_package_name(name)

    logger.info("adding new package: %s", name)

    file_list = utils.find_files_chroot(path, patterns)
    print(file_list)

    if len(file_list) < 1:
        raise Exception("packages must contain at least 1 file")

    file_data = utils.json_load(file_path)

    last_push = None
    for pdata in file_data["packages"]:
        if pdata["name"] != name:
            continue
        if not version:
            v = Version(pdata["version"])
            v.increment(tiny=1)
            version = v.string
        last_push = pdata["last_push"]
        file_data["packages"].remove(pdata)

    package_data = {
        "name": name,
        "version": version or DEFAULT_VERSION,
        "patterns": patterns,
        "files": file_list,
        "last_push": last_push,
        "last_modified": int(time.time()),
    }

    file_data["packages"].append(package_data)
    utils.json_save(file_path, file_data)


def command_pull(args):
    pass


def command_push(args):
    pass


def command_remove(args):
    pass


def cmp(a, b):
    """ trick to get python3 working with cmp """
    return (a > b) - (a < b)


def main():
    #print(find_files(path="../../", patterns=["*"]))
    default_server = os.environ.get("STIR_SERVER", "localhost")
    parser = argparse.ArgumentParser(description="Interact with libget")
    parser.add_argument(
        "-s", "--server", help="the server to use [env LIBGET_SERVER], default: %s" %
        default_server, default=default_server)
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="force yes or default on questions")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase logging output")

    subparsers = parser.add_subparsers()

    # Source
    commit = subparsers.add_parser("commit", help="commit a package")
    commit.add_argument("package", help="package name to add")
    commit.add_argument("path", help="path to package relative to FILE dir")
    commit.add_argument("-p", "--patterns",
                        help="patterns, use '**' for recursion", nargs="*")
    commit.add_argument("-f", "--file", help="path to stir-source file")
    commit.add_argument("-v", "--version", help="manually specify a version")
    commit.set_defaults(func=command_commit)

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("set to verbose output")

    args.func(args)


if __name__ == "__main__":
    main()
