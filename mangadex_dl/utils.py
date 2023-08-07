"""
Mangadex-dl: utils.py
Basic functions for getting information about manga;
"""

import re
import logging
from pathlib import Path
from functools import lru_cache
from collections import namedtuple

import mangadex_dl.download as dl

def get_uuid(manga_url):
    regex = re.compile(r"\w{8}-\w{4}-\w{4}-\w{4}-\w{12}")
    manga_uuid_match = re.findall(regex, manga_url)
    if manga_uuid_match:
        return manga_uuid_match[0]
    return None

def search_manga(title, language):
    res = dl.get_json("https://api.mangadex.org/manga", {"title": title})

    return [get_manga_info(manga["id"], language) for manga in res["data"]]

def get_manga_info(manga_url, language):
    manga_info = namedtuple("manga_info", ["uuid", "title", "title_en",
                                           "authors", "artists",
                                           "year", "status",
                                           "last_volume", "last_chapter",
                                           "demographic", "content_rating",
                                           "tags", "description",
                                           "original_language"])
    manga_info.uuid = get_uuid(manga_url)

    res = dl.get_json(f"https://api.mangadex.org/manga/{manga_info.uuid}")

    manga_info.year = res["data"]["attributes"]["year"]
    manga_info.status = res["data"]["attributes"]["status"]
    manga_info.last_volume = res["data"]["attributes"]["lastVolume"]
    manga_info.last_chapter = res["data"]["attributes"]["lastChapter"]
    manga_info.content_rating = res["data"]["attributes"]["contentRating"]
    manga_info.original_language = res["data"]["attributes"]["originalLanguage"]
    manga_info.demographic = res["data"]["attributes"]["publicationDemographic"]

    manga_info.tags = _get_tags(res)
    manga_info.description = _get_description(res, language)
    manga_info.authors, manga_info.artists = _get_authors(res)
    manga_info.title, manga_info.title_en = _get_title(res, language)

    return manga_info

def get_chapters_list(manga_uuid, language):
    chapters_info = get_chapters_info(manga_uuid, language)
    chapters_list = []
    offset = 0

    if chapters_info["total"] == 0:
        raise ValueError("No chapters available to download!")

    while offset < chapters_info["total"]: # if more than 500 chapters!
        res = dl.get_json(f"https://api.mangadex.org/manga/{manga_uuid}/feed"\
                          "?order[volume]=asc&order[chapter]=asc&limit=500"\
                          f"&translatedLanguage[]={language}&offset={offset}"\
                          "&contentRating[]=safe"\
                          "&contentRating[]=suggestive"\
                          "&contentRating[]=erotica"\
                          "&contentRating[]=pornographic")
        chapters_list += res["data"]
        offset += 500

    unavailable_list = []

    for chapter in chapters_list:
        if chapter["attributes"]["externalUrl"]:
            unavailable_list.append(chapter)

    if len(unavailable_list) != 0:
        s = f"{len(unavailable_list)} chapter(s) are not available:\n["
        s += ", ".join(i["attributes"]["chapter"] for i in unavailable_list)
        s += "]"
        logging.warning(s)

        for chapter in unavailable_list:
            chapters_list.remove(chapter)

    return chapters_list

def get_chapters_info(manga_uuid, language):
    return dl.get_json(f"https://api.mangadex.org/manga/{manga_uuid}/feed"\
                       f"?limit=0&translatedLanguage[]={language}"\
                       "&contentRating[]=safe"\
                       "&contentRating[]=suggestive"\
                       "&contentRating[]=erotica"\
                       "&contentRating[]=pornographic")

def create_manga_directory(user_dir,
                           manga_title: str,
                           manga_uuid: str) -> Path:

    out_dir = check_output_directory(user_dir)
    manga_dir = out_dir / manga_title

    if not manga_dir.is_dir():
        try:
            manga_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            logging.warning("Cannot create manga directory. "\
                            "Changed name to UUID.")
            manga_dir = out_dir / f"Manga {manga_uuid}"
            manga_dir.mkdir(parents=True, exist_ok=True)

    return manga_dir

def check_output_directory(user_dir):
    out_dir = Path(".")

    if user_dir.is_dir():
        out_dir = user_dir.resolve()

    return out_dir

def _get_title(res, language):
    title_dict = res["data"]["attributes"]["title"]
    alt_title_dict = res["data"]["attributes"]["altTitles"]

    if "en" in title_dict:
        title_en = title_dict["en"]
    elif len(title_dict) != 0:
        title_en = next(iter(title_dict.values()))
    else:
        title_en = res["data"]["id"]
    title = title_en

    if language in title_dict:
        title = title_dict[language]
    else:
        for alt_title in alt_title_dict:
            if language in alt_title:
                title = alt_title[language]

    return title, title_en

def _get_description(res, language):
    desc_dict = res["data"]["attributes"]["description"]
    desc = "Description missing"

    if "en" in desc_dict:
        desc = desc_dict["en"]
    if language in desc_dict:
        desc = desc_dict[language]

    return desc

def _get_tags(res):
    tags = namedtuple("manga_tags", ["format", "theme", "genre"])
    tags.format = []
    tags.theme = []
    tags.genre = []

    for tag in res["data"]["attributes"]["tags"]:
        tag_group = tag["attributes"]["group"]

        if "en" in tag["attributes"]["name"]:
            tag_name = tag["attributes"]["name"]["en"]
        else:
            tag_name = next(iter(tag["attributes"]["name"].values()))

        if tag_group == "format":
            tags.format.append(tag_name)
        elif tag_group == "theme":
            tags.theme.append(tag_name)
        elif tag_group == "genre":
            tags.genre.append(tag_name)

    return tags

def _get_authors(res):
    """
    This function returns a maximum of 3 authors only.
    Getting a big list from anthologies is too long.
    """
    authors = []
    artists = []
    for relation in res["data"]["relationships"]:
        if relation["type"] == "author":
            if len(authors) < 3:
                authors.append(_get_person_info(relation["id"]))
            elif len(authors) == 3:
                authors.append("and others...")
            continue

        if relation["type"] == "artist":
            if len(artists) < 3:
                artists.append(_get_person_info(relation["id"]))
            elif len(authors) == 3:
                artists.append("and others...")

    return authors, artists

@lru_cache(maxsize=16)
def _get_person_info(person_id):
    res = dl.get_json(f"https://api.mangadex.org/author/{person_id}")
    return res["data"]["attributes"]["name"]
