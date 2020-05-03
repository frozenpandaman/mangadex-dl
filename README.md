# mangadex-dl

A Python script to download manga from [MangaDex.org](https://mangadex.org).

## Requirements
  * [Python 3.4+](https://www.python.org/downloads/)
  * [cloudscraper](https://github.com/VeNoMouS/cloudscraper)
  * [Node.js](https://nodejs.org/en/download/package-manager/)

## Installation & usage
```
$ git clone https://github.com/frozenpandaman/mangadex-dl
$ pip install cloudscraper
$ cd mangadex-dl/
$ python mangadex-dl.py
```

For a list of language codes (optional argument; defaults to English), see [the wiki page](https://github.com/frozenpandaman/mangadex-dl/wiki/language-codes).

If you prefer commandline arguments, just run:
```
$ python mangadex-dl.py --help
```

### Example usage
```
$ ./mangadex-dl.py
mangadex-dl v0.3
Enter manga URL: https://mangadex.org/title/311/yotsuba-to
Do you want to package chapters into .cbz?: (y/N) y
Enter desired language: (gb)

Title: Yotsuba to!
Chapter found in language you requested
Available chapters:
 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
 23, 24, 25, 26, 27, 27.5, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 54.2, 55, 56, 57, 58,
 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 69.2, 70, 71, 72, 73, 74, 75, 76,
 77, 78, 79, 79.2, 80, 81, 81.2, 81.3, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
 92, 93, 94, 95, 96, 97, 98, 99, 100, 100, 101, 102, 103, 104, 104, 105

Enter chapter(s) to download: 1, 4-7

Downloading chapter 1...
 Downloaded page 1.
 Downloaded page 2.
... (and so on)
```

### Current limitations
 * The script will download all available releases (in your language) of each chapter specified.

If you are downloading for 10+ minutes straight, you may receive an IP block if trying to browse the site at the same time.