pyGitDeploy
===========

A script for rapid deployment to FTP servers

Requirements:
-----
* [Git](http://git-scm.com/)
* [Python](http://www.python.org/)
* [GitPython](http://packages.python.org/GitPython/0.3.1/index.html)

Usage:
------
Assuming python and this script is in your path

git pydeploy

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
* Make it possible to specify a specific state to deploy (in preperation for `git deploy --revert`)
* Add `--revert` to quickly go back to last deployment
* Add named deployments
 * Named deployments should work as aliases for different servers; `git deploy staging` `git deploy production`
* Bind a specific branch to a named deployment to merge config changes. (merge staging branch with current THEN upload)