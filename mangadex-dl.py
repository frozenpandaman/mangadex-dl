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

import requests, time, os, sys, re, json, html, zipfile, argparse, shutil

A_VERSION = "0.6"

def pad_filename(str):
	digits = re.compile('(\\d+)')
	pos = digits.search(str)
	if pos:
		return str[1:pos.start()] + pos.group(1).zfill(3) + str[pos.end():]
	else:
		return str

def float_conversion(tupl):
	try:
		x = float(tupl[0]) # (chap_num, chap_uuid)
	except ValueError: # empty string for oneshot
		x = 0
	return x

def find_id_in_url(url_parts):
	for part in url_parts:
		if "-" in part:
			return part

def zpad(num):
	if "." in num:
		parts = num.split('.')
		return "{}.{}".format(parts[0].zfill(3), parts[1])
	else:
		return num.zfill(3)

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
			# lookup in altTitles
			alt_titles = {}
			titles = resp["data"]["attributes"]["altTitles"]
			for val in titles:
				alt_titles.update(val)
			title = alt_titles[lang_code]
		except:
			# fallback to English title
			try:
				title = resp["data"]["attributes"]["title"]["en"]
			except:
				print("Error - could not retrieve manga title.")
				exit(1)
	return title

def uniquify(title, chapnum, groupname, basedir):
	counter = 1
	dest_folder = os.path.join(os.getcwd(), basedir, title, "{} [{}]".format(chapnum, groupname))
	while os.path.exists(dest_folder):
		dest_folder = os.path.join(os.getcwd(), basedir, title, "{}-{} [{}]".format(chapnum, counter, groupname))
		counter += 1
	return dest_folder

def dl(manga_id, lang_code, zip_up, ds, outdir):
	uuid = manga_id

	if manga_id.isnumeric():
		uuid = get_uuid(manga_id)

	title = get_title(uuid, lang_code)
	print("\nTITLE: {}".format(html.unescape(title)))

	# check available chapters & get images
	chap_list = []
	content_ratings = "contentRating[]=safe&contentRating[]=suggestive&contentRating[]=erotica&contentRating[]=pornographic"
	r = requests.get("https://api.mangadex.org/manga/{}/feed?limit=0&translatedLanguage[]={}&{}".format(uuid, lang_code, content_ratings))
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
		r = requests.get("https://api.mangadex.org/manga/{}/feed?order[chapter]=asc&order[volume]=asc&limit=500&translatedLanguage[]={}&offset={}&{}".format(uuid, lang_code, offset, content_ratings))
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

	# get chapter json(s)
	print()
	for chapter_info in requested_chapters:
		print("Downloading chapter {}...".format(chapter_info[0]))
		r = requests.get("https://api.mangadex.org/chapter/{}".format(chapter_info[1]))
		chapter = json.loads(r.text)

		r = requests.get("https://api.mangadex.org/at-home/server/{}".format(chapter_info[1]))
		baseurl = r.json()["baseUrl"]

		# make url list
		images = []
		accesstoken = ""
		chaphash = chapter["data"]["attributes"]["hash"]
		datamode = "dataSaver" if ds else "data"
		datamode2 = "data-saver" if ds else "data"

		for page_filename in chapter["data"]["attributes"][datamode]:
			images.append("{}/{}/{}/{}".format(baseurl, datamode2, chaphash, page_filename))

		# get group names & make combined name
		group_uuids = []
		for entry in chapter["data"]["relationships"]:
			if entry["type"] == "scanlation_group":
				group_uuids.append(entry["id"])

		groups = ""
		for i, group in enumerate(group_uuids):
			if i > 0:
				groups += " & "
			r = requests.get("https://api.mangadex.org/group/{}".format(group))
			name = r.json()["data"]["attributes"]["name"]
			groups += name
		groupname = re.sub('[/<>:"/\\|?*]', '-', groups)

		title = re.sub('[/<>:"/\\|?*]', '-', html.unescape(title))
		chapnum = zpad(chapter_info[0])
		if chapnum != "Oneshot":
			chapnum = 'c' + chapnum

		dest_folder = uniquify(title, chapnum, groupname, outdir)
		if not os.path.exists(dest_folder):
			os.makedirs(dest_folder)

		# download images
		for pagenum, url in enumerate(images, 1):
			filename = os.path.basename(url)
			ext = os.path.splitext(filename)[1]

			dest_filename = pad_filename("{}{}".format(pagenum, ext))
			outfile = os.path.join(dest_folder, dest_filename)

			r = requests.get(url)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
					print(" Downloaded page {}.".format(pagenum))
			else:
				# silently try again
				time.sleep(2)
				r = requests.get(url)
				if r.status_code == 200:
					with open(outfile, 'wb') as f:
						f.write(r.content)
						print(" Downloaded page {}.".format(pagenum))
				else:
					print(" Skipping download of page {} - error {}.".format(pagenum, r.status_code))
			time.sleep(0.5) # safely within limit of 5 requests per second
			# not reporting https://api.mangadex.network/report telemetry for now, sorry

		if zip_up:
			zip_name = os.path.join(os.getcwd(), outdir, title, "{} {} [{}]".format(title, chapnum, groupname)) + ".cbz"
			chap_folder = os.path.join(os.getcwd(), outdir, title, "{} [{}]".format(chapnum, groupname))
			with zipfile.ZipFile(zip_name, 'w') as myzip:
				for root, dirs, files in os.walk(chap_folder):
					for file in files:
						path = os.path.join(root, file)
						myzip.write(path, os.path.basename(path))
			print("Chapter successfully packaged into .cbz file.")
			shutil.rmtree(chap_folder) # remove original folder of loose images

	print("Done!")

if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	parser = argparse.ArgumentParser()
	parser.add_argument("-l", dest="lang", required=False, action="store",
						help="download in specified language code (default: en)", default="en")
	parser.add_argument("-d", dest="datasaver", required=False, action="store_true",
						help="download images in lower quality")
	parser.add_argument("-a", dest="cbz", required=False, action="store_true",
						help="package chapters into .cbz format")
	parser.add_argument("-o", dest="outdir", required=False, action="store", default="download",
						help="specify name of output directory")
	args = parser.parse_args()

	lang_code = "en" if args.lang is None else str(args.lang)

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

	dl(manga_id, lang_code, args.cbz, args.datasaver, args.outdir)