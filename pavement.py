from paver.easy import *
from paver.setuputils import setup

setup(
    name="pyGitDeploy",
    packages=["deploy"],
    version="0.6",
    url="https://github.com/MindTwister/pyGitDeploy",
    author="Kristoffer Sall Hansen",
    author_email="kristoffer@sallhansen.dk",
    entry_points={
        'console_scripts': [
        'git-deploy = deploy.deploy:main']
    },
    install_requires=["gitpython"]
    )
