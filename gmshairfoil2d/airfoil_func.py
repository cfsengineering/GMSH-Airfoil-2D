import requests
import os
import numpy as np

import gmshairfoil2d.__init__

LIB_DIR = os.path.dirname(gmshairfoil2d.__init__.__file__)
database_dir = os.path.join(LIB_DIR, os.path.dirname(LIB_DIR), "database")


def get_all_available_airfoil_names():
    """
    Request the airfoil list available at m-selig.ae.illinois.edu

    Returns
    -------
    _ : list
        return a list containing the same of the available airfoil
    """

    url = "https://m-selig.ae.illinois.edu/ads/coord_database.html"

    r = requests.get(url)

    airfoil_list = [t.split(".dat")[0] for t in r.text.split('href="coord/')[1:]]

    print(f"{len(airfoil_list)} airfoils found:")
    print(airfoil_list)

    return airfoil_list


def get_airfoil_file(airfoil_name):
    """
    Request the airfoil .dat file at m-selig.ae.illinois.edu and stores it (if found) in the
    database folder

    Parameters
    ----------
    airfoil_name : srt
        name of the airfoil
    """

    if not os.path.exists(database_dir):
        os.makedirs(database_dir)

    url = f"https://m-selig.ae.illinois.edu/ads/coord/{airfoil_name}.dat"

    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(f"Could not get airfoil {airfoil_name}")

    file_path = os.path.join(database_dir, f"{airfoil_name}.dat")

    if not os.path.exists(file_path):

        with open(file_path, "wb") as f:
            f.write(r.content)


def get_airfoil_points(airfoil_name):

    airfoil_points = []
    upper_points = []
    lower_points = []
    upper_len = 0
    lower_len = 0
    reverse_lower = False

    get_airfoil_file(airfoil_name)
    airfoil_file = os.path.join(database_dir, airfoil_name + ".dat")

    with open(airfoil_file) as f:
        lines = f.readlines()

    for line in lines:

        # Catch the text lines
        try:
            x, y = map(float, line.strip("\n").split())
        except ValueError:
            continue

        # Catch the line with the upper and lower number of points
        if x > 1 and y > 1:
            upper_len = int(x)
            lower_len = int(y)
            continue

        # Catch the x, y coordinates
        airfoil_points.append((x, y))

    n_points = len(airfoil_points)

    if not upper_len or not lower_len:

        upper_len = n_points // 2

        for i, (x, y) in enumerate(airfoil_points):
            if x == y == 0:
                upper_len = i
                break
    else:
        reverse_lower = True

    upper_points = airfoil_points[:upper_len]
    lower_points = airfoil_points[upper_len:]

    if reverse_lower:
        lower_points = lower_points[::-1]

    assert len(upper_points) + len(lower_points) == n_points

    x_up, y_up = zip(*[points for points in upper_points])
    x_lo, y_lo = zip(*[points for points in lower_points])

    x = [*x_up, *x_lo]
    y = [*y_up, *y_lo]

    cloud_points = [(x[k], y[k], 0) for k in range(0, len(x))]
    # remove duplicated points
    return sorted(set(cloud_points), key=cloud_points.index)


def NACA_4_digit_geom(NACA_name, nb_points=100):
    """
    Compute the profile of a NACA 4 digits airfoil

    Parameters
    ----------
    NACA_name : str
        4 digit of the NACA airfoil
    nb_points : int, optional
            number of points for the disrcetisation of
            the polar representation of the chord
    Returns
    -------
    _ : int
        return the 3d cloud of points representing the airfoil
    """

    theta_line = np.linspace(0, np.pi, nb_points)
    x_line = 0.5 * (1 - np.cos(theta_line))

    m = int(NACA_name[0]) / 100
    p = int(NACA_name[1]) / 10
    t = (int(NACA_name[2]) * 10 + int(NACA_name[3])) / 100

    # thickness line
    y_t = (
        t
        / 0.2
        * (
            0.2969 * x_line**0.5
            - 0.126 * x_line
            - 0.3516 * x_line**2
            + 0.2843 * x_line**3
            + -0.1036 * x_line**4
        )
    )

    # cambered airfoil:
    if p != 0:
        # camber line front of the airfoil (befor p)
        x_line_front = x_line[x_line < p]

        # camber line back of the airfoil (after p)
        x_line_back = x_line[x_line >= p]

        # total camber line
        y_c = np.concatenate(
            (
                (m / p**2) * (2 * p * x_line_front - x_line_front**2),
                (m / (1 - p) ** 2)
                * (1 - 2 * p + 2 * p * x_line_back - x_line_back**2),
            ),
            axis=0,
        )
        dyc_dx = np.concatenate(
            (
                (2 * m / p**2) * (p - x_line_front),
                (2 * m / (1 - p) ** 2) * (p - x_line_back),
            ),
            axis=0,
        )

        theta = np.arctan(dyc_dx)

        # upper and lower surface
        x_u = x_line - y_t * np.sin(theta)
        y_u = y_c + y_t * np.cos(theta)
        x_l = x_line + y_t * np.sin(theta)
        y_l = y_c - y_t * np.cos(theta)

    # uncambered airfoil:
    else:
        y_c = 0 * x_line
        dyc_dx = y_c
        # upper and lower surface
        x_u = x_line
        y_u = y_t
        x_l = x_line
        y_l = -y_t

    # concatenate the upper and lower
    x = np.concatenate((x_u[:-1], np.flip(x_l[1:])), axis=0)
    y = np.concatenate((y_u[:-1], np.flip(y_l[1:])), axis=0)

    # create the 3d points cloud
    return [(x[k], y[k], 0) for k in range(0, len(x))]
