"""
Mangadex-dl: download.py
Handling low-level HTTP requests and loading images.
"""

import time
import logging
import requests
import concurrent.futures
from pathlib import Path
from collections import deque

from mangadex_dl.instance import SESSION

def url_request(url, params={}, json=False):
    error = None
    for i in range(5):
        try:
            _DownloadLimits.check()

            r = SESSION.get(url, timeout=(10, 120), params=params)

            r.raise_for_status()

            if json:
                response = r.json()
            else:
                response = r.content

            if not json:
                content_length = r.headers.get("content-length")
                received_bytes = len(response)

                if content_length and received_bytes != int(content_length):
                    raise requests.RequestException(
                        "IncompleteRead: "\
                        f"{received_bytes} from {content_length}")

            return response
        except Exception as err:
            error = err
            time.sleep(1 if i < 3 else 10)
    logging.error(f"URL Request: {error}")
    raise error

def get_json(url, params={}):
    return url_request(url, params=params, json=True)

def download_chapters(requested_chapters,
                      out_directory,
                      is_datasaver,
                      gui={"set": False}):

    chapter_count = 1
    chapter_count_max = len(requested_chapters)

    for chapter in requested_chapters:
        chapter_number = chapter["attributes"]["chapter"] or "Oneshot"
        chapter_volume = chapter["attributes"]["volume"] or "Unknown"
        chapter_name = chapter["attributes"]["title"] or ""

        if gui["set"]:
            # This 'gui' object stores data to update progressbars and text in GUI
            gui["progress_chapter"].set((chapter_count/chapter_count_max)*100)
            gui["progress_chapter_text"].set(f"[ {chapter_count} / {chapter_count_max} ]")
        else:
            # Otherwise, print the console output
            print("\nDownloading chapter [{:3}/{:3}] Ch.{} {}".format(chapter_count,
                                                                      chapter_count_max,
                                                                      chapter_number,
                                                                      chapter_name))

        chapter_json = get_json(f"https://api.mangadex.org/at-home/server/{chapter['id']}")

        # "https://uploads.mangadex.org/data/3ed5ed7ba35891cc9902f94e8488a51a/"
        base_url = "{}/{}/{}/".format(chapter_json["baseUrl"],
                                      "data-saver" if is_datasaver else "data",
                                      chapter_json["chapter"]["hash"])

        # ["k6-413f22d5e1a26c32f621ead08a26c89b199c9266b9e76780c13548df0d8fcdf9.png", ...]
        image_url_list = chapter_json["chapter"]["dataSaver"] if is_datasaver else chapter_json["chapter"]["data"]

        image_count = 1
        image_count_downloaded = 0
        image_count_max = len(image_url_list)

        if image_count_max == 0:
            print(f"  Chapter {chapter_number} is not available from Mangadex.")
            continue

        directory_chapter = _create_chapter_directory(out_directory, chapter_volume, chapter_number)

        thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        if gui["set"]:
            gui["thread_pool"] = thread_pool
        with thread_pool as executor:
            future_list = []

            for image_url in image_url_list:
                future_list.append(executor.submit(_download_image,
                                                   base_url + image_url,
                                                   image_count,
                                                   directory_chapter))
                image_count += 1

            for future in concurrent.futures.as_completed(future_list):
                image_count_downloaded += 1
                if gui["set"]:
                    gui["progress_page"].set((image_count_downloaded/image_count_max)*100)
                    gui["progress_page_text"].set(f"[ {image_count_downloaded} / {image_count_max} ]")
                else:
                    print(f"\r  Downloaded images [{image_count_downloaded:3}/{image_count_max:3}]...", end="")

        if gui["set"]:
            gui["progress_page"].set(0)
            gui["progress_page_text"].set("[ - / - ]")

        chapter_count += 1

def _download_image(full_url, image_count, directory_chapter):

    image_file_path = directory_chapter / "{:03d}{}".format(image_count, Path(full_url).suffix)
    try:
        data = url_request(full_url)
        with open(image_file_path, mode="wb") as image_file:
            image_file.write(data)
    except Exception as err:
        logging.error(f"File download failed ({image_file_path}): {err}")

def _create_chapter_directory(out_directory, chapter_volume, chapter_number):
    directory_chapter = out_directory / f"Volume {chapter_volume}" / f"Chapter {chapter_number}"

    if directory_chapter.is_dir():
        # name folders like "Chapter 1 (2)"
        for i in range(1, 100):
            temp_path = Path(f"{directory_chapter} ({i})")
            if not temp_path.is_dir():
                directory_chapter = temp_path
                break

    directory_chapter.mkdir(parents=True, exist_ok=True)
    return directory_chapter

class _DownloadLimits:
    last_requests = deque(maxlen=5)

    @classmethod
    def check(cls):
        if len(cls.last_requests) == 5:
            interval = time.time() - cls.last_requests[0]
            if interval < 1:
                time.sleep(1 - interval)
        cls.last_requests.append(time.time())
