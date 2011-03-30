pyGitDeploy
===========

A script for rapid deployment to FTP servers.
The script uses git to find changes since last deployment and applies the changes to an FTP server, if no deployment has been made it uploads all watched files.


New in version:
-----
### 0.5.3 ###
* More verbosity

### 0.5.2 ###
* Made it possible to specify a specific state to deploy (in preperation for `git deploy --revert`)

### 0.5.1 ###
* Better format for default values
* Retains previously input values as default (except for password)

### 0.5 ###
* Now actually saves remote information

Requirements:
-----
* [Git](http://git-scm.com/)
* [Python](http://www.python.org/)
* [GitPython](http://packages.python.org/GitPython/0.3.1/index.html)

Usage:
------
Assuming python and this script is in your path:

    git pydeploy
    
Advanced:

    git deploy <commit>

When specifying which commit to deploy the script will still only compare to what is online and make the changes aka. diff works both ways.
    
The script will

Tested environments:
--------------------
### Windows versions: ###
* Windows 7

### Python versions: ###
* 2.7.1

If you have used this script anywhere else with success feel free to send me a message and I will update this document.


Todo:
--------

* Remove deleted files since last commit
* Add active or passive mode to configuration options
* Add `--revert` to quickly go back to last deployment
* Add named deployments
 * Named deployments should work as aliases for different servers; `git deploy staging` `git deploy production`
* Bind a specific branch to a named deployment to merge config changes. (merge staging branch with current THEN upload)
* Make the verbosity optional

Thanks:
-------
[Adeodato Simó](http://martirioenbenidorm.blogspot.com/) for [raw_input with editable default](http://chistera.yi.org/~dato/blog/entries/2008/02/14/python_raw_input_with_an_editable_default_value_using_readline.html)