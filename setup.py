import setuptools

NAME = "gmshairfoil2d"
VERSION = "0.0.1"
AUTHOR = "Aidan Jungo"
EMAIL = "aidan.jungo@cfse.ch"
DESCRIPTION = "Python tool to genreate 2D mesh around an airfoil"
LONG_DESCRIPTION = "Python tool to genreate 2D mesh around an airfoil."
URL = ""
REQUIRES_PYTHON = ">=3.6.0"
REQUIRED = []
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
    url=URL,
    include_package_data=True,
    package_dir={"": PACKAGE_DIR},
    license=LICENSE,
    packages=[NAME],
    python_requires=REQUIRES_PYTHON,
    keywords=["airfoil", "2D", "gmsh"],
    install_requires=REQUIRED,
    # See: https://pypi.org/classifiers/
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
)
