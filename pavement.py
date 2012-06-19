from paver.easy import *


@task
def generate():
    """Generate github pages"""
    sh("rm -rf build deploy dist pyGitDeplooy.egg-info")
    sh("rm -rf .gitattributes .gitignore")
    sh('rm paver-minilib.zip deploy.cfg *.md setup.py')
    sh("cd docs")
    sh('mv * ..')
    sh("cd ..")
    sh("mv deploy.html index.html")
    sh('rm -rf docs')
