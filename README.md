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
$ python mangadex-dl.py [language_code]
```

For a list of language codes (optional argument; defaults to English), see [the wiki page](https://github.com/frozenpandaman/mangadex-dl/wiki/language-codes).


### Example usage
```
$ ./mangadex-dl.py
mangadex-dl v0.2.2
Enter manga URL: https://mangadex.org/title/286/fullmetal-alchemist

Title: Fullmetal Alchemist
Chapter found in language you requested
Available chapters:
 Oneshot, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12.5, 13, 14, 15, 16, 16.5, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 29.5, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 57.5, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 95.5, 96, 97, 98, 99, 100, 101, 104, 105, 107, 108, 108.01, 108.4, 108.5, 108.6, 108.7


Enter chapter(s) to download: 5-7, oneshot, 2, 1, 105-108.7

Chapters to download:
 Oneshot, 1, 2, 5, 6, 7, 105, 107, 108, 108.01, 108.4, 108.5, 108.6, 108.7
 
Downloading chapter Oneshot...
 Downloaded page 1.
 Downloaded page 2.
... (and so on)
```

### Current limitations
 * The script will download all available releases (in your language) of each chapter specified.

If you are downloading for 10+ minutes straight, you may receive an IP block if trying to browse the site at the same time.