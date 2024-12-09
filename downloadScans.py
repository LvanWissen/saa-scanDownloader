"""
saa-scanDownloader

Usage:
    downloadScans.py ead <url> <folder>
    downloadScans.py ead <url> <folder> --concordance False
    downloadScans.py file <collectionNumber> <inventoryNumber> <path> <folder>
    downloadScans.py file <collectionNumber> <inventoryNumber> <path> <folder> --concordance False
    downloadScans.py (-h | --help)

Arguments:
  collectionNumber  Collection number in the SAA inventory.
  inventoryNumber   Inventory number from the collection.
  path              Path in the new (d.d. 2020) search environment. You can see
                    this by clicking on a inventory number and check the address
                    bar. E.g. 1.6. 
  folder            Output folder. A folder with the inventory number is
                    automatically created in this folder.   

Options:
    -h --help       Show this screen.
    --concordance <true_or_false>  Save a concordance.json file with scanname and uuid [default: True]
"""

import os
import math
import time
import requests
import json

from dataclasses import dataclass

import xml.etree.ElementTree as ET

from docopt import docopt

APIURL = "https://webservices.picturae.com/archives/scans/"

DOWNLOADURL = "https://download-images.memorix.nl/ams/download/fullsize/"


@dataclass
class C:
    """
    A class to represent an EAD object.
    """

    id: str
    title: str
    path: str
    hasPart: list


def getEAD(url: str):
    """
    Download the EAD file from the SAA website.

    Args:
        url (str): URL to the EAD file.

    Returns:
        str: EAD file content.
    """

    r = requests.get(url)

    tree = ET.fromstring(r.text)

    return tree


def parse_ead_element(el: ET.Element, level: str = "") -> C:
    """
    Parse an EAD element (did). This can be a series, subseries, or file.

    Args:
        el (ET.Element): EAD element.
        level (str, optional): Level in the hierarchy. Defaults to "".

    Returns:
        C: A C object.
    """

    id = el.find("did/unitid").text
    title = el.find("did/unittitle").text

    c = C(
        id=id,
        title=title,
        path=level,
        hasPart=[
            parse_ead_element(child, f"{level}.{i+1}")
            for i, child in enumerate(el.findall("c"))
        ],
    )

    return c


def parse_ead(tree: ET.Element) -> C:
    """
    Parse an EAD xml tree (root). All the children of the root
    are assumed to be series, subseries or files (dids).

    Args:
        tree (ET.Element): EAD tree.

    Returns:
        C: A C object.
    """

    id = tree.find(".//eadid").text
    title = tree.find(".//titleproper").text

    c = C(
        id=id,
        title=title,
        path="0",
        hasPart=[
            parse_ead_element(child, str(i + 1))
            for i, child in enumerate(tree.findall("archdesc/dsc/c"))
        ],
    )

    return c


def flatten_ead_tree(c):
    """
    Flatten an EAD tree (all subtrees) into a single list.

    Args:
        c (C): EAD object.

    Returns:
        list: A list of all the elements in the EAD object.
    """

    stack = []
    for part in c.hasPart:
        stack.append(part)
        if part.hasPart:
            stack += flatten_ead_tree(part)
    return stack


def getScanCount(path: str, collectionNumber: str, APIURL=APIURL):
    """
    Get the number of scans in a specific inventory.

    Args:
        path (str): Path in the new (d.d. 2020) search environment. You can see
                    this by clicking on a inventory number and check the address
                    bar. E.g. 1.6.
        collectionNumber (str): Collection number in the SAA inventory.
        APIURL ([type], optional): Picturae url. Defaults to APIURL.

    Returns:
        int: Number of scans in the inventory.
    """

    url = APIURL + collectionNumber + "/" + path
    arguments = {
        "apiKey": "eb37e65a-eb47-11e9-b95c-60f81db16c0e",
        "lang": "nl_NL",
        "findingAid": collectionNumber,
        "path": path,
        "callback": "callback_json8",
        "start": 0,
        "limit": 10,
    }

    r = requests.get(url, arguments)
    data = r.text.replace("callback_json8(", "").replace(")", "")
    data = json.loads(data)

    return data["scans"]["scancount"]


