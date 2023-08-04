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

    # set end point
    if not range_object["end"]["volume"]:
        range_object["end"] = range_object["start"]
    elif not range_object["end"]["chapter"]:
        range_object["end"]["chapter"] = range_object["start"]["chapter"]

    return range_object

def _get_chapters_from_range(chapters_list, dl_range):
    requested_chapters = []

    is_in_range = False     # flag to add chapters

    chapter_last = None     # flag to add last chapter
    volume_last = None      # flag to add last volume

    for chapter in chapters_list:
        chapter_volume = chapter["attributes"]["volume"]
        chapter_name   = chapter["attributes"]["chapter"] or "Oneshot"

        # if it was the last volume or chapter
        if (volume_last and chapter_volume != volume_last) or \
           (chapter_last and chapter_name != chapter_last):
            break

        if not is_in_range:
            # range start point check
            # if current volume name matches start volume name
            if (not chapter_volume and dl_range["start"]["volume"] == "u")\
               or (chapter_volume == dl_range["start"]["volume"]):

                # if the current chapter name is the same as the target chapter name
                # or if no target chapter is specified
                if chapter_name == dl_range["start"]["chapter"]\
                   or not dl_range["start"]["chapter"]:

                    # mark this and subsequent chapters for addition
                    is_in_range = True

        if is_in_range:
            # range end point check
            # if the current volume name is the same as the target volume name
            # or if no target volume is specified
            if (not chapter_volume and dl_range["end"]["volume"] == "u")\
               or (chapter_volume == dl_range["end"]["volume"]):

                # this volume is the last
                volume_last = chapter_volume

                # if the current chapter name is the same as the target chapter name
                if chapter_name == dl_range["end"]["chapter"]:
                    chapter_last = chapter_name

            requested_chapters.append(chapter)

    return requested_chapters
