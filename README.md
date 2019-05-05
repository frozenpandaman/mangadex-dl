# mangadex-dl

A Python script to download manga from [MangaDex.org](https://mangadex.org).

## Requirements
  * [Python 3](https://www.python.org/downloads/)
  * [cloudscraper](https://github.com/VeNoMouS/cloudscraper)
  * [Node.js](https://nodejs.org/en/download/package-manager/)

## Installation & usage
```
$ git clone https://github.com/frozenpandaman/mangadex-dl
$ pip install cloudscraper
$ cd mangadex-dl/
$ python mangadex-dl.py
```

### Example usage
```
$ ./mangadex-dl.py 
mangadex-dl v0.1
Enter manga URL: https://mangadex.org/title/311/yotsuba-to

Title: Yotsuba to!
Enter chapter(s) to download: 1, 4-7
Downloading chapter 1...
 Downloaded page 1.
 Downloaded page 2.
... (and so on)
```

Only English releases are currently supported, and the script will download all available releases of each chapter specified.

If you are downloading for 10+ minutes straight, you may receive an IP block if trying to browse the site at the same time.