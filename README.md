# saa-scanDownloader
Download scans from the Amsterdam City Archives. 

## How to use
```bash
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
```

### Example
```bash
$ python downloadScans.py 30398 11 1.11 69 data/jpg
```

```bash
$ python downloadScans.py 30398 11 1.11 69 data/jpg --concordance False
```