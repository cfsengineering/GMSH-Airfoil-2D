from pathlib import Path
import setuptools

NAME = "gmshairfoil2d"
VERSION = "0.2"
AUTHOR = "Giacomo Benedetti"
EMAIL = "giacomo.benedetti@cfse.ch"
DESCRIPTION = "Python tool to generate 2D mesh around an airfoil"
LONG_DESCRIPTION = open("README.md").read()
URL = "https://github.com/cfsengineering/GMSH-Airfoil-2D"
REQUIRES_PYTHON = ">=3.11.0"

lib_dir = Path(__file__).parent
requirement_path = Path(lib_dir, "requirement.txt")

REQUIRED = []
if requirement_path.is_file():
    with open(requirement_path) as f:
        REQUIRED = f.read().splitlines()

README = "README.md"
PACKAGE_DIR = "."
LICENSE = "Apache License 2.0"

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
    entry_points = {
        "console_scripts": ['gmshairfoil2d = gmshairfoil2d.gmshairfoil2d:main']
        },
    keywords=["airfoil", "2D", "mesh", "cfd", "gmsh"],
    install_requires=REQUIRED,
    # See: https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
