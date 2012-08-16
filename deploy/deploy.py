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
import json
import tempfile
from fnmatch import fnmatch
# See [[config]]
from .config import *

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
    def __init__(self, verbosity=0, dry=False, path="", target=""):
        self.deletedFiles = []
        self.updatedFiles = []
        self.verbose = verbosity
        self.dry = dry
        self.target = target
        # Repo will first attempt to find .git in the cwd, then work its way up
        self.repo = Repo(path)
        # We change dir to the repo working dir so file references we get from
        # the repo makes sense.
        os.chdir(self.repo.working_dir)
        self.configReader = ConfigReader(target)
        self.configGlobal = ConfigReader()
        self.ignored = []
        #Attempt to retrieve ignored files from the config file
        if self.configGlobal.has_option("global", "ignore"):
            self.ignored = json.loads(self.configGlobal.get_value("global", "ignore"))
        #Always ignore deploy.cfg
        self.ignored.append("deploy.cfg")

    def setVerbose(self, verbose):
        self.verbose = verbose

    # Use [glob](https://en.wikipedia.org/wiki/Glob_(programming)) matching to check if a file
    # is in the ignore list.
    def is_ignored(self, file):
        return (True in [fnmatch(file, pattern) for pattern in self.ignored])

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
        def storVersion(v):
            self.lastDeploy = v

        self.deployVersion = self.repo.commit(deployVersion).name_rev.split(" ")[0]
        #Attempt to read deployed version from online
        try:
            self.ftp.retrlines("RETR lastDeploy", storVersion)
        except:
            self.lastDeploy = None

        if self.lastDeploy != None:
            # Create a diff of changes between last deploy and current HEAD
            changes = self.repo.commit(self.lastDeploy).diff(deployVersion)
        # In case no previous deployments exists
        else:
            self.out("No previous deployments, adding all files", verbosity=0)
            # Grab all files in the repo
            for file in Git(self.repo.working_dir).ls_files().split("\n"):
                if self.is_ignored(file):
                    self.out("File:", file, "is ignored")
                    continue
                self.out("  ", file, verbosity=4)
                self.updatedFiles.append(file)
            return

        # Iterate through all changes, using [iter_change_type](http://packages.python.org/GitPython/0.3.1/reference.html#git.diff.DiffIndex)
        # to keep track of whats what
        self.out("Added files:")
        for fileAdded in changes.iter_change_type('A'):
            if self.is_ignored(fileAdded.b_blob.path):
                self.out("File:", fileAdded.b_blob.path, "is ignored")
                continue
            self.out("  ", fileAdded.b_blob.path)
            self.updatedFiles.append(fileAdded.b_blob.path)

        self.out("Updated files")
        for fileUpdated in changes.iter_change_type('M'):
            if self.is_ignored(fileUpdated.b_blob.path):
                self.out("File:", fileUpdated.b_blob.path, "is ignored")
                continue
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
        # Check the config file for already set values.
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

    #Upload files from submodules by creating new deploys
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

    #Handle renaming target specific files
    def handleRename(self):
        self.ftp.cwd('/' + self.remoteDir)
        #Check for `target_specific_files` in the config file
        #This is a json object of the form { name1 : replacement1, name2 : replacement2 }
        if self.configReader.has_option("ftp", "target_specific_files"):
            swapMap = json.loads(self.configReader.get_value("ftp", "target_specific_files"))
            for original, replacement in swapMap.iteritems():
                #Check if either the original or the replacement exists in the list
                #of updated files.
                if replacement in self.updatedFiles or original in self.updatedFiles:
                    self.out("Replacing", original, "with", replacement, verbosity=0)
                    if not self.dry and os.path.isfile(original) and os.path:
                        #Delete the original file
                        self.ftp.delete(original)
                        #If the replacement does not exist online, upload it
                        try:
                            self.ftp.size(replacement)
                        except:
                            self.ftp.storbinary("STOR " + replacement, open(replacement, 'rb'))
                        #Rename the replacement file to the original
                        self.ftp.rename(replacement, original)

    #Update the last deployment in the config file
    def updateLast(self):
        #Create a temporary file to store the latest deployed version
        (handle, fileName) = tempfile.mkstemp()
        os.write(handle,self.deployVersion)
        os.close(handle)
        if not self.dry:
            #Upload the temporary file to the ftp server
            self.ftp.storbinary("STOR lastDeploy", open(fileName, 'rb'))
        #Clean up after ourselves
        os.remove(fileName)



    def saveConfig(self):
        infoWriter = ConfigWriter(self.target)
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
        args["target"] = arguments[0]
    else:
        args["target"] = ""

    for option, value in options:
        if option in ("-n", "--dry-run"):
            args["dry"] = True

        if option in ("-v", "--verbose"):
            if value == "":
                value = 5
            args["verbose"] = value

    deploy = Deploy(path=os.getcwd(), verbosity=args["verbose"], dry=args["dry"], target=args["target"])

    deploy.connectFTP()
    deploy.checkFiles("HEAD")
    deploy.parseDirectories()
    deploy.checkDirectories()
    deploy.deleteFiles()
    deploy.uploadFiles()
    deploy.saveConfig()
    deploy.handleSubmodules()
    deploy.handleRename()
    deploy.updateLast()

__all__ = ("Deploy", "main")
if __name__ == "__main__":
    main()
