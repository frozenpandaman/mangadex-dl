"""
Mangadex-dl: parse.py
Parse command-line user input for requested chapters and return a list of them.
"""

import re

def parse_range(range_input):
    """
    Parse user input in console mode.
    """
    range_list = []

    if range_input == "all":
        return "all"

    # split the input string into separate ranges
    # ["v1", "v2(1)-v6(8)", ...]
    entry_input_list = range_input.split(",")

    # define a start and end point for each range
    for entry_input in entry_input_list:
        range_object = _parse_entry_input(entry_input)
        range_list.append(range_object)
    return range_list

def get_requested_chapters(chapters_list, dl_list):
    if dl_list == "all":
        return chapters_list

    requested_chapters = []
    for dl_range in dl_list:
        requested_chapters += _get_chapters_from_range(chapters_list, dl_range)

    if len(requested_chapters) == 0:
        raise ValueError("Empty list of chapters. "\
                         "Make sure you enter the correct download range!")

    return requested_chapters

def _parse_entry_input(entry_input):
    range_object = {"start": {"volume": None, "chapter": None},
                    "end": {"volume": None, "chapter": None}}

    # "v1(1)-v2(3)" --> ["v1(1)", "v2(3)"]
    entry_list = entry_input.split("-")
    re_range = r"v(?P<volume>u|\d+)(?:\((?P<chapter>Oneshot|\d+.?(?:\d+)?)\))?"

    # compose a range object from points
    point = "start" # first write to range_object["start"]
    for entry in entry_list:
        if entry == "":
            break
        # parse volume number
        entry_re = re.search(re_range, entry)
        range_object[point]["volume"] = entry_re.group("volume")
        range_object[point]["chapter"] = entry_re.group("chapter")

        point = "end" # switch to range_object["end"]
    return range_object

def _get_chapters_from_range(chapters_list, dl_range):
    requested_chapters = []

    is_in_range = False     # flag to add chapters

    chapter_last = None     # flags to add last chapter
    is_chapter_last = False #

    volume_last = None      # flags to add last volume
    is_volume_last = False  #

    for chapter in chapters_list:
        chapter_volume = chapter["attributes"]["volume"]
        chapter_name   = chapter["attributes"].get("chapter", "Oneshot")

        # checking exit conditions
        is_volume_last = bool(chapter_volume != volume_last and volume_last)
        is_chapter_last = bool(chapter_name != chapter_last and chapter_last)

        # if it was the last volume or chapter
        if (volume_last and is_volume_last) or \
           (chapter_last and is_chapter_last):
            break

        # range start point check
        if (not chapter_volume and dl_range["start"]["volume"] == "u") or \
           (chapter_volume == dl_range["start"]["volume"]):

            if not dl_range["end"]["volume"]:
                volume_last = chapter_volume

            if chapter_name == dl_range["start"]["chapter"] or \
               not dl_range["start"]["chapter"]:

                # flag this chapters to add in list
                is_in_range = True
                if (dl_range["end"]["volume"]) and \
                   (dl_range["start"]["chapter"]):
                    chapter_last = chapter_name

        # range end point check
        if (not chapter_volume and dl_range["end"]["volume"] == "u") or \
           (chapter_volume == dl_range["end"]["volume"]):
            # this volume is the last
            volume_last = chapter_volume
            if chapter_name == dl_range["end"]["chapter"]:
                chapter_last = chapter_name

        # add chapter to list
        if is_in_range:
            requested_chapters.append(chapter)
    return requested_chapters
