#!/usr/bin/env python
import os
import re
import datetime
import glob
import zipfile
import sys
import json
import argparse
import logging
#import raw_input

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# 1. read .libget-source
# 2. zip files specified
# 3. upload to server specified (.zip, .json)
# 4. increment minor version if not autoincrement=false


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


class Package(object):

    files = []

    def __init__(
            self, name, version, path,
            modified, created):

        self.name = Package.clean_name(name)
        self.version = Version(version.strip())
        self.path = get_linux_path(path)
        self.modified = modified
        self.created = created

    @classmethod
    def clean_name(cls, package_name):
        return package_name.strip().lower().replace(" ", "-")

    @classmethod
    def get_name_version(cls, package_string):
        ops = [">=", "<=", "==", "!="]
        for op in ops:
            if op in package_string:
                parts = package_string.split(op)
                return (Package.clean_name(parts[0]), "%s%s" % (op, parts[1]))
        return (package_string, None)

    @property
    def data(self):
        return dict(
            name=self.name,
            path=self.path,
            version=self.version.string,
            modified=self.modified,
            created=self.created,
            files=self.files
        )

    def verify(self):

        if os.path.isabs(self.path):
            raise Exception(
                ("package paths should be relative to SOURCE_FILE "
                 "or TARGET_FILE directory"))


class ManifestPackage(Package):

    def __init__(self, name, version, path, modified, files):

        self.name = name
        self.version = Version(version.strip())
        self.path = path
        self.modified = modified
        self.files = files

    @classmethod
    def from_data(self, data):
        return ManifestPackage(
            name=data["name"],
            version=data["version"],
            path=data["path"],
            modified=data["modified"],
            files=data["files"])


    @property
    def data(self):
        return {
            "name": self.name,
            "version": self.version.string,
            "path": self.path,
            "modified": self.modified,
            "files": self.files
        }


class SourcePackage(Package):

    def __init__(
            self, name, version, path,
            patterns, modified, created, root_dir):

        super(SourcePackage, self).__init__(
            name, version, path, modified, created)

        self.patterns = patterns
        self.root_dir = root_dir

        self.verify()

    @classmethod
    def from_data(cls, data, root_dir):
        date_string = get_date_string()

        p = SourcePackage(
            name=data["name"],
            version=data["version"],
            path=data["path"],
            patterns=data["patterns"] or ["**"],
            modified=data["modified"] or date_string,
            created=data["created"] or date_string,
            root_dir=root_dir
        )
        return p

    @property
    def data(self):
        base_data = super(SourcePackage, self).data
        base_data.update(dict(
            patterns=self.patterns,
        ))
        return base_data

    @property
    def dir(self):
        return os.path.join(self.root_dir, self.path)

    @property
    def files(self):
        curdir = get_curdir()
        os.chdir(self.dir)
        files = find_files(".", self.patterns)
        os.chdir(curdir)
        if not files:
            raise Exception("packages must contain at least one file")
        return files

    def make_zip(self):

        curdir = get_curdir()
        zip_path = os.path.join(
            self.root_dir, "%s-%s.zip" % (self.name, self.version))
        logger.info("building package file")
        logger.debug("temporary package file path: %s", zip_path)
        os.chdir(self.dir)
        create_zipfile(zip_path, self.files)
        os.chdir(curdir)

    def make_data_file(self):

        output_path = os.path.join(
            self.root_dir, "%s-%s.json" % (self.name, self.version))
        with open(output_path, "w") as fh:
            json.dump(self.data, fh, indent=2)

    def verify(self):

        if not isinstance(self.patterns, list):
            raise Exception("patterns must be a list")

        if not os.path.exists(self.dir):
            raise Exception("package directory not found")

        return super(SourcePackage, self).verify()


class TargetPackage(Package):

    def __init__(self, name, version, path, modified, created, files):

        super(TargetPackage, self).__init__(
            name, version, path, modified, created)

        self.verify()

    @classmethod
    def from_data(self, data):
        date_string = get_date_string()
        p = TargetPackage(
            name=data["name"],
            version=data["version"],
            path=data["path"],
            modified=data["modified"] or date_string,
            created=data["created"] or date_string,
            files=data["files"]
        )
        return p


