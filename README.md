pyGitDeploy
===========

A script for rapid deployment to FTP servers.
The script uses git to find changes since last deployment and applies the changes to an FTP server, if no previous deployment has been made it uploads all watched files.


Rationale
-----
Most shared hosting environments dont allow ssh, let alone git. To make sure all relevant changes are uploaded when your project reaches its next iteration this script runs a diff between your last deployment and current HEAD then syncs those changes with an FTP server.


New in version:
-----
### 0.6.1 ###
* Deploying using a diff from a specific commit was not as useful as hoped, instead you can supply a named target
* Config has been moved outside of the git folder and into the repo root
*	Config now has a `global` section
	*	Global section has an `ignore` option, this takes the form of a list of files to ignore for upload

### 0.6 ###
* Major rewrite, now uses [Paver](https://github.com/paver/paver)
* Documentation overhaul in the works using [Pycco](https://github.com/fitzgen/pycco)

### 0.5.6 ###
* Now handles submodules

### 0.5.5.4 ###
* Fix bug #4 "Crashes when not run from repo root"

### 0.5.1 - 0.5.5.3 ###
* Default/previous values should now be presented correctly.
* Fixed an issue with binary files, all files are now treated as binary.
* Fixed a bloody stupid mistake when retrieving the hex of the current HEAD
* Now actually deletes the files
* Updated the way the script handles no previous commits (grabs all files with `git ls-files`)
* Verbosity now a parameter
* Added -n or --dry-run for a simulated run (no upload, no directories created remotely)
* More verbosity
* Made it possible to specify a specific state to deploy (in preperation for `git deploy --revert`)
* Better format for default values
* Retains previously input values as default (except for password)

### 0.5 ###
* Now actually saves remote information

Requirements:
-----
* [Git](http://git-scm.com/)
* [Python](http://www.python.org/)
* [GitPython](http://packages.python.org/GitPython/0.3.1/index.html)

Installation:
-------------
Clone the repo from github, then

	paver install

Or

	python setup.py install

Usage:
------
Assuming python and this script is in your path:

    git deploy

The script will prompt you for ftp details and start the deployment process.
    
Advanced:

    git deploy [-v <level>| --verbose <level>] [-n | --dry-run] <target>

* **--dry-run**

  **-n**

 Runs the script without making any remote changes, only saves configuration and tells you what it would have done

* **--verbose**

 **-v**
 
 Runs in verbose mode, the optional parameter specifies _how_ verbose it should be, 0-5
  
  

Target is a named target server, the config file will keep track of individual targets and deployments

Tested environments:
--------------------
### Windows versions: ###
* Windows 7

### Linux versions: ###
* Mint 11-12
* Ubuntu 10+

### Python versions: ###
* 2.7.1

If you have used this script anywhere else with success feel free to send me a message and I will update this document.


Todo for version 1:
-------------------

* Add active or passive mode to configuration options
* Add `--revert` to quickly go back to last deployment
* Bind a specific branch to a named deployment to merge config changes. (merge staging branch with current THEN upload)
* Verbosity levels (_work in progress_)
* Document command line options

Thanks:
-------
[Adeodato Simó](http://martirioenbenidorm.blogspot.com/) for [raw_input with editable default](http://chistera.yi.org/~dato/blog/entries/2008/02/14/python_raw_input_with_an_editable_default_value_using_readline.html)
