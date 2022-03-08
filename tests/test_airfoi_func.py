import sys
import pickle
import os
import gmshairfoil2d.__init__

LIB_DIR = os.path.dirname(gmshairfoil2d.__init__.__file__)
test_data_dir = LIB_DIR + "/../database"

from gmshairfoil2d.airfoil_func import (
    get_all_available_airfoil_names,
    get_airfoil_file,
    NACA_4_digit_geom,
)


def test_get_all_available_airfoil_names():
    """
    Test if at least the database obtained containt some airfoils
    
    """

    expected_airfoil = ["naca0010", "naca0018", "falcon", "goe510", "e1210"]
    current_airfoil_list = get_all_available_airfoil_names()

    for foil in expected_airfoil:
        assert foil in current_airfoil_list, "test passed"


def test_get_airfoil_file():
    """
    Test if at least the database obtained containt some airfoils
    
    """
    test_data_dir


def test_NACA_4_digit_geom():
    """
    Test if the NACA0012 profil and NACA4412 profil are correctly generated
    
    """
    with open("test_data/naca0012.txt", "rb") as f:
        naca0012 = pickle.load(f)
    f.close()
    with open("test_data/naca4412.txt", "rb") as f:
        naca4412 = pickle.load(f)
    f.close()

    assert naca0012 == NACA_4_digit_geom("0012"), "test passed"
    assert naca4412 == NACA_4_digit_geom("4412"), "test passed"
    assert naca4412 != NACA_4_digit_geom("4413"), "test passed"
    f.close()
