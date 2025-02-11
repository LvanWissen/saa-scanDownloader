# saa-scanDownloader
Download scans from the Amsterdam City Archives. 

## How to use

_First install any dependencies with `pip install -r requirements.txt`._

```bash
Usage:
    downloadScans.py ead <url> <folder>
    downloadScans.py ead <url> <folder> --concordance False
    downloadScans.py file <collectionNumber> <inventoryNumber> <path> <folder>
    downloadScans.py file <collectionNumber> <inventoryNumber> <path> <folder> --concordance False
    downloadScans.py (-h | --help)

Arguments:
  url               URL to an EAD file.
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
```

### Example

Download an entire Collection from an EAD URL:

```bash
$ python downloadScans.py ead "https://archief.amsterdam/archives/xml/5001.ead.xml" data
```

```bash
$ python downloadScans.py ead "https://archief.amsterdam/archives/xml/5001.ead.xml" data --concordance False
```

Download a single inventory number from a collection:

```bash
$ python downloadScans.py file 30398 11 1.11 data/jpg
```

```bash
$ python downloadScans.py file 30398 11 1.11 data/jpg --concordance False
```
