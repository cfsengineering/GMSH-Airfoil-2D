# GMSH-Airfoil-2D

Python tool to genreate 2D mesh around an airfoil with [GMSH](https://gmsh.info/).



## Installation

You can clone and install this repository with the following commands:

```bash
    git clone https://github.com/cfsengineering/GMSH-Airfoil-2D.git
    cd GMSH-Airfoil-2D
    pip install -e .
```

## Usage

TODO: copy/paste the help of the `gmsh_airfoil_2d` here.


## Examples

To check all airfoil available in the [database](https://m-selig.ae.illinois.edu/ads/coord_database.html):

```bash
    python gmsh_airfoil_2d.py --list
```

To create a circular farfield mesh around a NACA0012 of 10m or radius:
(by defauld the chord of the lenght is 1 meter)

```bash
    python gmsh_airfoil_2d.py --naca 0012 --farfield 10
```

To create a circular farfield mesh around a Drela DAE11 airfoil (the name in the database is "dae11") of 20m or radius:

```bash
    python gmsh_airfoil_2d.py --airfoil dae11 --farfield 20
```


To create a box mesh around a Eppler E220 airfoil (the name in the database is "e211") of 10x4m (lenght x hight):

```bash
    python gmsh_airfoil_2d.py --airfoil e211 --box 10x4
```

To create a box mesh of 15x6m (lenght x hight) around a NACA 2312 airfoil placed with an angle of 8 degrees:

```bash
    python gmsh_airfoil_2d.py --naca 2312 -- aoa 8 --box 10x4
```




