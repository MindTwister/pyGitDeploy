from paver.easy import *


@task
def generate():
    """Generate github pages"""
    sh("rm -rf build deploy dist pyGitDeplooy.egg-info")
    sh("rm -rf .gitattributes .gitignore")
    sh("rm paver-minilib.zip deploy.cfg *.md setup.py")
    sh("mv docs/* .")
    sh("mv deploy.html index.html")