class Manager(object):

    packages = []
    file = None

    @property
    def package_names(self):
        return [p.name for p in self.packages]

    def get_package_by_name(self, package_name):
        package_name = Package.clean_name(package_name)
        for package in self.packages:
            if package.name == package_name:
                return package
        raise Exception("cannot find package (%s)" % package_name)

    def save(self):
        data = {
            "packages": [p.data for p in self.packages]
        }
        logger.info("saving source file to %s", self.file)
        with open(self.file, "w") as fh:
            json.dump(data, fh, indent=2)


class Manifest():

    file = None
    packages = []

    def __init__(self):
        self.file = os.path.join(get_sap_dir(), "manifest.json")

        if not os.path.exists(self.file):
            logger.info("creating manifest file")
            self.save()

        self.data = get_json_data(self.file)
        self.packages = [ManifestPackage.from_data(
            p) for p in self.data["packages"]]

    def add_package(self, package):

        try:
            new_package = self.get_package_by_name(package.name)
        except:
            new_package = ManifestPackage.from_data(package.data)
            self.packages.append(new_package)

        new_package.version = package.version
        new_package.path = package.path
        new_package.files = package.files
        new_package.modified = get_date_string()
        self.save()

    def remove_package(self, package):

        for p in self.packages:
            if p.name == package.name:
                logger.info("removing %s from manifest", p.name)
                self.packages.remove(p)

        self.save()


    def get_package_by_name(self, name):
        for p in self.packages:
            if p.name == name:
                return p
        raise Exception("can not find package: %s" % name)

    def save(self):
        logger.info("saving manifest data to %s", self.file)
        data = {
            "packages": [p.data for p in self.packages]
        }
        with open(self.file, "w") as fh:
            json.dump(data, fh, indent=2)


class Server():

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_best_version(self, version):
        return "0.0.1"

    def get_package_data(self, name, version):
        best_v = self.get_best_version(version)
        dpath = "%s-%s.json" % (name, best_v)
        return get_json_data(dpath)

    def get_package_zip(self, name, version):
        best_v = self.get_best_version(version)
        zpath = "%s-%s.zip" % (name, best_v)
        return zpath

class Source(Manager):

    packages = []

    def __init__(self, source_file, yes=False):

        self.file = source_file

        if not os.path.exists(source_file):
            if not yes:
                get_yn(
                    "source file (%s) does not exist, create it?" %
                    source_file, exit_on_n=True)
            self.save()

        self.dir = os.path.dirname(os.path.abspath(source_file))
        self.data = get_json_data(self.file)
        self.packages = [SourcePackage.from_data(
            p, root_dir=self.dir) for p in self.data["packages"]]
        self.yes = yes

    def add_package(self, package, local=False):

        logger.info("adding package (%s)", package.name)
        self.packages.append(package)
        self.save()
        # self.zip_package(package)
        package.make_zip()
        package.make_data_file()
        if not local:
            self.push_package(package)

    def push_package(self, package):
        logger.info("pushing package to server...")
        pass

    def rm_package(self, package_name, local=False):

        logger.info("removing package (%s)", package_name)
        package = self.get_package_by_name(package_name)
        self.packages.remove(package)
        self.save()

    def update_package(self, package, local=False):
        logger.info("updating package (%s)", package.name)
        for i in range(0, len(self.packages)):
            if self.packages[i].name == package.name:
                self.packages[i] = package
                self.save()
                package.make_zip()
                package.make_data_file()
                if not local:
                    self.push_package(package)
                return
        raise Exception("could not find package %s" % package.name)


