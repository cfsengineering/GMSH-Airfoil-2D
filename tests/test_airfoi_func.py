import sys
import pickle
import os
import gmshairfoil2d.__init__
from pytest import approx
from gmshairfoil2d.airfoil_func import (
    get_all_available_airfoil_names,
    get_airfoil_file,
    NACA_4_digit_geom,
)


LIB_DIR = os.path.dirname(gmshairfoil2d.__init__.__file__)
database_dir = os.path.join(LIB_DIR, os.path.dirname(LIB_DIR), "database")
test_data_dir = os.path.join(LIB_DIR, os.path.dirname(LIB_DIR), "tests", "test_data")


def test_get_all_available_airfoil_names():
    """
    Test if at least the database obtained containt some airfoils

    """

    expected_airfoil = ["naca0010", "naca0018", "falcon", "goe510", "e1210"]
    current_airfoil_list = get_all_available_airfoil_names()

    for foil in expected_airfoil:
        assert foil in current_airfoil_list


def test_get_airfoil_file():
    """
    Test if the download of some profiles is possible and if it is, check if
    they are conform

    """
    profiles = ["naca0010", "naca4412"]
    # Remove airfoil if they exist
    for profile in profiles:
        proflie_dl_path = os.path.join(database_dir, profile + ".dat")
        if os.path.exists(proflie_dl_path):
            os.remove(proflie_dl_path)

        proflie_test_path = os.path.join(test_data_dir, profile + ".dat")
        # Download them back
        get_airfoil_file(profile)

        # Test if download is correctly done
        assert os.path.exists(proflie_dl_path)

        with open(proflie_dl_path, "r") as f:
            profil_dl = f.read()

        with open(proflie_test_path, "r") as f:
            profil_test = f.read()
        # Test if conform
        assert profil_test == profil_dl


def test_NACA_4_digit_geom():
    """
    Test if the NACA0012 profil and NACA4412 profil are correctly generated
    
    """
    with open(os.path.join(test_data_dir, "naca0012.txt"), "rb") as f:
        naca0012 = pickle.load(f)
    with open(os.path.join(test_data_dir, "naca4412.txt"), "rb") as f:
        naca4412 = pickle.load(f)

    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca0012, NACA_4_digit_geom("0012"))]
    )
    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca4412, NACA_4_digit_geom("4412"))]
    )
