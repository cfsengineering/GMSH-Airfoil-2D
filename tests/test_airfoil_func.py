import pickle
from pathlib import Path

import gmshairfoil2d.__init__
from gmshairfoil2d.airfoil_func import (NACA_4_digit_geom, get_airfoil_file,
                                        get_all_available_airfoil_names)
from pytest import approx

LIB_DIR = Path(gmshairfoil2d.__init__.__file__).parents[1]

database_dir = Path(LIB_DIR, "database")
test_data_dir = Path(LIB_DIR, "tests", "test_data")

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
    they are conform.
    """

    # Remove airfoil if they exist
    for profile in ["naca0010", "naca4412"]:
        
        proflie_dl_path = Path(database_dir, profile + ".dat")
        if proflie_dl_path.exists():
            proflie_dl_path.unlink()

        # Download them back
        get_airfoil_file(profile)

        # Test if download is correctly done
        assert proflie_dl_path.exists()

        with open(proflie_dl_path, "r") as f:
            profil_dl = f.read()

        proflie_test_path = Path(test_data_dir, profile + ".dat")
        with open(proflie_test_path, "r") as f:
            profil_test = f.read()
        
        # Test if the downloaded profile is the same as the test profile
        assert profil_test == profil_dl


def test_NACA_4_digit_geom():
    """
    Test if the NACA0012 profil and NACA4412 profil are correctly generated
    
    """
    
    with open(Path(test_data_dir, "naca0012.txt"), "rb") as f:
        naca0012 = pickle.load(f)
    with open(Path(test_data_dir, "naca4412.txt"), "rb") as f:
        naca4412 = pickle.load(f)

    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca0012, NACA_4_digit_geom("0012"))]
    )
    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca4412, NACA_4_digit_geom("4412"))]
    )
