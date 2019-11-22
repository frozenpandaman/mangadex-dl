#!/usr/bin/env python3
import cloudscraper
import time, os, sys, re, json

A_VERSION = "0.1.6"


def chapter_key(c):
	try:
		n = int(float(c[0]))
		return (n, c)
	except:
		return ("no_chapter", c)


digits_pat = re.compile('(\d+)');

def pad_filename(s):
	m = digits_pat.search(s)
	if m:
		return s[:m.start()] + m.group(1).zfill(5) + s[m.end():]
	else:
		return s


def dl(manga_id, lang_code="gb"):
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
	print("\nTitle: {}".format(title))

	# i/o for chapters to download
	requested_chapters = []
	chap_list = input("Enter chapter(s) to download: ").strip()
	chap_list = [s for s in chap_list.split(',')]
	for s in chap_list:
		if "-" in s:
			r = [int(float(n)) for n in s.split('-')]
			s = list(range(r[0], r[1]+1))
		else:
			s = [float(s)]
		requested_chapters.extend(s)

	# find out which are availble to dl (in english for now)
	chaps_to_dl = []

	for chapter_id in manga["chapter"]:
		try:
			chapter_num = float(manga["chapter"][chapter_id]["chapter"])
		except:
			pass # Oneshot
		chapter_group = manga["chapter"][chapter_id]["group_name"]
		if chapter_num in requested_chapters and manga["chapter"][chapter_id]["lang_code"] == lang_code:
			chaps_to_dl.append((str(chapter_num).replace(".0",""), chapter_id, chapter_group))
	chaps_to_dl.sort(key=chapter_key)

	if len(chaps_to_dl) == 0:
		print("No chapters available to download!")
		exit(0)

	# get chapter(s) json
	print()
	for chapter_id in chaps_to_dl:
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
			dest_folder = os.path.join(os.getcwd(), "download", title, "c{} [{}]".format(chapter_id[0].zfill(3), groupname))
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
