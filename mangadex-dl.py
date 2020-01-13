#!/usr/bin/env python
import cloudscraper
import time, os, sys, re, json, html

A_VERSION = "0.2"

def pad_filename(str):
	digits = re.compile('(\\d+)')
	pos = digits.search(str)
	if pos:
		return str[1:pos.start()] + pos.group(1).zfill(3) + str[pos.end():]
	else:
		return str

def zpad(num):
	if "." in num:
		parts = num.split('.')
		return "{}.{}".format(parts[0].zfill(3), parts[1])
	else:
		return num.zfill(3)

def dl(manga_id, lang_code, tld):
	# grab manga info json from api
	scraper = cloudscraper.create_scraper()
	try:
		r = scraper.get("https://mangadex.{}/api/manga/{}/".format(tld, manga_id))
		manga = json.loads(r.text)
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("CloudFlare error: {}".format(err))
		exit(1)

	try:
		title = manga["manga"]["title"]
	except:
		print("Please enter a MangaDex manga (not chapter) URL.")
		exit(1)
	print("\nTitle: {}".format(html.unescape(title)))

	# check available chapters
	chapters = []

	if "chapter" in manga:
		print("Chapter found in language you requested")
	else:
		print("Chapter not found in the language you requested.")
		exit(1)

	for chap in manga["chapter"]:
		if manga["chapter"][str(chap)]["lang_code"] == lang_code:
			chapters.append(manga["chapter"][str(chap)]["chapter"])
	chapters.sort(key=lambda x: cvt_to_float(x)) # sort numerically by chapter #

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
		else:
			try:
				s = [chapters[chapters.index(s)]]
			except ValueError:
				print("Chapter {} does not exist. Skipping.".format(s))
				continue
		requested_chapters.extend(s)

	# find out which are availble to dl
	chaps_to_dl = []
	for chapter_id in manga["chapter"]:
		try:
			chapter_num = str(float(manga["chapter"][str(chapter_id)]["chapter"])).replace(".0","")
		except:
			pass # Oneshot
		chapter_group = manga["chapter"][chapter_id]["group_name"]
		if chapter_num in requested_chapters and manga["chapter"][chapter_id]["lang_code"] == lang_code:
			chaps_to_dl.append((str(chapter_num), chapter_id, chapter_group))
	chaps_to_dl.sort()

	if len(chaps_to_dl) == 0:
		print("No chapters available to download!")
		exit(0)

	# get chapter(s) json
	print()
	for chapter_id in chaps_to_dl:
		print("Downloading chapter {}...".format(chapter_id[0]))
		r = scraper.get("https://mangadex.{}/api/chapter/{}/".format(tld, chapter_id[1]))
		chapter = json.loads(r.text)

		# get url list
		images = []
		server = chapter["server"]
		if "mangadex.org" not in server:
			server = "https://mangadex.{}{}".format(tld, server)
		hashcode = chapter["hash"]
		for page in chapter["page_array"]:
			images.append("{}{}/{}".format(server, hashcode, page))

		# download images
		groupname = chapter_id[2].replace("/","-")
		for url in images:
			filename = os.path.basename(url)
			dest_folder = os.path.join(os.getcwd(), "download", title, "c{} [{}]".format(zpad(chapter_id[0]), groupname))
			if not os.path.exists(dest_folder):
				os.makedirs(dest_folder)
			dest_filename = pad_filename(filename)
			outfile = os.path.join(dest_folder, dest_filename)

			r = scraper.get(url)
			if r.status_code == 200:
				with open(outfile, 'wb') as f:
					f.write(r.content)
			else:
				print("Encountered Error {} when downloading.".format(e.code))

			print(" Downloaded page {}.".format(re.sub("\\D", "", filename)))
			time.sleep(1)

	print("Done!")

def cvt_to_float(input):
	try:
		out = float(input)
	except:
		return 0
	
	return out

if __name__ == "__main__":
	print("mangadex-dl v{}".format(A_VERSION))

	if len(sys.argv) > 1:
		lang_code = sys.argv[1]
	else:
		lang_code = "gb"

	url = ""
	while url == "":
		url = input("Enter manga URL: ").strip()
	manga_id = re.search("[0-9]+", url).group(0)
	split_url = url.split("/")
	for segment in split_url:
		if "mangadex" in segment:
			url = segment.split('.')

	if url == None:
		print("Error with URL")
		
	else:
		dl(manga_id, lang_code, url[1])
