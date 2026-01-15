#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration file handler for gmshairfoil2d.
Supports reading and writing simple key=value configuration files.
Empty values are skipped.
"""

import os
from pathlib import Path


def read_config(config_path):
    """
    Read configuration from a simple config file (key=value format).
    Empty values are skipped.
    
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
                
                # Convert string values to appropriate types
                if key in string_params:
                    # Keep these as strings
                    config[key] = value
                elif value.lower() == 'true':
                    config[key] = True
                elif value.lower() == 'false':
                    config[key] = False
                elif value.lower() == 'none':
                    config[key] = None
                else:
                    # Try to convert to float/int
                    try:
                        if '.' in value or 'e' in value.lower():
                            config[key] = float(value)
                        else:
                            config[key] = int(value)
                    except ValueError:
                        # Keep as string
                        config[key] = value
        
        return config
    
    except Exception as e:
        raise Exception(f"Error parsing configuration file: {e}")


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
    """
    Merge configuration file parameters with command-line arguments.
    Command-line arguments take precedence over config file values.
    
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
    # Convert args to dict
    args_dict = vars(args).copy()
    
    # For each key in config, update args only if not explicitly set on command line
    for key, value in config_dict.items():
        # Skip if the argument was explicitly provided on command line
        # We determine this by checking if it differs from the default
        if key in args_dict:
            # Only override with config value if current value is default/None
            if args_dict[key] is None or args_dict[key] is False:
                args_dict[key] = value
    
    # Convert back to Namespace
    for key, value in args_dict.items():
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
