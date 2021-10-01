#!/usr/bin/env python3

# Copyright (c) 2019-2021 eli fessler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import requests, os,re, html, argparse

from db import adddb, edit_ch, removedb, updater, viewdb , float_conversion , find_id_in_url, downloader, conn


A_VERSION = "0.5.2"


def get_uuid(manga_id):
	headers = {'Content-Type': 'application/json'}
	payload = '{"type": "manga", "ids": [' + str(manga_id) + ']}'
	try:
		r = requests.post("https://api.mangadex.org/legacy/mapping", headers=headers, data=payload)
	except:
		print("Error. Maybe the MangaDex API is down?")
		exit(1)
	try:
		resp = r.json()
		uuid = resp[0]["data"]["attributes"]["newId"]
	except:
		print("Please enter a valid MangaDex manga (not chapter) URL or ID.")
		exit(1)
	return uuid

def get_title(uuid, lang_code):
	r = requests.get("https://api.mangadex.org/manga/{}".format(uuid))
	resp = r.json()
	try:
		title = resp["data"]["attributes"]["title"][lang_code]
	except KeyError: # if no manga title in requested dl language
		try:
			title = resp["data"]["attributes"]["title"]["en"]
		except:
			print("Error - could not retrieve manga title.")
			exit(1)
	return title


def search(title):
	a = requests.get("https://api.mangadex.org/manga/?limit=25&offset=0&title={}".format(title))
	data = a.json()
	end = data['total']

	if end<10:
		end = end
	else:
		end = 10
	for i in range(end):
		ID = data['data'][i]['id']
		Tit = data['data'][i]['attributes']['title']['en']
		Chs = data['data'][i]['attributes']['lastChapter']
		print(f'---\n{i+1}:{Tit}\nID:\"{ID}\"\nLatest_chapter:\"{Chs}"')



def dl(manga_id, lang_code, zip_up, ds):
	uuid = manga_id

	if manga_id.isnumeric():
		uuid = get_uuid(manga_id)

	title = get_title(uuid, lang_code)
	print("\nTITLE: {}".format(html.unescape(title)))

	# check available chapters & get images
	chap_list = []
	r = requests.get("https://api.mangadex.org/manga/{}/feed?limit=0&translatedLanguage[]={}".format(uuid, lang_code))
	try:
		total = r.json()["total"]
	except KeyError:
		print("Error retrieving the chapters list. Did you specify a valid language code?")
		exit(1)

	if total == 0:
		print("No chapters available to download!")
		exit(0)

	offset = 0
	while offset < total: # if more than 500 chapters!
		r = requests.get("https://api.mangadex.org/manga/{}/feed?order[chapter]=asc&order[volume]=asc&limit=500&translatedLanguage[]={}&offset={}".format(uuid, lang_code, offset))
		chaps = r.json()
		for chapter in chaps["data"]:
			chap_num = chapter["attributes"]["chapter"]
			chap_uuid = chapter["id"]
			chap_list.append(("Oneshot", chap_uuid) if chap_num == None else (chap_num, chap_uuid))
		offset += 500
	chap_list.sort(key=float_conversion) # sort numerically by chapter #

	# chap_list is not empty at this point
	print("Available chapters:")
	print(" " + ', '.join(map(lambda x: x[0], chap_list)))

	# i/o for chapters to download
	requested_chapters = []
	dl_list = input("\nEnter chapter(s) to download: ").strip()

	dl_list = [s.strip() for s in dl_list.split(',')]
	chap_list_only_nums = [i[0] for i in chap_list]
	for s in dl_list:
		if "-" in s: # range
			split = s.split('-')
			lower_bound = split[0]
			upper_bound = split[-1]
			try:
				lower_bound_i = chap_list_only_nums.index(lower_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping range {}.".format(lower_bound, s))
				continue # go to next iteration of loop
			try:
				upper_bound_i = chap_list_only_nums.index(upper_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping range {}.".format(upper_bound, s))
				continue
			s = chap_list[lower_bound_i:upper_bound_i+1]
		elif s.lower() == "oneshot":
			if "Oneshot" in chap_list_only_nums:
				oneshot_idxs = [i for i, x in enumerate(chap_list_only_nums) if x == "Oneshot"]
				s = []
				for idx in oneshot_idxs:
					s.append(chap_list[idx])
			else:
				print("Chapter Oneshot does not exist. Skipping.")
				continue
		else: # single number (but might be multiple chapters numbered this)
			chap_idxs = [i for i, x in enumerate(chap_list_only_nums) if x == s]
			if len(chap_idxs) == 0:
				print("Chapter {} does not exist. Skipping.".format(s))
				continue
			s = []
			for idx in chap_idxs:
				s.append(chap_list[idx])
		requested_chapters.extend(s)
		downloader(requested_chapters ,title)


	# get chapter json(s)
	print()






if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	parser = argparse.ArgumentParser()
	parser.add_argument('-s', dest='search', required=False, action='store',
						help='Title of the Manga')
	parser.add_argument("-l", dest="lang", required=False, action="store",
						help="download in specified language code (default: en)", default="en")
	parser.add_argument("-d", dest="datasaver", required=False, action="store_true",
						help="downloads images in lower quality")
	parser.add_argument("-c", dest="cbz", required=False, action="store_true",
						help="packages chapters into .cbz format")
	parser.add_argument('-v', dest='view', required=False, nargs='?', const=' ',
						 help='View local db')
	parser.add_argument('-a', dest='add', required=False, action='store',
						 help='Provide id for manga to add it in db')
	parser.add_argument('-r', dest='remove', required=False, action='store',
						 help='Provide id for manga to remove it from db')
	parser.add_argument('-e', dest='edit', required=False, action='store',
						 help='Edit chapter number')
	parser.add_argument('-u', dest='update', required=False, nargs='?', const=' ',
						 help='Fetchs update from mangadex for manga in db')
	
	args = parser.parse_args()

	lang_code = "en" if args.lang is None else str(args.lang)
	zip_up    = args.cbz
	ds        = args.datasaver

	if args.search:
		 title = args.search
		 search(title)
	elif args.view:
		viewdb()
	elif args.add:
		_id = args.add
		adddb(_id)
	elif args.remove:
		_id = args.remove
		removedb(_id)
	elif args.edit:
		_id = args.edit
		edit_ch(_id)
	elif args.update:
		updater()
	else:
		url = ""
			# prompt for manga
		url = ""
		while url == "":
			url = input("Enter manga URL or ID: ").strip()

		try:
			url_parts = url.split('/')
			manga_id = find_id_in_url(url_parts)
		except:
			print("Error with URL.")
			exit(1)
		dl(manga_id, lang_code, zip_up, ds)
conn.close()