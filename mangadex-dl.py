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

def prompt_chapters(chapters):
	chapter_numbers = sorted(
		[chapter["chapter"] for chapter in chapters.values()],
		key = lambda x: float(x)
	)

	print("Available chapters:")
	print(", ".join(chapter_numbers))

	# i/o for chapters to download
	requested_chapters = []
	chapter_list = input("\nEnter chapter(s) to download: ").strip()
	chapter_list = [s.strip() for s in chapter_list.split(",")]

	for s in chapter_list:
		if "-" in s:
			split = s.split("-")
			lower_bound = split[0]
			upper_bound = split[1]

			try:
				lower_bound_i = chapter_numbers.index(lower_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping {}.".format(lower_bound, s))
				continue

			try:
				upper_bound_i = chapter_numbers.index(upper_bound)
			except ValueError:
				print("Chapter {} does not exist. Skipping {}.".format(upper_bound, s))
				continue

			s = chapter_numbers[lower_bound_i:upper_bound_i+1]
		else:
			try:
				s = [chapter_numbers[chapter_numbers.index(s)]]
			except ValueError:
				print("Chapter {} does not exist. Skipping.".format(s))
				continue

		requested_chapters.extend(s)

	return {id: chapter for id, chapter in chapters.items() if chapter["chapter"] in requested_chapters}

def dl(manga_id, lang_code):
	# grab manga info json from api
	scraper = cloudscraper.create_scraper()
	try:
		r = scraper.get("https://mangadex.org/api/manga/{}/".format(manga_id))
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
	chapters = {}
	oneshots = {}

	for id, chapter in manga["chapter"].items():
		if chapter["lang_code"] == lang_code:
			if chapter["chapter"] == "":
				oneshots[id] = chapter
			else:
				chapters[id] = chapter

	requested_chapters = prompt_chapters(chapters)

	# find out which are availble to dl
	chapters_to_download = [
		(chapter["chapter"], id, chapter["group_name"])
		for id, chapter in requested_chapters.items()
	]

	if len(chapters_to_download) == 0:
		print("No chapters available to download!")
		exit(0)

	# get chapter(s) json
	print()
	for chapter_id in chapters_to_download:
		print("Downloading chapter {}...".format(chapter_id[0]))
		r = scraper.get("https://mangadex.org/api/chapter/{}/".format(chapter_id[1]))
		chapter = json.loads(r.text)

		# get url list
		images = []
		server = chapter["server"]
		if "mangadex.org" not in server:
			server = "https://mangadex.org{}".format(server)
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
	dl(manga_id, lang_code)
