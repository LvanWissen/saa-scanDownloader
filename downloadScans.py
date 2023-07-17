"""
saa-scanDownloader

Usage:
    downloadScans.py <collectionNumber> <inventoryNumber> <path> <nscans> <folder>
    downloadScans.py <collectionNumber> <inventoryNumber> <path> <nscans> <folder> --concordance False
    downloadScans.py (-h | --help)

Arguments:
  collectionNumber  Collection number in the SAA inventory.
  inventoryNumber   Inventory number from the collection.
  path              Path in the new (d.d. 2020) search environment. You can see
                    this by clicking on a inventory number and check the address
                    bar. E.g. 1.6. 
  nscans            How many scans are in this inventory? This can also be read
                    from the SAA website. 
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

from docopt import docopt

APIURL = "https://webservices.picturae.com/archives/scans/"

DOWNLOADURL = "https://download-images.memorix.nl/ams/download/fullsize/"


def getScans(path: str,
             nscans: int,
             collectionNumber: str,
             start: int = 0,
             limit: int = 100,
             APIURL=APIURL):
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

    url = APIURL + collectionNumber + '/' + path
    arguments = {
        'apiKey': 'eb37e65a-eb47-11e9-b95c-60f81db16c0e',
        'lang': 'nl_NL',
        'findingAid': collectionNumber,
        'path': path,
        'callback': 'callback_json8',
        'start': start,
        'limit': limit
    }

    scans = []
    for i in range(math.ceil(nscans / 100)):
        r = requests.get(url, arguments)

        data = r.text.replace('callback_json8(', '').replace(')', '')
        data = json.loads(data)

        arguments['start'] += limit
        time.sleep(.6)  # be gentle

        scans += data['scans']['scans']

    return scans


def downloadScan(uuidScan: str, scanName: str, folder: str = 'data'):
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
    
    url = DOWNLOADURL + uuidScan + '.jpg'

    r = requests.get(url, stream=True)

    if r.status_code == 200:
        with open(fp, 'wb') as outfile:
            for chunk in r:
                outfile.write(chunk)


def main(path, nscans, collectionNumber, inventoryNumber, folder,
         concordancefile):

    folder = os.path.join(folder, inventoryNumber)
    if concordancefile:
        concordance = dict()

    # 1. Obtain the scan metadata
    scans = getScans(path, nscans, collectionNumber)

    # 2. Download each scan
    print(f"Downloading scans to {os.path.abspath(folder)}:")
    for n, scan in enumerate(scans, 1):
        uuid = scan['id']
        name = scan['name']

        print(f"\t{n}/{nscans}\t{name}.jpg")
        downloadScan(uuid, name, folder)

        if concordancefile:
            concordance[name] = uuid

        time.sleep(1)

        # break

    if concordancefile:
        with open(os.path.join(folder, 'concordance.json'),
                  'w',
                  encoding='utf-8') as jsonfile:
            json.dump(concordance, jsonfile, indent=4)


if __name__ == "__main__":

    arguments = docopt(__doc__)

    COLLECTIONNUMBER = arguments['<collectionNumber>']
    INVENTORYNUMBER = arguments['<inventoryNumber>']
    PATH = arguments['<path>']
    NSCANS = int(arguments['<nscans>'])
    FOLDER = arguments['<folder>']
    CONCORDANCEFILE = True if arguments['--concordance'] == 'True' else False

    os.makedirs(os.path.join(FOLDER, INVENTORYNUMBER), exist_ok=True)

    main(PATH, NSCANS, COLLECTIONNUMBER, INVENTORYNUMBER, FOLDER,
         CONCORDANCEFILE)
