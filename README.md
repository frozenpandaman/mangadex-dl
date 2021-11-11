# mangadex-dl

A Python script to download manga from [MangaDex.org](https://mangadex.org/).

## Requirements
  * [Python 3.4+](https://www.python.org/downloads/) (or [install via Homebrew](https://docs.python-guide.org/starting/install3/osx/) on macOS)
  * Python's [Requests](https://docs.python-requests.org/en/latest/) library

## Installation & usage
```
$ git clone https://github.com/frozenpandaman/mangadex-dl
$ pip install requests
$ cd mangadex-dl/
$ python mangadex-dl.py [-l language_code] [-d] [-a] [-o dl_dir]
```

You can also execute the script via `./mangadex-dl.py` on macOS and Linux. On Windows, use a backslash.

### Optional flags

* `-l`: Download releases in a language other than English. For a list of language codes, see the [wiki page](https://github.com/frozenpandaman/mangadex-dl/wiki/language-codes).
* `-d`: Download page images in lower quality (higher JPG compression/"data saver").
* `-a`: Package downloaded chapters into .cbz ([comic book archive](https://en.wikipedia.org/wiki/Comic_book_archive)) files.
* `-o`: Use a custom output directory name to save downloaded chapters. Defaults to "download".

### Example usage
```
$ ./mangadex-dl.py
mangadex-dl v0.6
Enter manga URL: https://mangadex.org/title/58be6aa6-06cb-4ca5-bd20-f1392ce451fb/yotsuba-to

Title: Yotsuba to!
Available chapters:
 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
 23, 24, 25, 26, 27, 27.5, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 54.2, 55, 56, 57, 58,
 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 69.2, 70, 71, 72, 73, 74, 75, 76,
 77, 78, 79, 79.2, 80, 81, 81.2, 81.3, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91,
 92, 93, 94, 95, 96, 97, 98, 99, 100, 100, 100, 101, 102, 103, 104, 105

Enter chapter(s) to download: 1, 4-7

Downloading chapter 1...
 Downloaded page 1.
 Downloaded page 2.
... (and so on)
```

### Current limitations
 * The script will download all available releases (in your language) of each chapter specified.

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)