def getScans(
    path: str,
    nscans: int,
    collectionNumber: str,
    start: int = 0,
    limit: int = 100,
    APIURL=APIURL,
):
    """
    Download scan metadata that contains a.o. the name and uuid.

    Args:
        path (str): Path in the new (d.d. 2020) search environment. You can see
                    this by clicking on a inventory number and check the address
                    bar. E.g. 1.6.
        nscans (int): How many scans are in this inventory? This can also be
                      read from the SAA website.
        collectionNumber (str): Collection number in the SAA inventory.
        start (int, optional): Offset. Defaults to 0.
        limit (int, optional): Maximum number of scans to retrieve in one go.
                               Defaults to 100.
        APIURL ([type], optional): Picturae url. Defaults to APIURL.
    """

    url = APIURL + collectionNumber + "/" + path
    arguments = {
        "apiKey": "eb37e65a-eb47-11e9-b95c-60f81db16c0e",
        "lang": "nl_NL",
        "findingAid": collectionNumber,
        "path": path,
        "callback": "callback_json8",
        "start": start,
        "limit": limit,
    }

    scans = []
    for i in range(math.ceil(nscans / 100)):
        r = requests.get(url, arguments)

        data = r.text.replace("callback_json8(", "").replace(")", "")
        data = json.loads(data)

        arguments["start"] += limit
        time.sleep(1)  # be gentle

        scans += data["scans"]["scans"]

    return scans


def downloadScan(uuidScan: str, scanName: str, folder: str = "data"):
    """
    Download a single scan by uuid.

    Args:
        uuidScan (str): a scan's uuid (e.g. cb8e6db8-6dc7-50d6-97c1-6d6fa5284ab3)
        scanName (str): a scan's name (e.g. KLAC00169000001)
        folder (str, optional): Output folder. A folder with the inventory
                                number is automatically created in this folder.
                                Defaults to 'data'.
    """

    fp = os.path.join(folder, scanName + ".jpg")

    if os.path.exists(fp):
        return

    url = DOWNLOADURL + uuidScan + ".jpg"

    r = requests.get(url, stream=True)

    if r.status_code == 200:
        with open(fp, "wb") as outfile:
            for chunk in r:
                outfile.write(chunk)


def downloadScansFromEAD(c, folder, concordancefile):
    """
    Download scans from an EAD object.

    Args:
        c (C): EAD object.
        folder (str): Output folder.
        concordancefile (bool): Save a concordance.json file with scanname and uuid.
    """

    collectionNumber = c.id

    # Flatten!
    children = [child for part in c.hasPart for child in (part.hasPart or [part])]

    for child in children:
        if not child.hasPart:  # File level
            path = child.path
            inventoryNumber = child.id

            downloadFile(
                path, collectionNumber, inventoryNumber, folder, concordancefile
            )


def downloadFile(path, collectionNumber, inventoryNumber, folder, concordancefile):

    folder = os.path.join(folder, collectionNumber, inventoryNumber)
    if concordancefile:
        concordance = dict()

    # 0. Get the scan count
    nscans = getScanCount(path, collectionNumber)

    # 1. Obtain the scan metadata
    scans = getScans(path, nscans, collectionNumber)

    if not scans:
        print(f"No scans found for {inventoryNumber}")
        return

    os.makedirs(folder, exist_ok=True)

    # 2. Download each scan
    print(f"Downloading scans to {os.path.abspath(folder)}:")
    for n, scan in enumerate(scans, 1):
        uuid = scan["id"]
        name = scan["name"]

        print(f"\t{n}/{nscans}\t{name}.jpg")
        downloadScan(uuid, name, folder)

        if concordancefile:
            concordance[name] = uuid

        time.sleep(1)

        # break

    if concordancefile:
        with open(
            os.path.join(folder, "concordance.json"), "w", encoding="utf-8"
        ) as jsonfile:
            json.dump(concordance, jsonfile, indent=4)


if __name__ == "__main__":

    arguments = docopt(__doc__)

    FOLDER = arguments["<folder>"]
    os.makedirs(FOLDER, exist_ok=True)

    CONCORDANCEFILE = True if arguments["--concordance"] == "True" else False

    if arguments["ead"]:
        EADURL = arguments["<url>"]
        FOLDER = arguments["<folder>"]

        tree = getEAD(EADURL)
        c = parse_ead(tree)

        collectionNumber = c.id
        elements = flatten_ead_tree(c)

        for element in sorted(elements, key=lambda x: x.path):
            if not element.hasPart:  # File level
                path = element.path
                inventoryNumber = element.id

                downloadFile(
                    path, collectionNumber, inventoryNumber, FOLDER, CONCORDANCEFILE
                )

    elif arguments["file"]:
        COLLECTIONNUMBER = arguments["<collectionNumber>"]
        INVENTORYNUMBER = arguments["<inventoryNumber>"]
        PATH = arguments["<path>"]
        CONCORDANCEFILE = True if arguments["--concordance"] == "True" else False

        downloadFile(PATH, COLLECTIONNUMBER, INVENTORYNUMBER, FOLDER, CONCORDANCEFILE)

    else:
        print(__doc__)
