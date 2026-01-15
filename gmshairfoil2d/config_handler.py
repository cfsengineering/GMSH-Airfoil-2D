#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration file handler for gmshairfoil2d.
Supports reading and writing simple key=value configuration files.
Empty values are skipped.
"""

from pathlib import Path


def _convert_value(value, key, string_params):
    """Convert string value to appropriate type.
    
    Parameters
    ----------
    value : str
        String value to convert
    key : str
        Configuration key name
    string_params : set
        Set of keys that should remain as strings
    
    Returns
    -------
    str, int, float, bool, or None
        Converted value
    """
    if key in string_params:
        return value
    
    value_lower = value.lower()
    if value_lower == 'true':
        return True
    elif value_lower == 'false':
        return False
    elif value_lower == 'none':
        return None
    
    # Try to convert to numeric
    try:
        if '.' in value or 'e' in value_lower:
            return float(value)
        return int(value)
    except ValueError:
        return value


def read_config(config_path):
    """Read configuration from a simple config file (key=value format).
    
    Empty values are skipped. Values are automatically converted to appropriate types
    (int, float, bool) unless the key is in the string_params set.
    
    Parameters
    ----------
    config_path : str or Path
        Path to the configuration file
    
    Returns
    -------
    dict
        Dictionary containing configuration parameters
    
    Raises
    ------
    FileNotFoundError
        If the configuration file doesn't exist
    Exception
        If there's an error parsing the configuration file
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Parameters that should always remain as strings
    string_params = {'naca', 'airfoil', 'airfoil_path', 'flap_path', 'format', 'arg_struc', 'box'}
    
    config = {}
    
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Split by first '=' only
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Skip empty values
                if not value:
                    continue
                
                # Convert value to appropriate type
                config[key] = _convert_value(value, key, string_params)
        
        return config
    
    except FileNotFoundError:
        raise
    except Exception as e:
        raise Exception(f"Error parsing configuration file: {e}") from e


def write_config(config_dict, output_path):
    """
    Write configuration to a simple config file (key=value format).
    
    Parameters
    ----------
    config_dict : dict
        Configuration dictionary to write
    output_path : str or Path
        Output path for the configuration file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for key, value in config_dict.items():
            if value is None:
                f.write(f"{key}=\n")
            else:
                f.write(f"{key}= {value}\n")
    
    print(f"Configuration saved to: {output_path}")


def merge_config_with_args(config_dict, args):
    """Merge configuration file parameters with command-line arguments.
    
    Command-line arguments take precedence over config file values. Only applies
    config values when the command-line value is None or False (default).
    
    Parameters
    ----------
    config_dict : dict
        Configuration dictionary from config file
    args : argparse.Namespace
        Command-line arguments
    
    Returns
    -------
    argparse.Namespace
        Merged arguments with config values applied
    """
    args_dict = vars(args)
    
    # For each key in config, update args only if not explicitly set on command line
    for key, value in config_dict.items():
        if key in args_dict:
            # Only override with config value if current value is default/None/False
            if args_dict[key] is None or args_dict[key] is False:
                setattr(args, key, value)
    
    return args


def create_example_config(output_path="config_example.cfg"):
    """
    Create an example configuration file with all available options.
    
    Parameters
    ----------
    output_path : str or Path
        Output path for the example configuration file
    """
    example_config = {
        "naca": "0012",
        "airfoil": None,
        "airfoil_path": None,
        "flap_path": None,
        "aoa": "0.0",
        "deflection": "0.0",
        "farfield": "10",
        "farfield_ctype": None,
        "box": None,
        "airfoil_mesh_size": "0.01",
        "flap_mesh_size": None,
        "ext_mesh_size": "0.2",
        "no_bl": "False",
        "first_layer": "3e-05",
        "ratio": "1.2",
        "nb_layers": "35",
        "format": "su2",
        "structured": "False",
        "arg_struc": "10x10",
        "output": None,
        "ui": "False",
    }
    
    write_config(example_config, output_path)
