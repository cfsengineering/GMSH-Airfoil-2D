import requests
import os
import numpy as np


path = "../../database"

if not os.path.exists(path):
    os.makedirs(path)


def get_all_available_airfoil_names():
    url = "https://m-selig.ae.illinois.edu/ads/coord_database.html"

    r = requests.get(url)

    airfoil_list = [t.split(".dat")[0] for t in r.text.split('href="coord/')[1:]]

    print(f"{len(airfoil_list)} airfoils found:")
    print(airfoil_list)

    return airfoil_list


def get_airfoil_file(airfoil_name):

    url = f"https://m-selig.ae.illinois.edu/ads/coord/{airfoil_name}.dat"

    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(f"Could not get airfoil {airfoil_name}")

    file = f"/{airfoil_name}.dat"

    if not os.path.exists(path + file):
        try:
            open(path + file, "wb").write(r.content)
        except OSError:
            print("Failed creating the file :", file)


def NACA_4_digit_geom(NACA_name, nb_points=100):
    theta_line = np.linspace(0, np.pi, nb_points)
    x_line = 0.5 * (1 - np.cos(theta_line))
    m = int(NACA_name[0]) / 100
    p = int(NACA_name[1]) / 10
    t = (int(NACA_name[2]) * 10 + int(NACA_name[3])) / 100
    # camber line front of the airfoil (befor p)
    x_line_front = x_line[x_line < p]
    # camber line back of the airfoil (after p)
    x_line_back = x_line[x_line >= p]
    # total camber line
    if p != 0:
        y_c = np.concatenate(
            (
                (m / p ** 2) * (2 * p * x_line_front - x_line_front ** 2),
                (m / (1 - p) ** 2)
                * (1 - 2 * p + 2 * p * x_line_back - x_line_back ** 2),
            ),
            axis=0,
        )
        dyc_dx = np.concatenate(
            (
                (2 * m / p ** 2) * (p - x_line_front),
                (2 * m / (1 - p) ** 2) * (p - x_line_back),
            ),
            axis=0,
        )
    else:
        y_c = (0 * x_line_front, 0 * x_line_back)
        dyc_dx = y_c

    # thickness line
    y_t = (
        t
        / 0.2
        * (
            0.2969 * x_line ** 0.5
            - 0.126 * x_line
            - 0.3516 * x_line ** 2
            + 0.2843 * x_line ** 3
            + -0.1036 * x_line ** 4
        )
    )
    if p != 0:
        theta = np.arctan(dyc_dx)
        # upper and lower surface
        x_u = x_line - y_t * np.sin(theta)
        y_u = y_c + y_t * np.cos(theta)
        x_l = x_line + y_t * np.sin(theta)
        y_l = y_c - y_t * np.cos(theta)
    else:
        # upper and lower surface
        x_u = x_line
        y_u = y_t
        x_l = x_line
        y_l = -y_t
    # concatenate the upper and lower
    final_x = np.concatenate((x_u[:-1], np.flip(x_l[1:])), axis=0)
    final_y = np.concatenate((y_u[:-1], np.flip(y_l[1:])), axis=0)

    # create the 3d points cloud
    points_cloud = [[final_x[k], final_y[k], 0] for k in range(0, len(final_x))]
    return points_cloud
