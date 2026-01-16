#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the configuration file handler
"""

import pytest
from pathlib import Path
from gmshairfoil2d.config_handler import read_config, write_config, merge_config_with_args
import argparse


def test_read_config_basic(tmp_path):
    """
    Test reading basic configuration from file
    """
    config_content = """# Test configuration file
naca= 0012
aoa= 5.0
farfield= 10
format= su2
"""
    
    config_file = tmp_path / "test_config.cfg"
    config_file.write_text(config_content)
    
    config = read_config(str(config_file))
    
    assert config['naca'] == '0012'
    assert config['aoa'] == 5.0
    assert config['farfield'] == 10
    assert config['format'] == 'su2'


def test_read_config_empty_values(tmp_path):
    """
    Test that empty values are skipped
    """
    config_content = """naca= 0012
airfoil=
aoa= 5.0
output=
format= su2
"""
    
    config_file = tmp_path / "test_config.cfg"
    config_file.write_text(config_content)
    
    config = read_config(str(config_file))
    
    # Should have the parameters with values
    assert 'naca' in config
    assert 'aoa' in config
    assert 'format' in config
    
    # Should NOT have the empty parameters
    assert 'airfoil' not in config
    assert 'output' not in config


def test_read_config_boolean_values(tmp_path):
    """
    Test that boolean values are correctly converted
    """
    config_content = """no_bl= False
structured= True
ui= false
"""
    
    config_file = tmp_path / "test_config.cfg"
    config_file.write_text(config_content)
    
    config = read_config(str(config_file))
    
    assert config['no_bl'] is False
    assert config['structured'] is True
    assert config['ui'] is False


def test_read_config_numeric_conversion(tmp_path):
    """
    Test that numeric values are correctly converted to float/int
    """
    config_content = """nb_layers= 35
aoa= 5.5
first_layer= 3e-05
ratio= 1.2
"""
    
    config_file = tmp_path / "test_config.cfg"
    config_file.write_text(config_content)
    
    config = read_config(str(config_file))
    
    assert config['nb_layers'] == 35
    assert isinstance(config['nb_layers'], int)
    assert config['aoa'] == 5.5
    assert isinstance(config['aoa'], float)
    assert config['first_layer'] == 3e-05
    assert isinstance(config['first_layer'], float)
    assert config['ratio'] == 1.2
    assert isinstance(config['ratio'], float)


def test_read_config_comments_ignored(tmp_path):
    """
    Test that comment lines are ignored
    """
    config_content = """# This is a comment
naca= 0012
# Another comment
aoa= 5.0
# Even more comments here
"""
    
    config_file = tmp_path / "test_config.cfg"
    config_file.write_text(config_content)
    
    config = read_config(str(config_file))
    
    assert len(config) == 2
    assert config['naca'] == '0012'
    assert config['aoa'] == 5.0


def test_read_config_file_not_found():
    """
    Test that FileNotFoundError is raised for non-existent files
    """
    with pytest.raises(FileNotFoundError):
        read_config("/non/existent/config.cfg")


def test_write_config(tmp_path):
    """
    Test writing configuration to file
    """
    config_dict = {
        'naca': '0012',
        'aoa': 5.0,
        'farfield': 10,
        'format': 'su2',
        'structured': False
    }
    
    output_file = tmp_path / "output_config.cfg"
    write_config(config_dict, str(output_file))
    
    # Verify file was created
    assert output_file.exists()
    
    # Read back and verify
    content = output_file.read_text()
    assert 'naca= 0012' in content
    assert 'aoa= 5.0' in content
    assert 'farfield= 10' in content
    assert 'format= su2' in content


def test_write_config_with_none_values(tmp_path):
    """
    Test writing configuration with None values
    """
    config_dict = {
        'naca': '0012',
        'airfoil': None,
        'aoa': 5.0
    }
    
    output_file = tmp_path / "output_config.cfg"
    write_config(config_dict, str(output_file))
    
    content = output_file.read_text()
    assert 'airfoil=' in content


def test_merge_config_with_args():
    """
    Test merging configuration with command-line arguments
    """
    config_dict = {
        'naca': '0012',
        'aoa': 5.0,
        'farfield': 10,
        'format': 'su2'
    }
    
    # Create mock args with defaults
    parser = argparse.ArgumentParser()
    parser.add_argument('--naca', default=None)
    parser.add_argument('--aoa', type=float, default=None)
    parser.add_argument('--farfield', type=float, default=10)
    parser.add_argument('--format', default=None)
    parser.add_argument('--output', default='.')
    
    args = parser.parse_args([])
    
    # Merge config into args
    merged_args = merge_config_with_args(config_dict, args)
    
    assert merged_args.naca == '0012'
    assert merged_args.aoa == 5.0
    assert merged_args.format == 'su2'
    assert merged_args.output == '.'  # Default not overridden


def test_merge_config_cli_precedence():
    """
    Test that CLI arguments take precedence over config file
    """
    config_dict = {
        'naca': '0012',
        'aoa': 5.0,
        'format': 'su2'
    }
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--naca', default=None)
    parser.add_argument('--aoa', type=float, default=None)
    parser.add_argument('--format', default=None)
    
    # Simulate CLI providing aoa explicitly
    args = parser.parse_args(['--aoa', '10.0'])
    
    merged_args = merge_config_with_args(config_dict, args)
    
    # Config values applied
    assert merged_args.naca == '0012'
    assert merged_args.format == 'su2'
    
    # CLI value takes precedence
    assert merged_args.aoa == 10.0


def test_read_write_roundtrip(tmp_path):
    """
    Test that writing and reading back produces the same config
    """
    original_config = {
        'naca': '2412',
        'aoa': 3.5,
        'farfield': 15,
        'format': 'cgns',
        'nb_layers': 50,
        'first_layer': 1e-04
    }
    
    config_file = tmp_path / "roundtrip_config.cfg"
    
    # Write
    write_config(original_config, str(config_file))
    
    # Read back
    read_back_config = read_config(str(config_file))
    
    # Verify all values match
    for key, value in original_config.items():
        assert key in read_back_config
        assert read_back_config[key] == value
