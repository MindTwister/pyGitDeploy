from paver.easy import *
from paver.setuputils import setup
import os

setup(
    name="pyGitDeploy",
    packages=["deploy"],
    version="0.7.1",
    url="https://github.com/MindTwister/pyGitDeploy",
    author="Kristoffer Sall Hansen",
    author_email="kristoffer@sallhansen.dk",
    entry_points={
        'console_scripts': [
        'git-deploy = deploy.deploy:main']
    },
    install_requires=["gitpython"]
    )


@task
@needs('minilib', 'docs')
def prepare():
    """Prepares the project for commit/install"""
    pass


@task
def docs():
    """Generates the project documentation"""
    os.system("pycco deploy/*.py")


@task
def clean():
    """Clean all build files"""
    sh("rm -rf docs")
    sh("rm -rf pyGitDeploy.egg-info")
    sh("rm -rf build")
    sh("rm -rf setup.py")
    sh("rm -rf paver-minilib.zip")
