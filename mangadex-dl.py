#!/usr/bin/env python3

# Copyright (C) 2019-2021 eli fessler
# Copyright (C) 2022 Uwuewsky
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

import argparse
from mangadex_dl_functions import *

MANGADEX_DL_VERSION = "1.0"

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
