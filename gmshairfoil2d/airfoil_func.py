import sys
from pathlib import Path

import numpy as np
import requests

import gmshairfoil2d.__init__

LIB_DIR = Path(gmshairfoil2d.__init__.__file__).parents[1]
database_dir = Path(LIB_DIR, "database")


def read_airfoil_from_file(file_path):
    """Read airfoil coordinates from a .dat file.
    
    Parameters
    ----------
    file_path : str or Path
        Path to airfoil data file
    
    Returns
    -------
    list
        List of unique (x, y, 0) points sorted by original order
    
    Raises
    ------
    FileNotFoundError
        If file does not exist
    ValueError
        If no valid airfoil points found
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} not found.")

    airfoil_points = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('#', 'Airfoil')):
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                x, y = map(float, parts)
            except ValueError:
                continue
            if x > 1 and y > 1:
                continue
            airfoil_points.append((x, y))

    if not airfoil_points:
        raise ValueError(f"No valid airfoil points found in {file_path}")

    # Split upper and lower surfaces
    try:
        split_index = next(i for i, (x, y) in enumerate(airfoil_points) if x >= 1.0)
    except StopIteration:
        split_index = len(airfoil_points) // 2

    upper_points = airfoil_points[:split_index + 1]
    lower_points = airfoil_points[split_index + 1:]

    # Ensure lower points start from trailing edge
    if lower_points and lower_points[0][0] == 0.0:
        lower_points = lower_points[::-1]

    # Combine and remove duplicates
    x_up, y_up = zip(*upper_points) if upper_points else ([], [])
    x_lo, y_lo = zip(*lower_points) if lower_points else ([], [])

    cloud_points = [(x, y, 0) for x, y in zip([*x_up, *x_lo], [*y_up, *y_lo])]
    return sorted(set(cloud_points), key=cloud_points.index)


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
    Request the airfoil .dat file from m-selig.ae.illinois.edu and store it in database folder.

    Parameters
    ----------
    airfoil_name : str
        Name of the airfoil
    
    Raises
    ------
    SystemExit
        If airfoil not found or network error occurs
    """
    if not database_dir.exists():
        database_dir.mkdir()

    file_path = Path(database_dir, f"{airfoil_name}.dat")
    if file_path.exists():
        return

    url = f"https://m-selig.ae.illinois.edu/ads/coord/{airfoil_name}.dat"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Error: Could not find airfoil '{airfoil_name}' on UIUC database.")
            sys.exit(1)
        with open(file_path, "wb") as f:
            f.write(response.content)
    except requests.exceptions.RequestException:
        print(f"❌ Network Error: Could not connect to the database. Check your internet.")
        sys.exit(1)


def get_airfoil_points(airfoil_name: str) -> list[tuple[float, float, float]]:
    """Load airfoil points from the database.
    
    Parameters
    ----------
    airfoil_name : str
        Name of the airfoil in the database
    
    Returns
    -------
    list
        List of unique (x, y, 0) points
    
    Raises
    ------
    ValueError
        If no valid points found for the airfoil
    """
    if len(airfoil_name) == 4 and airfoil_name.isdigit():
        return four_digit_naca_airfoil(
            naca_name=airfoil_name,
        )

    get_airfoil_file(airfoil_name)
    airfoil_file = Path(database_dir, f"{airfoil_name}.dat")

    airfoil_points = []
    with open(airfoil_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(('#', 'Airfoil')):
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            try:
                x, y = map(float, parts)
            except ValueError:
                continue
            if x > 1 and y > 1:
                continue
            airfoil_points.append((x, y))

    if not airfoil_points:
        raise ValueError(f"No valid points found for airfoil {airfoil_name}")

    def _dedupe_consecutive(points, tol=1e-9):
        out = []
        for x, y in points:
            if not out:
                out.append((x, y))
                continue
            if abs(x - out[-1][0]) <= tol and abs(y - out[-1][1]) <= tol:
                continue
            out.append((x, y))
        return out

    def _dedupe_any(points, tol=1e-9):
        out = []
        for x, y in points:
            if any(abs(x - ux) <= tol and abs(y - uy) <= tol for ux, uy in out):
                continue
            out.append((x, y))
        return out

    tol = 1e-9
    airfoil_points = _dedupe_consecutive(airfoil_points, tol=tol)

    if len(airfoil_points) < 3:
        raise ValueError(f"Not enough unique points for airfoil {airfoil_name}")

    # Split into upper/lower when a LE point repeats (common in UIUC files)
    min_x = min(x for x, _ in airfoil_points)
    le_indices = [i for i, (x, _) in enumerate(airfoil_points) if abs(x - min_x) <= tol]

    if len(le_indices) >= 2:
        split_idx = le_indices[1]
        upper = airfoil_points[:split_idx]
        lower = airfoil_points[split_idx:]
    else:
        # Fallback: split at first maximum x (trailing edge)
        max_x = max(x for x, _ in airfoil_points)
        split_idx = next(i for i, (x, _) in enumerate(airfoil_points) if abs(x - max_x) <= tol)
        upper = airfoil_points[:split_idx + 1]
        lower = airfoil_points[split_idx + 1:]

    def _ensure_le_to_te(points):
        if len(points) < 2:
            return points
        return points if points[0][0] <= points[-1][0] else points[::-1]

    upper = _ensure_le_to_te(upper)
    lower = _ensure_le_to_te(lower)

    # Build a closed loop starting at TE: TE->LE (upper reversed) then LE->TE (lower)
    if upper and lower:
        upper = upper[::-1]
        loop = upper + lower[1:]
    else:
        loop = airfoil_points

    # Remove duplicate closing point if present
    if len(loop) > 1:
        x0, y0 = loop[0]
        x1, y1 = loop[-1]
        if abs(x0 - x1) <= tol and abs(y0 - y1) <= tol:
            loop.pop()

    loop = _dedupe_any(loop, tol=tol)

    if len(loop) < 3:
        raise ValueError(f"Not enough unique points for airfoil {airfoil_name}")

    return [(x, y, 0) for x, y in loop]


def four_digit_naca_airfoil(naca_name: str, nb_points: int = 100):
    """
    Compute the profile of a NACA 4 digits airfoil

    Parameters
    ----------
    naca_name : str
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

    m = int(naca_name[0]) / 100
    p = int(naca_name[1]) / 10
    t = (int(naca_name[2]) * 10 + int(naca_name[3])) / 100

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
