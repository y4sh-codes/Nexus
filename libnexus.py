import argparse  # To parse command-line arguments
import configparser  # To read and write these files
from datetime import datetime  # For Date/Time manipulation
import grp  # To read the group database on Unix/Linux
import pwd  # To read the users database on Unix/Linux
from fnmatch import fnmatch  # To match filenames against patterns for .gitignore file
import os  # For filesystem abstraction 
import hashlib  # To use SHA-1 function which is used by Git
from math import ceil 
import re  # For some regular expressions
import sys  # To access actual command-line arguments
import zlib  # To compress files and folders

argparser = argparse.ArgumentParser(description="Version Control System")

argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

class NexusRepository (object):
    """ A nexus repository """
    worktree = None
    nexusdir = None
    conf = None

    def __init__ (self, path, force=False):
        self.worktree = path
        self.nexusdir = os.path.join(path, ".nexus")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a Nexus repository{path}")

        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            ver = int(self.conf.get("core", "repositoryformatversion"))
            if ver != 0:
                raise Exception("Unsupported repositoryformatversion: {vers}")  
            
def repo_dir(repo, *path, mkdir=False):
    """Same as repo_path, but mkdir *path if absent if mkdir."""

    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
    else:
        raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None
        
def repo_file(repo, *path, mkdir=False):

    """Same as repo_path, but create dirname(*path) if absent.  For
    example, repo_file(r, \"refs\", \"remotes\", \"origin\", \"HEAD\") will create
    .nexus/refs/remotes/origin.""" 

    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)
        
def repo_path(repo, *path):
    """ Compute path under repo's nexusdir """ 
    return os.path.join(repo.nexusdir, *path)

def repo_create(path):
    """ Create a new repository at path """

    repo = NexusRepository(path, True)

    # Firstly we would make sure either the path doesn't exist or is an empty dir

    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory")
        if os.path.exists(repo.nexusdir) and os.listdir(repo.nexusdir):
            raise Exception(f"{path} is not empty")
        
    else:
        os.makedirs(repo.worktree)
        
    assert repo_dir(repo, "branches", mkdir = True)
    assert repo_dir(repo, "objects", mkdir=True)
    assert repo_dir(repo, "refs", "tags", mkdir=True)
    assert repo_dir(repo, "refs", "heads", mkdir=True)

    #.nexus/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

    #.nexus/HEAD
    with open(repo_file(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")
        
    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)

        return repo    
    
def repo_default_config():
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret    
    
argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")

argsp.add_argument(metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repository.")

def cmd_init(args):
    repo_create(args.path)

def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, ".nexus")):
        return NexusRepository(path)

    parent = os.path.realpath(os.path.join(path, ".."))

    if parent == path:
        if required:
            raise Exception("No nexus directory.")
        else:
            return None

    return repo_find(parent, required)