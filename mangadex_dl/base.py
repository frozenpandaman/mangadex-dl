"""
Mangadex-dl: base.py
Basic functions for getting information about manga; to create an output directory.
"""

import os, re
from collections import namedtuple

from .download import *

def search_manga(title, language):
	data = urllib.parse.urlencode({"title": title})
	response = get_json("https://api.mangadex.org/manga?{}".format(data))
	
	return [get_manga_info(manga["id"], language) for manga in response["data"]]

def get_manga_info(manga_url, language):
	manga_info = namedtuple("manga_info", ["uuid", "title", "title_en", "authors", "artists", "year",
					       "status", "last_volume", "last_chapter", "demographic",
					       "content_rating", "tags", "description", "original_language"])
	manga_info.uuid = _get_uuid(manga_url)
	
	response = get_json("https://api.mangadex.org/manga/{}".format(manga_info.uuid))

	manga_info.year = response["data"]["attributes"]["year"]
	manga_info.status = response["data"]["attributes"]["status"]
	manga_info.last_volume = response["data"]["attributes"]["lastVolume"]
	manga_info.last_chapter = response["data"]["attributes"]["lastChapter"]
	manga_info.content_rating = response["data"]["attributes"]["contentRating"]
	manga_info.original_language = response["data"]["attributes"]["originalLanguage"]
	manga_info.demographic = response["data"]["attributes"]["publicationDemographic"]
	
	manga_info.tags = _get_tags(response)
	manga_info.description = _get_description(response, language)
	manga_info.authors, manga_info.artists = _get_authors(response)
	manga_info.title, manga_info.title_en = _get_title(response, language)
	
	return manga_info

def get_chapters_list(manga_uuid, language):
	chapters_info = get_chapters_info(manga_uuid, language)
	chapters_list = []
	offset = 0
	
	if chapters_info["total"] == 0:
		raise ValueError("No chapters available to download!")
	
	while offset < chapters_info["total"]: # if more than 500 chapters!
		response = get_json("https://api.mangadex.org/manga/{}/feed"\
				    "?order[volume]=asc&order[chapter]=asc&limit=500"\
				    "&translatedLanguage[]={}&offset={}"\
				    "&contentRating[]=safe"\
				    "&contentRating[]=suggestive"\
				    "&contentRating[]=erotica"\
				    "&contentRating[]=pornographic"
				    .format(manga_uuid, language, offset))
		chapters_list += response["data"]
		offset += 500
	
	unavailable_list = []
	for chapter in chapters_list:
		if chapter["attributes"]["externalUrl"] != None:
			unavailable_list.append(chapter)
	if len(unavailable_list) != 0:
		for chapter in unavailable_list:
			chapters_list.remove(chapter)
		print("Warning: {} chapters are not available from Mangadex.org.".format(len(unavailable_list)))
	
	return chapters_list

def get_chapters_info(manga_uuid, language):
	return get_json("https://api.mangadex.org/manga/{}/feed"\
			"?limit=0&translatedLanguage[]={}"\
			"&contentRating[]=safe"\
			"&contentRating[]=suggestive"\
			"&contentRating[]=erotica"\
			"&contentRating[]=pornographic"
			.format(manga_uuid, language))

def create_manga_directory(user_directory, manga_title, manga_uuid):
	out_directory = check_output_directory(user_directory)
	manga_directory = os.path.join(out_directory, manga_title)
	
	if not os.path.exists(manga_directory):
		try:
			os.makedirs(manga_directory)
		except OSError:
			print("Warning: Cannot create manga directory. Changed name to UUID.")
			manga_directory = os.path.join(out_directory, "Manga {}".format(manga_uuid))
			os.makedirs(manga_directory)
	return manga_directory

def check_output_directory(user_directory):
	out_directory = os.path.abspath(".")
	
	if os.path.isdir(user_directory):
		out_directory = os.path.abspath(user_directory)
	
	return out_directory

def _get_uuid(manga_url):
	regex = re.compile("\w{8}-\w{4}-\w{4}-\w{4}-\w{12}")
	manga_uuid_match = re.findall(regex, manga_url)
	if manga_uuid_match:
		return manga_uuid_match[0]
	else:
		raise ValueError("Cannot retrieve manga UUID")

def _get_title(response, language):
	title_en = response["data"]["attributes"]["title"]["en"]
	title = title_en
	
	if language in response["data"]["attributes"]["title"]:
		title = response["data"]["attributes"]["title"][language]
	else:
		for altTitle in response["data"]["attributes"]["altTitles"]:
			if language in altTitle:
				title = altTitle[language]
	return title, title_en

def _get_description(response, language):
	desc = "Description missing"
	if "en" in response["data"]["attributes"]["description"]:
		desc = response["data"]["attributes"]["description"]["en"]
	
	if language in response["data"]["attributes"]["description"]:
		desc = response["data"]["attributes"]["description"][language]
	
	return desc

def _get_tags(response):
	tags = namedtuple("manga_tags", ["format", "theme", "genre"])
	tags.format = []
	tags.theme = []
	tags.genre = []
	for tag in response["data"]["attributes"]["tags"]:
		if tag["attributes"]["group"] == "format":
			tags.format.append(tag["attributes"]["name"]["en"])
		elif tag["attributes"]["group"] == "theme":
			tags.theme.append(tag["attributes"]["name"]["en"])
		elif tag["attributes"]["group"] == "genre":
			tags.genre.append(tag["attributes"]["name"]["en"])
	
	return tags
		
def _get_authors(response):
	"""
	This function returns a maximum of 3 authors only. Getting a big list from anthologies is too long.
	"""
	authors = []
	artists = []
	for relation in response["data"]["relationships"]:
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

def _get_person_info(person_id):
	return get_json("https://api.mangadex.org/author/{}".format(person_id))["data"]["attributes"]["name"]
