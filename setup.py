from pathlib import Path
import setuptools
import os

NAME = "gmshairfoil2d"
VERSION = "0.1.1"
AUTHOR = "Aidan Jungo"
EMAIL = "aidan.jungo@cfse.ch"
DESCRIPTION = "Python tool to genreate 2D mesh around an airfoil"
LONG_DESCRIPTION = open("README.md").read()
URL = "https://github.com/cfsengineering/GMSH-Airfoil-2D"
REQUIRES_PYTHON = ">=3.6.0"

thelibFolder = Path(__file__).parent
requirementPath = Path(thelibFolder, "requirement.txt")

REQUIRED = []
if os.path.isfile(requirementPath):
    with open(requirementPath) as f:
        REQUIRED = f.read().splitlines()

README = "README.md"
PACKAGE_DIR = "."
LICENSE = "Apache License 2.0"
SCRIPTS = [str(Path("src/bin/gmshairfoil2d"))]

setuptools.setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url=URL,
    include_package_data=True,
    package_dir={"": PACKAGE_DIR},
    license=LICENSE,
    packages=[NAME],
    python_requires=REQUIRES_PYTHON,
    scripts=SCRIPTS,
    keywords=["airfoil", "2D", "mesh", "cfd", "gmsh"],
    install_requires=REQUIRED,
    # See: https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
