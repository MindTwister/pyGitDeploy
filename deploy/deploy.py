#!/usr/bin/env python

# Preliminaries
# -------------
from __future__ import print_function
# [GitPython](http://packages.python.org/GitPython/0.3.1/reference.html)
from git import *
import getpass
import ftplib
import sys
import os
import getopt

# Attempt to import readline, if available we will use that
# [readline](http://docs.python.org/library/readline.html?highlight=readline#readline)
# is not available outside of unix.
try:
    import readline
    gotReadline = True
except ImportError:
    gotReadline = False


# Deploy
# ======
class Deploy:
    def __init__(self, verbosity=0, dry=False, path=""):
        self.deletedFiles = []
        self.updatedFiles = []
        self.verbose = verbosity
        self.dry = dry
        # Repo will first attempt to find .git in the cwd, then work its way up
        self.repo = Repo(path)
        # We change dir to the repo working dir so file references we get from
        # the repo makes sense.
        os.chdir(self.repo.working_dir)
        self.configReader = self.repo.config_reader()

    def setVerbose(self, verbose):
        self.verbose = verbose

    # Wrap raw_input/readline to show default values
    def raw_input_default(self, prompt, default):
        # If we have readline, insert the default text after prompting
        # this way the user can delete the default and replace it
        if gotReadline:
            def pre_input_hook():
                readline.insert_text(default)
                readline.redisplay()

            readline.set_pre_input_hook(pre_input_hook)
            try:
                return raw_input(prompt)
            finally:
                readline.set_pre_input_hook(None)
        # If we do not have readline, prompt for text with the default
        # value placed in square braces imediately behind it. If we get
        # an empty string back, set the returned value to the default
        else:
            if(default != ""):
                prompt = "[" + default + "] " + prompt

            val = raw_input(prompt)
            if val == "":
                val = default
            return val

    # Use git to check for files changed since last deploy.
    def checkFiles(self, deployVersion):

        self.deployVersion = self.repo.commit(deployVersion).name_rev.split(" ")[0]

        # Check the config and see if a last deployment exists
        if self.configReader.has_option("ftp", "lastDeploy"):
            lastDeploy = self.configReader.get_value("ftp", "lastDeploy")
            # Create a diff of changes between last deploy and current HEAD
            changes = self.repo.commit(lastDeploy).diff(deployVersion)
        # In case no previous deployments exists
        else:
            self.out("No previous deployments, adding all files", verbosity=0)
            # Grab all files in the repo
            for file in Git(self.repo.working_dir).ls_files().split("\n"):
                self.out("  ", file, verbosity=4)
                self.updatedFiles.append(file)
            return

        # Iterate through all changes, using [iter_change_type](http://packages.python.org/GitPython/0.3.1/reference.html#git.diff.DiffIndex)
        # to keep track of whats what
        self.out("Added files:")
        for fileAdded in changes.iter_change_type('A'):
            self.out("  ", fileAdded.b_blob.path)
            self.updatedFiles.append(fileAdded.b_blob.path)

        self.out("Updated files")
        for fileUpdated in changes.iter_change_type('M'):
            self.out("  ", fileUpdated.a_blob.path)
            self.updatedFiles.append(fileUpdated.a_blob.path)

        self.out("Deleted files")
        for fileDeleted in changes.iter_change_type('D'):
            self.out("  ", fileDeleted.a_blob.path)
            self.deletedFiles.append(fileDeleted.a_blob.path)

        self.out("Renamed files")
        for fileRenamed in changes.iter_change_type('R'):
            self.out("  From: ", fileRenamed.a_blob.path, " to ", fileRenamed.b_blob.path)

    # Setup FTP settings
    def connectFTP(self, rebuild_config=False):

        # The following checks the config file for already set values.
        #
        # If the value is not found the user will be prompted for information.
        if self.configReader.has_option("ftp", "remoteServer"):
            self.remoteServer = self.configReader.get_value("ftp", "remoteServer")
        else:
            default = ""
            if rebuild_config:
                default = self.remoteServer
            self.remoteServer = self.raw_input_default("Server: ", default)

        if self.configReader.has_option("ftp", "remoteUser"):
            self.remoteUser = self.configReader.get_value("ftp", "remoteUser")
        else:
            default = ""
            if rebuild_config:
                default = self.remoteUser
            self.remoteUser = self.raw_input_default("Username: ", default)

        self.savePass = False

        if self.configReader.has_option("ftp", "remotePassword"):
            self.remotePassword = self.configReader.get_value("ftp", "remotePassword")
            self.savePass = True
        else:
            self.remotePassword = getpass.getpass("Password: ")

        if self.configReader.has_option("ftp", "remoteDir"):
            self.remoteDir = self.configReader.get_value("ftp", "remoteDir")
        else:
            default = ""
            if rebuild_config:
                default = self.remoteDir
            self.remoteDir = self.raw_input_default("Remote directory: ", default)

        if(self.configReader.has_option("ftp", "savePass") == False and not self.configReader.has_option("ftp", "remotePassword")):
                if raw_input("Save password (y/n):").lower() == "y":
                    self.savePass = True

        # Trim the remote dir of slashes the first slash will be prepended by the system.
        # This means that all remote directories must be absolute.
        while self.remoteDir.startswith("/"):
            self.remoteDir = self.remoteDir[1:]

        while self.remoteDir.endswith("/"):
            self.remoteDir = self.remoteDir[:-1]

        # Attempt to connect to the remote ftp server and change directory to the specified
        # remote folder.
        try:
            self.ftp = ftplib.FTP(self.remoteServer, self.remoteUser, self.remotePassword)
            self.ftp.cwd("/" + self.remoteDir)
        except ftplib.all_errors as connectionError:
            self.out("Error connecting to server: ", connectionError, verbosity=0)
            if raw_input("Retry (y/n)?: ").lower() == "y":
                self.connectFTP(True)
            else:
                exit(255)

        self.rootFolder = self.remoteDir

    # Parse folders from the changed files
    def parseDirectories(self):
        self.dirs = {}
        # Run through each updated file and generate a dictionary tree of expected remote folders
        for file in self.updatedFiles:
            dirs = file.split('/')[:-1]
            cwd = self.dirs
            for dir in dirs:
                if dir not in cwd:
                    cwd[dir] = {}

                cwd = cwd[dir]

    # Check remote for expected folders
    def checkDirectories(self, cwd="", folders={}):
        # Instead of keeping track of nesting levels etc, we use absolute paths on the remote server.
        if cwd == "":
            cwd = "/" + self.rootFolder
            folders = self.dirs
        if self.ftp:
            self.out("Checking folders under", cwd)

            for dir, subFolders in folders.iteritems():
                self.out("Checking ", cwd + "/" + dir)
                # To test for the remote directory we use the tried and tested "better to ask forgiveness"
                try:
                    self.ftp.cwd(cwd + "/" + dir)
                except:
                    self.out("Creating previously non-existing folder", cwd + "/" + dir, verbosity=0)
                    if not self.dry:
                        self.ftp.mkd(cwd + "/" + dir)
                # Recursively check the sub-folders of the current folder
                self.checkDirectories(cwd + "/" + dir, subFolders)

            if cwd == "/" + self.rootFolder:
                self.ftp.cwd(cwd)

    # Delete remote files if they have been deleted from the repository
    def deleteFiles(self):
        for file in self.deletedFiles:
            self.out("Deleting ", file, verbosity=0)
            if not self.dry:
                try:
                    self.ftp.delete(file)
                except:
                    self.out("Error: ", file, " did not exist online, could have been deletet by other means", verbosity=0)

    # Upload local files to remote
    def uploadFiles(self):
        for file in self.updatedFiles:
            self.out("Uploading", file, verbosity=0)
            if not self.dry and os.path.isfile(file):
                self.ftp.storbinary("STOR " + file, open(file, 'rb'))
            elif not self.dry and os.path.isdir(file):
                try:
                    self.ftp.mkd(file)
                except:
                    #sumodule folder allready exists
                    pass

    def handleSubmodules(self):
        base = os.getcwd()
        for subModule in self.repo.submodules:
            path = os.path.join(base, subModule.path)
            dep = Deploy(verbosity=self.verbose, dry=self.dry, path=path)
            dep.ftp = self.ftp
            dep.rootFolder = self.rootFolder + '/' + subModule.path
            dep.checkFiles(args["commit"])
            dep.parseDirectories()
            dep.checkDirectories()
            dep.deleteFiles()
            dep.uploadFiles()
            dep.updateLast()
            try:
                dep.handleSubmodules()
            except:
                pass

    def updateLast(self):
        infoWriter = self.repo.config_writer()
        if not self.dry:
            infoWriter.set_value('ftp', 'lastDeploy', self.deployVersion)

    def saveConfig(self):
        infoWriter = self.repo.config_writer()
        infoWriter.set_value('ftp', 'remoteUser', self.remoteUser)
        infoWriter.set_value('ftp', 'remoteDir', self.remoteDir)
        infoWriter.set_value('ftp', 'remoteServer', self.remoteServer)
        if self.savePass:
            infoWriter.set_value('ftp', 'remotePassword', self.remotePassword)

    def out(self, *args, **kwargs):
        try:
            verbosity = kwargs["verbosity"]
        except:
            verbosity = 5
        if self.verbose >= verbosity:
            for a in args:
                if a != "":
                    print(a, end=" ")
            print("")


def main():

    args = {
        "dry": False,
        "commit": "HEAD",
        "verbose": 1
    }

    options, arguments = getopt.getopt(sys.argv[1:], "vn", ["dry-run", "verbose"])
    if len(arguments):
        args["commit"] = arguments[0]
    else:
        args["commit"] = "HEAD"

    for option, value in options:
        if option in ("-n", "--dry-run"):
            args["dry"] = True

        if option in ("-v", "--verbose"):
            if value == "":
                value = 5
            args["verbose"] = value

    deploy = Deploy(path=os.getcwd(), verbosity=args["verbose"], dry=args["dry"])

    deploy.checkFiles(args["commit"])
    deploy.parseDirectories()
    deploy.connectFTP()
    deploy.checkDirectories()
    deploy.deleteFiles()
    deploy.uploadFiles()
    deploy.saveConfig()
    deploy.updateLast()
    deploy.handleSubmodules()

__all__ = ("Deploy", "main")
if __name__ == "__main__":
    main()
