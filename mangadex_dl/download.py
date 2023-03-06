"""
Mangadex-dl: download.py
Handling low-level HTTP requests and loading images.
"""

import os, time, json, concurrent.futures, http.client, urllib.parse
from collections import deque

def url_request(url):
    # let's try three times
    error = None
    for i in range(3):
        try:
            # This function uses http.client instead of urllib.requets
            # since urllib often returns an IncompleteRead
            # https://github.com/python/cpython/issues/83552
            # (it's still better to use requests, but...)
            # (upd: oh well, even requests 2.x does not guarantee this)
            _DownloadLimits.check()
            
            data = bytes()
            url_parse = urllib.parse.urlparse(url)
            conn = http.client.HTTPSConnection(url_parse.netloc, timeout=60)
            conn.request("GET", urllib.parse.urlunsplit(["", "", url_parse.path, url_parse.query, ""]))
            response = conn.getresponse()
            
            if response.status != 200:
                raise http.client.HTTPException("Error: {}, {}".format(response.status,response.reason))

            while chunk := response.read(1024):
                data += chunk
            
            # Mangadex doesn't set Transfer-Encoding, so...
            if response.getheader("content-length") != None:
                if len(data) != int(response.getheader("content-length")):
                    raise http.client.IncompleteRead(data)
            conn.close()
            return data
        except Exception as err:
            error = err
            time.sleep(1 if i != 2 else 10)
    raise error

def get_json(url):
    return json.loads(url_request(url).decode("utf-8"))

def download_chapters(requested_chapters, out_directory, is_datasaver, gui={"set": False}):
    chapter_count = 1
    chapter_count_max = len(requested_chapters)
    
    for chapter in requested_chapters:
        chapter_number = chapter["attributes"]["chapter"] if chapter["attributes"]["chapter"] != None else "Oneshot"
        chapter_name = chapter["attributes"]["title"] if chapter["attributes"]["title"] != None else ""
        chapter_volume = chapter["attributes"]["volume"] if chapter["attributes"]["volume"] != None else "Unknown"
        
        if gui["set"]:
            # This 'gui' object stores data to update progressbars and text in GUI
            gui["progress_chapter"].set((chapter_count/chapter_count_max)*100)
            gui["progress_chapter_text"].set("[ {} / {} ]".format(chapter_count, chapter_count_max))
        else:
            # Otherwise, print the console output
            print("\nDownloading chapter [{:3}/{:3}] Ch.{} {}".format(chapter_count, chapter_count_max, chapter_number, chapter_name))
        
        chapter_json = get_json("https://api.mangadex.org/at-home/server/{}".format(chapter["id"]))
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
            print("  Chapter {} is not available from Mangadex.".format(chapter_number))
            continue
        
        directory_chapter = _create_chapter_directory(out_directory, chapter_volume, chapter_number)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_list = []
            if gui["set"]:
                gui["download_futures"] = future_list
            
            for image_url in image_url_list:
                future_list.append(executor.submit(_download_image, base_url + image_url, image_count, directory_chapter))
                image_count += 1
            
            for future in concurrent.futures.as_completed(future_list):
                image_count_downloaded += 1
                if gui["set"]:
                    gui["progress_page"].set((image_count_downloaded/image_count_max)*100)
                    gui["progress_page_text"].set("[ {} / {} ]".format(image_count_downloaded, image_count_max))
                else:
                    print("\r  Downloaded images [{:3}/{:3}]...".format(image_count_downloaded, image_count_max), end="")
        
        if gui["set"]:
            gui["progress_page"].set(0)
            gui["progress_page_text"].set("[ - / - ]")
        
        chapter_count += 1
    return

def _download_image(full_url, image_count, directory_chapter):
    image_file_path = os.path.join(directory_chapter, "{:03d}{}".format(image_count, os.path.splitext(full_url)[1]))
    try:
        data = url_request(full_url)
        with open(image_file_path, mode="wb") as image_file:
            image_file.write(data)
    except Exception as err:
        print("File download failed\n({})\n[{}]\n".format(image_file_path, err))
    return

def _create_chapter_directory(out_directory, chapter_volume, chapter_number):
    directory_chapter = os.path.join(out_directory, "Volume {}".format(chapter_volume), "Chapter {}".format(chapter_number))
    if os.path.exists(directory_chapter):
        # name folders like "Chapter 1 (2)"
        for i in range(1, 100):
            temp_path = "{} ({})".format(directory_chapter, i)
            if not os.path.exists(temp_path):
                directory_chapter = temp_path
                break
    os.makedirs(directory_chapter)
    return directory_chapter

class _DownloadLimits:
    last_requests = deque(maxlen=5)
    
    def check():
        if len(_DownloadLimits.last_requests) == 5:
            interval = time.time() - _DownloadLimits.last_requests[0]
            if interval < 1:
                time.sleep(1 - interval)
        _DownloadLimits.last_requests.append(time.time())
        return
