#!/usr/bin/env python3
import cloudscraper
import time, os, sys, re, json, html
import threading

#inital values
A_VERSION = "0.2.8"

# Global variables
file_save_location = "C:\\Manga"
#default save location 
# file_save_location = os.getcwd(), "download"
failed_chapters = []
all_chapters = []
scraper = cloudscraper.create_scraper()

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

def dl(manga_id, lang_code):
	global file_save_location
	global all_chapters
	global failed_chapters
	global scraper

	# grab manga info json from api v2	
	try:
		r = scraper.get("https://mangadex.org/api/v2/manga/{}/chapters".format(manga_id))
		manga = json.loads(r.text)
		manga = manga["data"]
	except (json.decoder.JSONDecodeError, ValueError) as err:
		print("CloudFlare error: {}".format(err))
		exit(1)

	# Check if there is a title
	try:
		title = manga["chapters"][0]["mangaTitle"]
	except:
		print("Please enter a MangaDex manga (not chapter) URL.")
		exit(1)
	print("\nTitle: {}".format(html.unescape(title)))

	# check available chapters
	chapters = []
	for chap in range(len(manga["chapters"])):
		if manga["chapters"][chap]["language"] == lang_code:
			chapters.append(manga["chapters"][chap]["chapter"])
	chapters.sort(key=float_conversion) # sort numerically by chapter #

	chapters_revised = ["Oneshot" if x == "" else x for x in chapters]

	dupl = set()
	for i in chapters_revised:
		if chapters_revised.count(i) > 1:
			dupl.add(i)

	if len(chapters) == 0:
		print("No chapters available to download!")
	else:
		print("Available chapters:")
		print(" " + ', '.join(map(str, chapters_revised)))
		if len(dupl) != 0: 
			print("Duplictes found")
			print(" " + ', '.join(map(str, dupl)))

	# i/o for chapters to download
	requested_chapters = []
	chap_list = input("\nEnter chapter(s) to download: ").strip()
	
	if chap_list == "all" or chap_list == "a":			#chapters
		requested_chapters.extend(chapters)
	else:
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
	for chapter_id in range(len(manga["chapters"])):
		#print(manga["chapters"][chapter_id]["chapter"])
		try:
			chapter_num = str(float(manga["chapters"][str(chapter_id)]["chapter"])).replace(".0", "")
		except:
			chapter_num = str(manga["chapters"][chapter_id]["chapter"])
			#pass # Oneshot
		chapter_group = manga["chapters"][chapter_id]["groups"]
		#print(chapter_group)
		if chapter_num in requested_chapters and manga["chapters"][chapter_id]["language"] == lang_code:
			chaps_to_dl.append((str(chapter_num), manga["chapters"][chapter_id]["id"], chapter_group))
	chaps_to_dl.sort(key = lambda x: x[0])

	# get chapter(s) json
	print()
	for chapter_id in chaps_to_dl:
		print("Downloading chapter {}...".format(chapter_id[0]))
		r = scraper.get("https://mangadex.org/api/v2/chapter/{}/".format(chapter_id[1]))
		chapter = json.loads(r.text)
		chapter = chapter["data"]
		# get url list
		images = []
		server = chapter["server"]
		if "mangadex." not in server:
			server = "https://mangadex.org{}".format(server)
		hashcode = chapter["hash"]
		for page in chapter["pages"]:
			images.append("{}{}/{}".format(server, hashcode, page))

		# download images
		groupname = re.sub('[/<>:"/\\|?*]', '-', chapter["groups"][0]["name"])
		for pagenum, url in enumerate(images, 1):
			title = re.sub('[/<>:"/\\|?*]', '-', title)
			dest_folder = os.path.join(file_save_location, title)#, 
			loc = ("c{} [{}]".format(zpad(chapter_id[0]), groupname))
			if not os.path.exists(dest_folder):
				os.makedirs(dest_folder)
			tr = threading.Thread(target=img, args=(pagenum, url, groupname, title, chapter_id, dest_folder, loc))
			tr.start()

	while threading.active_count() > 1:
		tr.join()
	print("Downloading done!")

	for x in all_chapters:
		try:
			f = open(x)
			f.close()
		except:
			print(x)

def img(pagenum, url, groupname, title, chapter_id, dest_folder, loc):
			global all_chapters
			global scraper
			filename = os.path.basename(url)
			ext = os.path.splitext(filename)[1]
			dest_filename = pad_filename("{}{}".format(pagenum, ext))
			dest_filename = loc +" "+ dest_filename
			outfile = os.path.join(dest_folder, dest_filename)
			all_chapters.append(outfile)
			fail_count = 0
			while True:
				r = scraper.get(url)
				if r.status_code == 200:
					with open(outfile, 'wb') as f:
						f.write(r.content)
						break
				else:
					print("Encountered Error {} when downloading.".format(r.status_code))
					fail_count += 1
					if  fail_count > 6:
						break
			print(" Downloaded chapter {} page {}.		Nr of active threads{}.".format(chapter_id[0], pagenum, threading.active_count()-2))

if __name__ == "__main__":
	while True:
		print("mangadex-dl v{}".format(A_VERSION))

		if len(sys.argv) > 1:
			lang_code = sys.argv[1]
		else:
			lang_code = "gb"

		url = ""
		while url == "":
			url = input("Enter manga URL: ").strip()
		if url == "exit" or url == "quit":
			quit() 
		try:
			manga_id = re.search("[0-9]+", url).group(0)
			split_url = url.split("/")
			for segment in split_url:
				if "mangadex" in segment:
					url = segment.split('.')
		except:
			print("Error with URL.")

		dl(manga_id, lang_code)