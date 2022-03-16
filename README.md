# GMSH-Airfoil-2D

Python tool to genreate 2D unstructured mesh around an airfoil with [GMSH](https://gmsh.info/) in one command line.


## Installation

You can clone and install this repository with the following commands:

```bash
git clone https://github.com/cfsengineering/GMSH-Airfoil-2D.git
cd GMSH-Airfoil-2D
pip install -e .
```

## Usage

```text
python run_gmsh_airfoil_2d.py -h                                    

optional arguments:
  -h, --help                  show this help message and exit
  --list                      Display all airfoil available in the database :
                              https://m-selig.ae.illinois.edu/ads/coord_database.html
  --naca [4DIGITS]            NACA airfoil 4 digit (default 0012)
  --airfoil [NAME]            Name of an airfoil profile in the database (database available with
                              the --list argument)
  --aoa [AOA]                 Angle of attack [deg] (default: 0 [deg])
  --farfield [RADIUS]         Create a circular farfield mesh of given radius [m] (default 10m)
  --box [LENGTHxWIDTH]        Create a box mesh of dimensions [length]x[height] [m]
  --airfoil_mesh_size [SIZE]  Mesh size of the airfoil countour [m] (default 0.01m)
  --ext_mesh_size [SIZE]      Mesh size of the external domain [m] (default 0.2m)
  --format [FORMAT]           format of the mesh file, e.g: msh, vtk, wrl, stl, mesh, cgns, su2,
                              dat (default su2)
  --output [PATH]             output path for the mesh file (default : current dir)
  --ui                        Open GMSH user interface to see the mesh

```


## Examples of use:

To check all airfoil available in the [database](https://m-selig.ae.illinois.edu/ads/coord_database.html):

```bash
python run_gmsh_airfoil_2d.py --list
```

For all the following examples, the defauld chord lenght is 1 meter.

To create a circular farfield mesh around a NACA0012 of 10m of radius and see the result with GMSH user interface:

```bash
python run_gmsh_airfoil_2d.py --naca 0012 --farfield 10 --ui
```

![GMSH user interface with the 2D mesh](images/example_mesh.png)


To create a circular farfield mesh around a Drela DAE11 airfoil (the name in the database is "dae11") of 20m or radius with a mesh size of 0.005m on the airfoil:

```bash
python run_gmsh_airfoil_2d.py --airfoil dae11 --farfield 20 --airfoil_mesh_size 0.005
```

To create mesh around a Eppler E220 airfoil (the name in the database is "e211") with an angle of attack of 8 degree in a box of 12x4m (lenght x hight) and save it as a vtk mesh and see the result with GMSH user interface:

```bash
python run_gmsh_airfoil_2d.py --airfoil e211 --aoa 8 --box 12x4 --format vtk --ui
```

![GMSH user interface with the 2D mesh, rectangular box](images/example_mesh_box.png)