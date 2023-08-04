"""
Mangadex-dl: archive.py
Functions for archiving the manga directory.
"""

import shutil
import zipfile
from pathlib import Path

def archive_manga(manga_dir: Path, archive_mode: str, is_keep: bool, ext: str,
                  gui: dict = {}) -> None:

    dir_list = _find_directories(manga_dir, archive_mode)

    dir_archived = 0
    dir_max = len(dir_list)

    if dir_max == 0:
        print("Looks like there is nothing to archive.", end="", flush=True)
        return

    for directory in dir_list:
        _archive_directory(directory, ext, is_keep)
        dir_archived += 1

        if gui.get("set", False):
            gui["progress_chapter"].set(
                (dir_archived/dir_max)*100)
            gui["progress_chapter_text"].set(
                f"[ {dir_archived} / {dir_max} ]")
        else:
            print(f"\r  Archiving [{dir_archived:3}/{dir_max:3}]...", end="")

def _archive_directory(directory: Path, ext: str, is_keep: bool = True) -> None:
    zip_name = directory.with_suffix(directory.suffix + f".{ext}")

    with zipfile.ZipFile(zip_name, mode="w",
                         compression=zipfile.ZIP_STORED,
                         allowZip64=True) as zip_file:
        for filename in directory.glob("**/*"):
            zip_file.write(filename, filename.relative_to(directory))

    if not is_keep:
        shutil.rmtree(directory)

def _find_directories(manga_dir: Path, archive_mode: str) -> list[Path]:
    dir_list = []

    if archive_mode == "manga":
        # archive whole manga dir
        dir_list.append(manga_dir)
    elif archive_mode == "volume":
        # archive volume directories
        dir_list += manga_dir.glob("*/")
    else:
        # archive chapter directories
        dir_list += manga_dir.glob("*/*/")

    # skip directories that have already been archived before
    dir_list = list(filter(lambda f: not (f.with_suffix(".zip").is_file()
                                          or f.with_suffix(".cbz").is_file()), dir_list))
    return dir_list
