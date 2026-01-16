# Configuration File Examples

This directory contains example configuration files that correspond to the examples shown in the main README.md.

## Usage

Each config file can be used with the `--config` option:

```bash
gmshairfoil2d --config example/example1_naca0012.cfg
```

Or override specific parameters via command line:

```bash
gmshairfoil2d --config example/example1_naca0012.cfg --output ./meshes
```

## Available Examples

### Example 1: NACA0012 with circular farfield
**File:** `example1_naca0012.cfg`

Generates a circular farfield mesh around a NACA0012 airfoil without boundary layer, with GMSH UI.

Equivalent command:
```bash
gmshairfoil2d --naca 0012 --farfield 10 --ui --no_bl
```

### Example 2: DAE11 with boundary layer
**File:** `example2_dae11.cfg`

Generates a circular farfield mesh around a Drela DAE11 airfoil with boundary layer, custom mesh size on airfoil.

Equivalent command:
```bash
gmshairfoil2d --airfoil dae11 --farfield 4 --airfoil_mesh_size 0.005
```

### Example 3: E211 in box with angle of attack
**File:** `example3_e211_box.cfg`

Generates a box mesh around an Eppler E211 airfoil at 8 degrees angle of attack, without boundary layer, saved as VTK format with GMSH UI.

Equivalent command:
```bash
gmshairfoil2d --airfoil e211 --aoa 8 --box 12x4 --format vtk --ui --no_bl
```

### Example 4: CH10SM with box and boundary layer
**File:** `example4_ch10sm_bl.cfg`

Generates a box mesh around a Chuck Hollinger CH10SM airfoil with default boundary layer parameters (first layer height 3e-5, 35 layers, growth ratio 1.2), with GMSH UI.

Equivalent command:
```bash
gmshairfoil2d --airfoil ch10sm --ui --box 2x1.4
```

### Example 5: NACA4220 structured mesh
**File:** `example5_naca4220_structured.cfg`

Generates a fully structured mesh around a NACA4220 airfoil at 6 degrees angle of attack with custom mesh parameters, with GMSH UI.

Equivalent command:
```bash
gmshairfoil2d --naca 4220 --airfoil_mesh_size 0.08 --ui --structured --first_layer 0.01 --arg_struc 6x7 --aoa 6
```

### Example 6: Custom airfoil from file
**File:** `example6_custom_airfoil_flap.cfg`

Generates a box mesh around a NLR 7301 custom airfoil profile with a deflected flap at 10 degrees, without boundary layer, with GMSH UI.

Equivalent command:
```bash
gmshairfoil2d --airfoil_path tests/test_data/NLR_7301.dat --flap_path tests/test_data/Flap_NLR_7301.dat --deflection 10 --box 4x3 --ui --no_bl
```

This example demonstrates how to use custom airfoil and flap profiles from external files instead of built-in NACA or database airfoils.

## Creating Your Own Config

You can create a new config file by copying one of these examples and modifying the parameters:

```bash
cp example1_naca0012.cfg my_custom_config.cfg
# Edit my_custom_config.cfg with your favorite editor
gmshairfoil2d --config my_custom_config.cfg
```

Or generate a template with all available parameters:

```bash
gmshairfoil2d --example_config
```

For detailed information about all available parameters, see [CONFIG_README.md](CONFIG_README.md).
