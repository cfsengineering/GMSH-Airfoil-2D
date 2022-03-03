import requests


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

    open(f"database/{airfoil_name}.dat", "wb").write(r.content)