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

import cloudscraper
import time, os, sys, re, json, html, random

A_VERSION = "0.3"

def pad_filename(str):
	digits = re.compile('(\\d+)')
	pos = digits.search(str)
	if pos:
		return str[1:pos.start()] + pos.group(1).zfill(3) + str[pos.end():]
	else:
		return str

def float_conversion(x):
	try:
		x = float(x)
	except ValueError: # empty string for oneshot
		x = 0
	return x

def zpad(num):
	if "." in num:
		parts = num.split('.')
		return "{}.{}".format(parts[0].zfill(3), parts[1])
	else:
		return num.zfill(3)

def dl(manga_id, lang_code, tld="org"):
	if len(tld) == 1: #
		tld = "org"
	# grab manga info json from api
	scraper = cloudscraper.create_scraper()
	try:
		r = scraper.get("https://api.mangadex.{}/v2/manga/{}/?include=chapters".format(tld, manga_id))
		jason = json.loads(r.text)
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("CloudFlare error: {}".format(err))
		exit(1)
	except:
		print("Error with URL.")
		exit(1)

	try:
		title = jason["data"]["manga"]["title"]
	except:
		print("Please enter a valid MangaDex manga (not chapter) URL or ID.")
		exit(1)
	print("\nTITLE: {}".format(html.unescape(title)))

	# check available chapters
	chapters = []
	for i in jason["data"]["chapters"]:
		if i["language"] == lang_code:
			chapters.append(i["chapter"])
	chapters.sort(key=float_conversion) # sort numerically by chapter #

	chapters = ["Oneshot" if x == "" else x for x in chapters]
	if len(chapters) == 0:
		print("No chapters available to download!")
		exit(0)
	else:
		print("Available chapters:")
		print(" " + ', '.join(map(str, chapters)))

	# i/o for chapters to download
	requested_chapters = []
	chap_list = input("\nEnter chapter(s) to download: ").strip()
	chap_list = [s for s in chap_list.split(',')]
	for s in chap_list:
		s = s.strip()
		if "-" in s:
			split = s.split('-')
			lower_bound = split[0]
			upper_bound = split[1]
			try:
				lower_bound_i = chapters.index(lower_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping {}.".format(lower_bound, s))
				continue # go to next iteration of loop
			try:
				upper_bound_i = chapters.index(upper_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping {}.".format(upper_bound, s))
				continue
			s = chapters[lower_bound_i:upper_bound_i+1]
		elif s.lower() == "oneshot":
			if "Oneshot" in chapters:
				s = ["Oneshot"]
			else:
				print("Chapter {} does not exist. Skipping.".format(s))
		else:
			try:
				s = [chapters[chapters.index(s)]]
			except ValueError:
				print("Chapter {} does not exist. Skipping.".format(s))
				continue
		requested_chapters.extend(s)

	# find out which are availble to dl
	chaps_to_dl = []
	chapter_num = None
	for i in jason["data"]["chapters"]:
		try:
			chapter_num = str(float(i["chapter"]))
			chapter_num = re.sub('.0$', '', chapter_num) # only replace at end (not chapter #s with decimals)
		except: # oneshot
			if "Oneshot" in requested_chapters and i["language"] == lang_code:
				chaps_to_dl.append(("Oneshot", i["id"]))
		if chapter_num in requested_chapters and i["language"] == lang_code:
			chaps_to_dl.append((str(chapter_num), i["id"]))
	chaps_to_dl.sort(key = lambda x: float_conversion(x[0]))

	# get chapter(s) json
	print()
	for chapter_info in chaps_to_dl:
		print("Downloading chapter {}...".format(chapter_info[0]))
		r = scraper.get("https://api.mangadex.{}/v2/chapter/{}/".format(tld, chapter_info[1]))
		chapter = json.loads(r.text)

		# get url list
		images = []
		server = chapter["data"]["server"]
		if "mangadex." not in server:
			server = chapter["data"]["serverFallback"] # https://s2.mangadex.org/data/
		hashcode = chapter["data"]["hash"]
		for page in chapter["data"]["pages"]:
			images.append("{}{}/{}".format(server, hashcode, page))

		# create combined group name
		groups = ""
		for i in range(len(chapter["data"]["groups"])):
			if i > 0:
				groups += " & "
			groups += chapter["data"]["groups"][i]["name"]
		groupname = re.sub('[/<>:"/\\|?*]', '-', groups)

		# download images
		for pagenum, url in enumerate(images, 1):
			filename = os.path.basename(url)
			ext = os.path.splitext(filename)[1]

			title = re.sub('[/<>:"/\\|?*]', '-', title)
			chapnum = zpad(chapter_info[0])
			if chapnum != "Oneshot":
				chapnum = 'c' + chapnum
			dest_folder = os.path.join(os.getcwd(), "download", title, "{} [{}]".format(chapnum, groupname))
			if not os.path.exists(dest_folder):
				os.makedirs(dest_folder)
			dest_filename = pad_filename("{}{}".format(pagenum, ext))
			outfile = os.path.join(dest_folder, dest_filename)

			r = scraper.get(url)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
					print(" Downloaded page {}.".format(pagenum))
			else:
				# silently try again
				time.sleep(3)
				r = scraper.get(url)
				if r.status_code == 200:
					with open(outfile, 'wb') as f:
						f.write(r.content)
						print(" Downloaded page {}.".format(pagenum))
				else:
					print(" Skipping download of page {} - error {}.".format(pagenum, r.status_code))
			time.sleep(1)

	print("Done!")

if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	if len(sys.argv) > 1:
		lang_code = sys.argv[1]
	else:
		lang_code = "gb"

	url = ""
	while url == "":
		url = input("Enter manga URL or ID: ").strip()
	try:
		manga_id = re.search("[0-9]+", url).group(0)
		split_url = url.split("/")
		for segment in split_url:
			if "mangadex" in segment:
				url = segment.split('.')
	except:
		print("Error with URL.")
		exit(1)

	dl(manga_id, lang_code, url[-1])