class Target(Manager):

    packages = []

    def __init__(self, target_file, yes=False):

        self.server = Server("localhost", "8080")
        self.file = target_file
        self.cache_dir = os.path.join(get_sap_dir(), "cache")
        self.manifest = Manifest()
        self.data = get_json_data(self.file)
        self.packages = [TargetPackage.from_data(
            p) for p in self.data["packages"]]
        self.yes = yes
        if not os.path.exists(target_file):
            if not yes:
                get_yn(
                    "target file (%s) does not exist, create it?" % target_file,
                    exit_on_n=True)
            self.save()

        if not os.path.exists(get_sap_dir()):
            logger.info("making sap directory at %s", get_sap_dir())
            os.mkdir(get_sap_dir())

        if not os.path.exists(self.cache_dir):
            logger.info("making sap cache directory at %s", self.cache_dir)
            os.mkdir(self.cache_dir)

    def savex(self):
        data = {
            "packages": self.packages
        }
        logger.info("saving target file to %s", self.file)
        with open(self.file, "w") as fh:
            json.dump(data, fh, indent=2)

    def install_package(self, package, output_path=None):
        if not output_path:
            output_path = package.name

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        try:
            existing = self.manifest.get_package_by_name(package.name)
            if existing.version > package.version:
                if not self.yes:
                    get_yn(
                        ("are you sure you want to install an older (%s) "
                         "version over a newer (%s) one?") %
                        (package.version, existing.version),
                        exit_on_n=True)
            self.remove_package(existing)
        except:
            existing = None

        logger.info("downloading %s (%s)", package.name, package.version)
        zpath = self.server.get_package_zip(
            package.name, package.version)
        extract_zipfile(output_path, zpath)
        self.manifest.add_package(package)


    def install_package_by_name(self, name, version=None, output_path=None):
        # fetch package from server, overwrite path, load it
        data = self.server.get_package_data(name, version)
        package = TargetPackage.from_data(data)
        self.install_package(package, output_path=output_path)



    def remove_package(self, package):
        self.manifest.remove_package(package)


def create_zipfile(output_path, file_paths):

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zfh:
        for fp in file_paths:
            zfh.write(fp)

def extract_zipfile(output_path, zip_path):

    with zipfile.ZipFile(zip_path, "r") as zfh:
        zfh.extractall(output_path)


def cmp(a, b):
    """ trick to get python3 working with cmp """
    return (a > b) - (a < b)


def do_save(args):
    target = Target(args.file, yes=args.yes)
    current_date = get_date_string()
    for pname in args.packages:
        name, version = Package.get_name_version(pname)
        logger.info("saving %s (%s)", name, version or "latest")
        target.install_package_by_name(name, version, args.path)



def do_install(args):
    pass


def do_source_add(args):

    source = Source(args.file, yes=args.yes)

    args.package = Package.clean_name(args.package)
    if args.package in source.package_names:
        if not args.yes:
            get_yn(
                "package (%s) already exists, overwrite?" % args.package,
                exit_on_n=True)
        return do_source_update(args)

    package = SourcePackage(
        name=args.package,
        version=args.version or "0.0.1",
        path=args.path,
        patterns=args.pattern or ["**"],
        modified=get_date_string(),
        created=get_date_string(),
        root_dir=source.dir
    )

    source.add_package(package)


def do_source_rm(args):

    source = Source(args.file, yes=args.yes)
    if args.packages:
        for package in args.packages:
            source.rm_package(package, local=args.local)
    else:
        if not args.yes:
            get_yn("remove all packages?", exit_on_n=True)
        for package in source.package_names:
            source.rm_package(package, local=args.local)


def do_source_update(args):

    source = Source(args.file, yes=args.yes)

    args.package = Package.clean_name(args.package)

    try:
        package = source.get_package_by_name(args.package)
    except:
        logger.error(
            "package not found (%s), did you mean add?",
            args.package)
        return
    package.path = args.path or package.path
    package.modified = get_date_string()
    package.version = args.version or package.version
    package.patterns = args.pattern or package.patterns
    package.verify()
    source.update_package(package)


def find_files(path, patterns=["**"]):
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
                #print(re, fname)
                m = pre.match(fname)
                if m:
                    file_list.append(fname)
                    logger.debug("MATCH: %s", fname)

    return file_list


def get_linux_path(path):
    return path.replace("\\", "/")


def get_relpath(path):
    if path.startswith("./"):
        return path[2:]
    return path


