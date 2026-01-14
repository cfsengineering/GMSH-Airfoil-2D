import pickle
from pathlib import Path
from unittest.mock import patch, Mock

import gmshairfoil2d.__init__
from gmshairfoil2d.airfoil_func import (NACA_4_digit_geom, get_airfoil_file,
                                        get_all_available_airfoil_names)
from pytest import approx

LIB_DIR = Path(gmshairfoil2d.__init__.__file__).parents[1]

database_dir = Path(LIB_DIR, "database")
test_data_dir = Path(LIB_DIR, "tests", "test_data")

def test_get_all_available_airfoil_names(monkeypatch):
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = (
                '<html>'
                '<a href="coord/naca0010.dat">naca0010</a>'
                '<a href="coord/naca0018.dat">naca0018</a>'
                '<a href="coord/falcon.dat">falcon</a>'
                '<a href="coord/goe510.dat">goe510</a>'
                '<a href="coord/e1210.dat">e1210</a>'
                '</html>'
            )

    monkeypatch.setattr("gmshairfoil2d.airfoil_func.requests.get", lambda *args, **kwargs: MockResponse())

    from gmshairfoil2d.airfoil_func import get_all_available_airfoil_names
    current_airfoil_list = get_all_available_airfoil_names()

    expected_airfoil = ["naca0010", "naca0018", "falcon", "goe510", "e1210"]
    for foil in expected_airfoil:
        assert foil in current_airfoil_list


def test_get_airfoil_file(monkeypatch, tmp_path):
    """
    Testa il download (simulato) dei profili e verifica che il file 
    venga salvato correttamente con il contenuto atteso.
    """

    fake_content = "0.0 0.0\n0.5 0.1\n1.0 0.0"
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.text = fake_content

    monkeypatch.setattr("gmshairfoil2d.airfoil_func.requests.get", lambda *args, **kwargs: MockResponse())

    monkeypatch.setattr("gmshairfoil2d.airfoil_func.database_dir", tmp_path)

    from gmshairfoil2d.airfoil_func import get_airfoil_file
    
    profile = "naca0010"
    expected_path = tmp_path / f"{profile}.dat"

    get_airfoil_file(profile)

    assert expected_path.exists()
    assert expected_path.read_text() == fake_content


def test_NACA_4_digit_geom():
    with open(Path(test_data_dir, "naca0012.txt"), "rb") as f:
        naca0012 = pickle.load(f)
    with open(Path(test_data_dir, "naca4412.txt"), "rb") as f:
        naca4412 = pickle.load(f)

    """
    Test if the NACA0012 profil and NACA4412 profil are correctly generated
    """

    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca0012, NACA_4_digit_geom("0012"))]
    )

    assert all(
        [a == approx(b, 1e-3) for a, b in zip(naca4412, NACA_4_digit_geom("4412"))]
    )
