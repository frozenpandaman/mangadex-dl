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

import requests, time, os, sys, re, json, html, zipfile, configargparse, shutil, PIL.Image

A_VERSION = "0.7"

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
		r = requests.post("https://api.mangadex.org/legacy/mapping",
				headers=headers, data=payload)
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

def dl(manga_id, lang_code, zip_up, ds, outdir, make_pdf, remove_dir, skip_files):
	uuid = manga_id

	if manga_id.isnumeric():
		uuid = get_uuid(manga_id)

	title = get_title(uuid, lang_code)
	print("\nTITLE: {}".format(html.unescape(title)))

	# check available chapters & get images
	chap_list = []
	content_ratings = "contentRating[]=safe"\
			"&contentRating[]=suggestive"\
			"&contentRating[]=erotica"\
			"&contentRating[]=pornographic"
	r = requests.get("https://api.mangadex.org/manga/{}/feed"\
			"?limit=0&translatedLanguage[]={}&{}"
			.format(uuid, lang_code, content_ratings))
	try:
		total = r.json()["total"]
	except KeyError:
		print("Error retrieving the chapters list. "\
				"Did you specify a valid language code?")
		exit(1)

	if total == 0:
		print("No chapters available to download!")
		exit(0)

	offset = 0
	while offset < total: # if more than 500 chapters!
		r = requests.get("https://api.mangadex.org/manga/{}/feed"\
				"?order[chapter]=asc&order[volume]=asc&limit=500"\
				"&translatedLanguage[]={}&offset={}&{}"
				.format(uuid, lang_code, offset, content_ratings))
		chaps = r.json()
		chap_list += chaps["data"]
		offset += 500

	# chap_list is not empty at this point
	print("Available chapters:")
	print(" " + ', '.join(map(
		lambda x: "Oneshot" if x["attributes"]["chapter"] is None
		else x["attributes"]["chapter"],
		chap_list)))

	# i/o for chapters to download
	requested_chapters = []
	dl_list = input("\nEnter chapter(s) to download: ").strip()

	dl_list = [s.strip() for s in dl_list.split(',')]
	chap_list_only_nums = [i["attributes"]["chapter"] for i in chap_list]
	for s in dl_list:
		if "-" in s: # range
			split = s.split('-')
			lower_bound = split[0]
			upper_bound = split[-1]
			try:
				lower_bound_i = chap_list_only_nums.index(lower_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping range {}."
						.format(lower_bound, s))
				continue # go to next iteration of loop
			try:
				upper_bound_i = chap_list_only_nums.index(upper_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping range {}."
						.format(upper_bound, s))
				continue
			s = chap_list[lower_bound_i:upper_bound_i+1]
		elif s.lower() == "oneshot":
			if None in chap_list_only_nums:
				oneshot_idxs = [i
						for i, x in enumerate(chap_list_only_nums)
						if x is None]
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
	progress_indicator = ["|", "/", "–", "\\"]
	for index, chapter in enumerate(requested_chapters):
		print("Downloading chapter {} [{}/{}]".format(
			chapter["attributes"]["chapter"]
			if chapter["attributes"]["chapter"] is not None
			else "Oneshot", index+1, len(requested_chapters)))

		r = requests.get("https://api.mangadex.org/at-home/server/{}"
				.format(chapter["id"]))
		chapter_data = r.json()
		baseurl = chapter_data["baseUrl"]

		# make url list
		images = []
		accesstoken = ""
		chaphash = chapter_data["chapter"]["hash"]
		datamode = "dataSaver" if ds else "data"
		datamode2 = "data-saver" if ds else "data"
		errored = False

		for page_filename in chapter_data["chapter"][datamode]:
			images.append("{}/{}/{}/{}".format(
				baseurl, datamode2, chaphash, page_filename))

		# get group names & make combined name
		group_uuids = []
		for entry in chapter["relationships"]:
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
		if (chapter["attributes"]["chapter"]) is None:
			chapnum = "Oneshot"
		else:
			chapnum = 'c' + zpad(chapter["attributes"]["chapter"])

		dest_folder = os.path.join(os.getcwd(), outdir, title,
								   "{} [{}]".format(chapnum, groupname))
		if not skip_files:
			dest_folder = uniquify(title, chapnum, groupname, outdir)
		# Creates the path for all images format
		format_file_name = os.path.join(os.getcwd(), outdir, title,
										"{} {} [{}].".format(title, chapnum, groupname))
		zip_in_root = format_file_name + "cbz"
		pdf_in_root = format_file_name + "pdf"
		is_file_in_root = True if os.path.exists(zip_in_root) or os.path.exists(pdf_in_root) \
			else False
		if not os.path.exists(dest_folder) and not is_file_in_root:
			os.makedirs(dest_folder)

		# download images
		for pagenum, url in enumerate(images, 1):
			filename = os.path.basename(url)
			ext = os.path.splitext(filename)[1]

			dest_filename = pad_filename("{}{}".format(pagenum, ext))
			outfile = os.path.join(dest_folder, dest_filename)
			if is_file_in_root:
				break
			if os.path.exists(outfile):
				continue
			r = requests.get(url)
			# go back to the beginning and erase the line before printing more
			print("\r\033[K{} Downloading pages [{}/{}]".format(
				progress_indicator[(pagenum-1)%4], pagenum, len(images)),
				end='', flush=True)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
			else:
				# silently try again
				time.sleep(2)
				r = requests.get(url)
				if r.status_code == 200:
					errored = False
					with open(outfile, 'wb') as f:
						f.write(r.content)
				else:
					errored = True
					print("\n Skipping download of page {} - error {}.".format(
						pagenum, r.status_code))
			time.sleep(0.2) # within limit of 5 requests per second
			# not reporting https://api.mangadex.network/report telemetry for now, sorry

		if not remove_dir:
			format_file_name = dest_folder + "/" + "{} {} [{}].".format(title, chapnum, groupname)
		zip_path = format_file_name + "cbz"
		if zip_up and not is_file_in_root:
			chap_folder = os.path.join(os.getcwd(), outdir, title,
							"{} [{}]".format(chapnum, groupname))
			with zipfile.ZipFile(zip_path, 'w') as myzip:
				for root, dirs, files in os.walk(chap_folder):
					for file in files:
						if str(file).lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')):
							path = os.path.join(root, file)
							myzip.write(path, os.path.basename(path))
		if not errored:
			if len(requested_chapters) != index+1:
				# go back to chapter line and clear it and everything under it
				print("\033[F\033[J", end='', flush=True)
			else:
				print("\r\033[K", end='', flush=True)

		pdf_path = format_file_name + "pdf"
		if make_pdf and not is_file_in_root:
			with os.scandir(dest_folder) as entries:
				img_list = []
				for entry in entries:
					if str(entry.name).lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp')):
						image_location = os.path.join(dest_folder, entry.name)
						img = PIL.Image.open(image_location)
						img.load()
						img_list.append(img)
				img_list[0].save(fp=pdf_path, format="PDF", save_all=True,
								 append_images=img_list[1:])
		if remove_dir and os.path.exists(dest_folder):
			shutil.rmtree(dest_folder)  # remove original folder of loose images
	print("Done.")


