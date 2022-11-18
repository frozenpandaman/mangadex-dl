"""
Mangadex-dl: console.py
Initializes the console version.
"""

import sys, traceback

from .base import *
from .parse import *
from .archive import *
from .download import *
from .duplicate import *

def init_console(args):
	# input urls if they are not given by command line option
	if not args.manga_urls:
		while True:
			print()
			try:
				manga_input = input("Enter manga URL or ID. (leave blank to complete)\n"\
						    "> ")
			except EOFError:
				break
			if manga_input is None or manga_input == "":
				break
			args.manga_urls.append(manga_input)
	# download manga from list
	for manga_url in args.manga_urls:
		try:
			_dl_console(manga_url, args)
		except Exception:
			print("{}\nSkip download.".format(traceback.format_exc()))
	return

def _dl_console(manga_url, args):
	print("\nReceiving manga's info...")
	manga_info = get_manga_info(manga_url, args.language)
	
	print("\n[{:2}/{:2}] TITLE: {}\n".format(args.manga_urls.index(manga_url)+1, len(args.manga_urls), manga_info.title))
	
	# get available chapters
	chapters_list = get_chapters_list(manga_info.uuid, args.language)
	
	# duplicate check
	chapters_list = resolve_duplicated_chapters(chapters_list, args.resolve, _resolve_duplicates_manual_console)
	
	# print chapters list
	_print_available_chapters(chapters_list)
	
	# i/o for chapters to download
	if args.download == None:
		dl_input = input("\nEnter chapter(s) to download:"\
				 "\n(see README for examples of valid format)"\
				 "\n> ")
	else:
		dl_input = args.download
	
	dl_list = parse_range(dl_input)
	
	# requested chapters list in dl_range
	requested_chapters = get_requested_chapters(chapters_list, dl_list)
	
	# download images
	manga_directory = create_manga_directory(args.outdir, manga_info.title_en, manga_info.uuid)
	download_chapters(requested_chapters, manga_directory, args.datasaver)
	print("\nChapters download completed successfully")
	
	# archive
	if args.archive != None:
		print("\nArchive downloaded chapters...")
		archive_manga(manga_directory, args.archive, args.keep)
		print("\nArchiving completed successfully")
	
	print("\nManga \"{}\" was successfully downloaded".format(manga_info.title))
	return

def _print_available_chapters(chapters_list):
	print("Available chapters: (total {})".format(len(chapters_list)), end="")
	volume_number = None
	for chapter in chapters_list:
		chapter_volume = chapter["attributes"]["volume"] if chapter["attributes"]["volume"] != "" and chapter["attributes"]["volume"] != None else "Unknown"
		chapter_name = chapter["attributes"]["chapter"] if chapter["attributes"]["chapter"] != None else "Oneshot"
		
		if volume_number != chapter_volume:
			volume_number = chapter_volume
			print("\nVolume {:2}".format(volume_number), end=": ")
		
		print("{:>6}".format(chapter_name), end="")
	print()


def _resolve_duplicates_manual_console(chapters_list, duplicates_list, scanlation_groups):
	for group in scanlation_groups:
		group_priority = input("Specify priority for {}. [1-5]\n> ".format(group["attributes"]["name"]))
		group["priority"] = group_priority
	print("Groups are prioritized\n")
	
	chapters_list = resolve_scanlate_priority_function(chapters_list, duplicates_list, scanlation_groups)
	
	return chapters_list
