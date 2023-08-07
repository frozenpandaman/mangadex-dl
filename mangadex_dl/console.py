"""
Mangadex-dl: console.py
Initializes the console version.
"""

import traceback

from mangadex_dl import utils
from mangadex_dl import parse
from mangadex_dl import archive as ar
from mangadex_dl import download as dl
from mangadex_dl import duplicate as dup


def init_console(args):
    # input urls if they are not given by command line option
    if not args.manga_urls:
        while True:
            try:
                manga_input = input("\nEnter URL or text to search "\
                                    "by title. (leave blank to complete)\n> ")
            except EOFError:
                break
            if not manga_input:
                break
            args.manga_urls.append(manga_input)

    # download manga from list
    for manga_url in args.manga_urls:
        try:
            _dl_console(manga_url, args)
        except Exception:
            print("{}\nSkip download.".format(traceback.format_exc()))

def _dl_console(manga_url, args):
    print("\nReceiving manga's info...")
    manga_info = _search_manga_info(manga_url, args.language)

    print("\n[{:2}/{:2}] TITLE: {}\n".format(
        args.manga_urls.index(manga_url)+1,
        len(args.manga_urls), manga_info.title))

    # get available chapters
    chapters_list = utils.get_chapters_list(manga_info.uuid, args.language)

    # duplicate check
    chapters_list = dup.resolve_duplicated_chapters(chapters_list,
                                                    args.resolve,
                                                    _resolve_duplicates_manual_console)

    # print chapters list
    _print_available_chapters(chapters_list)

    # i/o for chapters to download
    if not args.download:
        dl_input = input("\nEnter chapters to download:"\
                         "\n(see README for examples of valid format) "\
                         "(leave blank to cancel)"\
                         "\n> ")
        if dl_input == "":
            return
    else:
        dl_input = args.download

    dl_list = parse.parse_range(dl_input)

    # requested chapters list in dl_range
    requested_chapters = parse.get_requested_chapters(chapters_list, dl_list)

    # download images
    manga_directory = utils.create_manga_directory(args.outdir,
                                                   manga_info.title_en,
                                                   manga_info.uuid)

    dl.download_chapters(requested_chapters, manga_directory, args.datasaver)
    print("\nChapters download completed successfully")

    # archive
    if args.archive:
        print("\nArchive downloaded chapters...")
        ar.archive_manga(manga_directory, args.archive, args.keep, args.ext)
        print("\nArchiving completed successfully")

    print(f"\nManga \"{manga_info.title}\" was successfully downloaded")

def _search_manga_info(manga_url, language):

    if utils.get_uuid(manga_url):
        manga_info = utils.get_manga_info(manga_url, language)
        return manga_info

    manga_list_found = utils.search_manga(manga_url, language)

    if len(manga_list_found) == 0:
        raise ValueError("Nothing was found according to your request")
    if len(manga_list_found) == 1:
        return manga_list_found[0]

    _print_found_manga_list(manga_list_found)

    user_input = input("Insert number (leave blank to cancel):\n> ")

    if user_input == "":
        raise ValueError("The program was canceled by the user")

    return manga_list_found[int(user_input)-1]

def _print_found_manga_list(manga_list):
    print("The following titles were found on request:")
    for i, manga in enumerate(manga_list, start=1):
        print("{:2}. {} ({}) by {}".format(
            i, manga.title, manga.year, ", ".join(manga.authors)))

def _print_available_chapters(chapters_list):

    print(f"Available chapters: (total {len(chapters_list)})", end="")

    volume_number = None
    for chapter in chapters_list:
        chapter_volume = chapter["attributes"]["volume"] or "Unknown"
        chapter_name = chapter["attributes"]["chapter"] or "Oneshot"

        if volume_number != chapter_volume:
            volume_number = chapter_volume
            print(f"\nVolume {volume_number:2}: ", end="")

        print(f"{chapter_name:>6}", end="")
    print()

def _resolve_duplicates_manual_console(chapters_list,
                                       duplicates_list,
                                       scanlation_groups):
    for group in scanlation_groups:
        group_priority = input("Specify priority for "\
                               f"{group['attributes']['name']}. "\
                               "[1-5], highest is 1.\n> ")
        group["priority"] = group_priority
    print("Groups are prioritized\n")

    chapters_list = dup.resolve_scanlate_priority_function(chapters_list,
                                                           duplicates_list,
                                                           scanlation_groups)

    return chapters_list