if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	parser = configargparse.ArgParser(default_config_files=['config.txt'])
	parser.add_argument("-l", "--language", dest="lang", required=False,
			action="store", default="en", metavar="lang_code",
			help="Download in specified language code (default: en)")
	parser.add_argument("-d", "--datasaver", dest="datasaver", required=False,
			action="store_true",
			help="Download images in lower quality")
	parser.add_argument("-a", "--cbz", dest="cbz", required=False,
			action="store_true",
			help="Package chapters into .cbz format")
	parser.add_argument("-o", "--outdir", dest="outdir", required=False,
			action="store", default="download", metavar="dl-dir",
			help="Specify name of output directory")
	parser.add_argument("-p", "--pdf", dest="create_pdf", required=False, action="store_true",
			help="Package chapter into .pdf format")
	parser.add_argument("-r", "--remove", dest="remove_dir", required=False, action="store_true",
			help="Removes the downloaded chapters directory only if '-p' or '-a' flag exists")
	parser.add_argument("-s", "--skip", dest="skip_files", required=False, action="store_true",
			help="Skip the chapter if it's already downloaded")
	args = parser.parse_args()

	lang_code = "en" if args.lang is None else str(args.lang)
	# Prevents people from spamming the servers with useless requests
	if not args.create_pdf and not args.cbz:
		args.remove_dir = False

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

	dl(manga_id, lang_code, args.cbz, args.datasaver, args.outdir, args.create_pdf,
	   args.remove_dir, args.skip_files)
