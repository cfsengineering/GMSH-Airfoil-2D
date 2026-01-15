## Configuration File Usage

The `gmshairfoil2d` tool supports configuration files for batch generation of meshes without using command-line arguments.

### Format

Configuration files use a simple key=value format:
- One parameter per line
- Empty lines and comments (starting with `#`) are ignored
- Empty values (after `=`) are skipped
- Spaces around the `=` sign are flexible

Example:
```
# Configuration for NACA 0012 airfoil
naca= 0012
aoa= 0.0
farfield= 10
format= su2
```

### Creating Example Config

To create an example configuration file with all available options:

```bash
gmshairfoil2d --example_config
```

This generates `config_example.cfg` with default/example values.

### Using Config File

Run with a configuration file:

```bash
gmshairfoil2d --config path/to/config.cfg
```

### Overriding Config with Command Line

Command-line arguments take precedence over config file values:

```bash
gmshairfoil2d --config config.cfg --aoa 5.0
```

This uses the config file settings but overrides `aoa` with `5.0`.

### Saving Current Config

To save the configuration from a run:

```bash
gmshairfoil2d --naca 0012 --aoa 5.0 --save_config my_config.cfg
```

This creates a config file with the parameters used for the mesh generation.

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `naca` | string | - | NACA 4-digit airfoil (e.g., 0012, 2412) |
| `airfoil` | string | - | Named airfoil from database |
| `airfoil_path` | string | - | Path to custom airfoil .dat file |
| `flap_path` | string | - | Path to custom flap .dat file |
| `aoa` | float | 0.0 | Angle of attack [degrees] |
| `deflection` | float | 0.0 | Flap deflection angle [degrees] |
| `farfield` | float | 10 | Farfield radius [m] |
| `farfield_ctype` | boolean | - | Use C-type structured farfield for hybrid meshes |
| `box` | string | - | Box dimensions (e.g., 20x10) |
| `airfoil_mesh_size` | float | 0.01 | Mesh size on airfoil [m] |
| `ext_mesh_size` | float | 0.2 | Mesh size in external domain [m] |
| `no_bl` | boolean | - | Disable boundary layer |
| `first_layer` | float | 3e-05 | Height of first BL [m] |
| `ratio` | float | 1.2 | BL growth ratio |
| `nb_layers` | int | 35 | Number of BL layers |
| `format` | string | su2 | Output format (msh, su2, cgns, vtk, etc.) |
| `structured` | boolean | - | Generate fully structured mesh |
| `arg_struc` | string | 10x10 | Structured mesh domain [LxH] |
| `output` | string | . | Output directory |
| `ui` | boolean | - | Open GMSH GUI after generation |

### Notes

- Boolean values can be written as `True`, `False`, `true`, `false`
- Empty values (e.g., `output=`) are skipped - the default is used
- Floating point numbers are automatically detected (e.g., `3e-05`)
- You must specify at least one airfoil source: `naca`, `airfoil`, or `airfoil_path`
