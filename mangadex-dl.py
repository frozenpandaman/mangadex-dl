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

import argparse, os
from mangadex_dl_functions import *

MANGADEX_DL_VERSION = "0.7"

def dl(manga_url, args):
	manga_uuid = get_uuid(manga_url)
	manga_title, manga_title_en = get_title(manga_uuid, args.language)
	
	print("\n[{:2}/{:2}] TITLE: {}\n".format(args.manga_urls.index(manga_url)+1, len(args.manga_urls), manga_title))
	
	# check available chapters
	chapters_info = get_chapters_info(manga_uuid, args.language)
	
	if chapters_info["total"] == 0:
		raise ValueError("No chapters available to download!")
	
	chapters_list = get_chapters_list(manga_uuid, chapters_info["total"], args.language)
	
	# duplicate check
	if args.resolve != "all":
		duplicated_chapters_list = get_duplicated_chapters(chapters_list)
		if len(duplicated_chapters_list) != 0:
			chapters_list = resolve_duplicated_chapters(chapters_list, duplicated_chapters_list, args.resolve)
	
	# print chapters list
	print_available_chapters(chapters_list)
	
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
	if len(requested_chapters) == 0:
		raise ValueError("Empty list of chapters. Make sure you enter the correct download range!")
	
	# download images
	if os.path.isdir(args.outdir):
		out_directory = args.outdir
	else:
		out_directory = "."
	
	manga_directory = os.path.join(out_directory, manga_title_en)
	if not os.path.exists(manga_directory):
		try:
			os.makedirs(manga_directory)
		except OSError:
			manga_directory = os.path.join(out_directory, "Manga {}".format(manga_uuid))
			if not os.path.exists(manga_directory):
				os.makedirs(manga_directory)
	
	download_chapters(requested_chapters, manga_directory, args.datasaver)
	
	# archive
	if args.archive != None:
		archive_manga_directory(manga_directory, out_directory, args.archive, args.keep)
	
	print("\nManga \"{}\" was successfully downloaded".format(manga_title))

def initialize():
	help_str = "Examples of valid input for a range of downloadable chapters: "\
	"[ all | "\
	"v1 | "\
	"v1-v10 | "\
	"v1(3) | "\
	"v1(3)-v10(5) | "\
	"v1-v10(5) | "\
	"vu(Oneshot), u - Volume Unknown ]."
	
	parser = argparse.ArgumentParser(epilog=help_str)
	parser.add_argument("-l", dest="language", required=False,
			    action="store", default="en",
			    help="download in specified language code (default: en)")
	parser.add_argument("-o", dest="outdir", required=False,
			    action="store", default="download",
			    help="specify name of output directory")
	parser.add_argument("-d", dest="download", required=False,
			    action="store", metavar="<range>",
			    help="downloading chapters range")
	parser.add_argument("-a", dest="archive", required=False,
			    choices=["chap", "vol", "manga"],
			    help="package into zip files")
	parser.add_argument("-k", dest="keep", required=False,
			    action="store_true",
			    help="keep original files after archiving")
	parser.add_argument("-s", dest="datasaver", required=False,
			    action="store_true",
			    help="download images in lower quality")
	parser.add_argument("-r", dest="resolve", required=False,
			    choices=["all", "one"],
			    help="how to deal with duplicate chapters")
	parser.add_argument("manga_urls", metavar="<manga_urls>", nargs="*",
			    help="specify manga url")
	args = parser.parse_args()
	
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
			dl(manga_url, args)
		except Exception as err:
			print("\nError:", err, "\nSkip download.")

if __name__ == "__main__":
	print("mangadex-dl v{}".format(MANGADEX_DL_VERSION))
	initialize()
	print("\nThe program has ended. Exiting...")
