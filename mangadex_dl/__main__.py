import argparse

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
			    help="download in specified language code (default: 'en')")
	parser.add_argument("-o", dest="outdir", required=False,
			    action="store", default=".",
			    help="specify name of output directory (default: './')")
	parser.add_argument("-d", dest="download", required=False,
			    action="store", metavar="<range>",
			    help="downloading chapters range")
	parser.add_argument("-a", dest="archive", required=False,
			    choices=["chapter", "volume", "manga"],
			    help="package into zip files")
	parser.add_argument("-k", dest="keep", required=False,
			    action="store_true", default=False,
			    help="keep original files after archiving (default: False)")
	parser.add_argument("-s", dest="datasaver", required=False,
			    action="store_true", default=False,
			    help="download images in lower quality (default: False)")
	parser.add_argument("-r", dest="resolve", required=False,
			    choices=["all", "one", "manual"], default="one",
			    help="how to deal with duplicate chapters (default: 'one')")
	parser.add_argument("-g", dest="gui", required=False,
			    action="store_true", default=False,
			    help="open GUI instead console version (default: False)")
	parser.add_argument("manga_urls", metavar="<manga_urls>", nargs="*",
			    help="specify manga url")
	
	args = parser.parse_args()
	if args.gui:
		from .gui import init_gui
		init_gui(args)
	else:
		from .console import init_console
		init_console(args)
	return

if __name__ == "__main__":
	initialize()