def get_sap_dir():
    return os.path.join(os.path.expanduser("~"), ".sap")


def get_date_string():
    dt = datetime.datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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


def get_json_data(path):

    data = {}
    with open(path) as fh:
        data = json.load(fh)
    return data


def get_json_data_package(data, package_name):
    for package in data.get("packages"):
        if package["name"].lower() == package_name.lower():
            return package
    return None


def get_curdir():
    return os.path.abspath(os.curdir)


def get_source_file_dir(source_file):
    return os.path.dirname(os.path.abspath(source_file))


def get_yn(message, exit_on_n=False):
    message = "%s [Y/n]" % message
    yn = get_input(message, default="n").lower()
    if yn in ["y", "yes"]:
        return True
    if exit_on_n:
        sys.exit()
    return False


def main():
    #print(find_files(path="../../", patterns=["*"]))
    root_dir = get_curdir()
    default_server = os.environ.get("SAP_SERVER", "localhost")
    default_source_path = os.path.join(root_dir, "sap-source.json")
    default_target_path = os.path.join(root_dir, "sap.json")
    parser = argparse.ArgumentParser(description="Interact with libget")
    parser.add_argument(
        "-s", "--server", help="the server to use [env LIBGET_SERVER], default: %s" %
        default_server, default=default_server)
    parser.add_argument(
        "--target-file", help="the target libget.json file, default: %s" %
        default_target_path, default=default_target_path)
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="force yes or default on questions")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase logging output")

    subparsers = parser.add_subparsers()

    # Source
    source_p = subparsers.add_parser(
        "source", help="add, remove, or push source libraries")
    source_sub = source_p.add_subparsers()

    source_add = source_sub.add_parser(
        "add", help="adds a package to server and source file")
    source_push = source_sub.add_parser(
        "push", help="pushes source file to server")
    source_rm = source_sub.add_parser(
        "rm", aliases=["remove"], help="removes a package from server and source file")
    source_up = source_sub.add_parser(
        "up", aliases=["update"], help="update a package")

    for sub_cmd in [source_push, source_rm]:
        sub_cmd.add_argument(
            "packages", nargs="*",
            help="the package name, leave blank to use source-file")

    for sub_cmd in [source_add, source_up]:
        sub_cmd.add_argument("package", help="the package name")
        sub_cmd.add_argument(
            "path", help="the path of the package, relative to SOURCE_FILE path")
        sub_cmd.add_argument(
            "-p", "--pattern", action="append",
            help=("a glob pattern for files inside PATH, "
                  "defaults to '**', can add multiple -p args"))
        sub_cmd.add_argument(
            "-l", "--local", action="store_true",
            help="add package to source file only (no server)")
        sub_cmd.add_argument(
            "-v", "--version", help="package version, defaults to 0.0.1")

    for sub_cmd in [source_add, source_up, source_rm]:
        sub_cmd.add_argument(
            "-f", "--file", default=default_source_path,
            help="the sap SOURCE file location, defaults to: %s" %
            default_source_path)

    # Source add
    source_add.set_defaults(func=do_source_add)

    # Source rm
    source_rm.add_argument(
        "-l", "--local", action="store_true",
        help="remove package from source file only (no server)")
    source_rm.add_argument(
        "-v", "--version",
        help="removes only this version, does nothing with --local")
    source_rm.set_defaults(func=do_source_rm)

    # Source update
    source_up.set_defaults(func=do_source_update)

    # Target
    target_save = subparsers.add_parser(
        "save", help="installs a libget package")
    target_save.add_argument(
        "packages", nargs="*",
        help="package to get, leave blank to use target file")
    target_save.add_argument(
        "-p", "--path", help="relative path to install package")

    target_save.set_defaults(func=do_save)


    for sub_cmd in [target_save]:
        sub_cmd.add_argument(
            "-f", "--file", default=default_target_path,
            help="target file location, defaults to %s" %
            default_target_path)

    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("root dir is %s", root_dir)
        logger.debug("set to verbose output")

    args.func(args)


if __name__ == "__main__":
    main()
