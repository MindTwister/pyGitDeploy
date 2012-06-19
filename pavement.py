from paver.easy import *


@task
def generate():
    """Generate github pages"""
    sh("git checkout master -- deploy/deploy.py deploy/config.py")
    sh("mv deploy/*.py .")
    sh("pycco *.py")
    sh("mv docs/* .")
    sh("mv deploy.html index.html")
    sh("rm deploy.py config.py pavement.html")
    sh("rm -rf docs/ deploy/")
