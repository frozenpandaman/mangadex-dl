"""
Mangadex-dl: download.py
Handling low-level HTTP requests and loading images.
"""

import urllib.request, os, time, json, concurrent.futures
from collections import deque

def url_request(url):
	# let's try five times
	error = None
	for i in range(0,5):
		try:
			_DownloadLimits.check()
			response = urllib.request.urlopen(url, timeout=60).read()
			return response
		except Exception as err:
			error = err
			time.sleep(2)
	raise error

def get_json(url):
	return json.loads(url_request(url).decode("utf-8"))

def download_chapters(requested_chapters, out_directory, is_datasaver, gui={"set": False}):
	chapter_count = 1
	chapter_count_max = len(requested_chapters)
	
	for chapter in requested_chapters:
		chapter_number = chapter["attributes"]["chapter"] if chapter["attributes"]["chapter"] != None else "Oneshot"
		chapter_name = chapter["attributes"]["title"] if chapter["attributes"]["title"] != None else ""
		chapter_volume = chapter["attributes"]["volume"] if chapter["attributes"]["volume"] != None else "Unknown"
		
		print("\nDownloading chapter [{:3}/{:3}] Ch.{} {}".format(chapter_count, chapter_count_max, chapter_number, chapter_name))
		
		chapter_json = get_json("https://api.mangadex.org/at-home/server/{}".format(chapter["id"]))
		base_url = "{}/{}/{}/".format(chapter_json["baseUrl"], "data-saver" if is_datasaver else "data", chapter_json["chapter"]["hash"])
		image_url_list = chapter_json["chapter"]["dataSaver"] if is_datasaver else chapter_json["chapter"]["data"]
		
		image_count = 1
		image_count_downloaded = 1
		image_count_max = len(image_url_list)
		
		if image_count_max == 0:
			print("  Chapter {} is not available from Mangadex.".format(chapter_number))
			print("  It looks like Mangadex contains a link to a third-party site, but not the images themselves.")
			continue
		
		directory_chapter = os.path.join(out_directory, "Volume {}".format(chapter_volume), "Chapter {}".format(chapter_number))
		if os.path.exists(directory_chapter):
			# name folders like "Chapter 1 (2)"
			for i in range(1, 10):
				temp_path = "{} ({})".format(directory_chapter, i)
				if not os.path.exists(temp_path):
					directory_chapter = temp_path
					break
		os.makedirs(directory_chapter)
		
		future_list = []
		with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
			for image_url in image_url_list:
				future_list.append(executor.submit(_download_image, base_url + image_url, image_count, directory_chapter))
				image_count += 1
			for future in concurrent.futures.as_completed(future_list):
				print("\r  Downloaded images [{:3}/{:3}]...".format(image_count_downloaded, image_count_max), end="")
				image_count_downloaded += 1
				
				if gui["set"]:
					if gui["exit"]:
						for f in future_list:
							f.cancel()
		if gui["set"]:
			gui["progress"].set((chapter_count/chapter_count_max)*100)
		
		chapter_count += 1
	
	print("\nChapters download completed successfully")
	return

def _download_image(full_url, image_count, directory_chapter):
	image_file_path = os.path.join(directory_chapter, "{:03d}{}".format(image_count, os.path.splitext(full_url)[1]))
	image_file = open(image_file_path, mode="wb")
	with image_file:
		image_file.write(url_request(full_url))
	return

class _DownloadLimits:
	last_requests = deque(maxlen=5)
	
	def check():
		if len(_DownloadLimits.last_requests) == 5:
			interval = time.time() - _DownloadLimits.last_requests[0]
			if interval < 1:
				time.sleep(1 - interval)
		_DownloadLimits.last_requests.append(time.time())
		return
