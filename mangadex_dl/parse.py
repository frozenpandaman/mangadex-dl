"""
Mangadex-dl: parse.py
Parse command-line user input for requested chapters and return a list of them.
"""

import re

def parse_range(range_input):
	"""
	Sample object: 
	sample = [{"start": {"volume": "2", "chapter": "5"},  | v2(5)-v6(9)
	             "end": {"volume": "6", "chapter": "9"}}] |
	"""
	requested_list = []
	
	if range_input == "all":
		return "all"
	
	# split the input into separate ranges
	entry_input_list = range_input.split(",")
	
	# define a start and end point for each range
	for entry_input in entry_input_list:
		range_object = {"start": {"volume": None, "chapter": None}, "end": {"volume": None, "chapter": None}}
		
		volume_input_list = entry_input.split("-")
		
		# compose a range object from points 
		start = True
		for volume_input in volume_input_list:
			if volume_input == "":
				break
			# parse volume number
			re_entry = "v(u|\d+)"
			regex = re.compile("{}".format(re_entry))
			volume_list = re.findall(regex, volume_input)
			
			if len(volume_list) != 0:
				if start:
					range_object["start"]["volume"] = volume_list[0]
				else:
					range_object["end"]["volume"] = volume_list[0]
			
			# parse chapter number
			re_entry = "\((Oneshot|[\d.]+)\)"
			regex = re.compile("{}".format(re_entry))
			chapter_input = re.findall(regex, volume_input)
			
			if len(chapter_input) != 0:
				for chapter_ranges in chapter_input[0].split(","):
					re_entry = "(Oneshot|[\d.]+)"
					regex = re.compile("{}".format(re_entry))
					chapter = re.findall(regex, chapter_ranges)[0]
					if "-" in chapter_ranges:
						chapter = (tuple(chapter_ranges.split("-")))
					if start:
						range_object["start"]["chapter"] = chapter
					else:
						range_object["end"]["chapter"] = chapter
			
			start = False
		requested_list.append(range_object)
	
	return requested_list

def get_requested_chapters(chapters_list, dl_list):
	if dl_list == "all":
		return chapters_list
	
	requested_chapters = []
	for dl_range in dl_list:
		is_in_range = False     # flag to add chapters
		chapter_last = None     # flags to add last chapter
		is_chapter_last = False
		volume_last = None      # flags to add last volume
		is_volume_last = False
		for chapter in chapters_list:
			chapter_volume = chapter["attributes"]["volume"]
			chapter_name   = chapter["attributes"]["chapter"] if chapter["attributes"]["chapter"] != None else "Oneshot"
			
			# checking exit conditions
			is_volume_last = True if chapter_volume != volume_last and volume_last != None else False
			is_chapter_last = True if chapter_name != chapter_last and chapter_last != None else False
			
			# if it was the last volume or chapter
			if (volume_last != None and is_volume_last) or (chapter_last != None and is_chapter_last):
				break
			
			# range start point check
			if (chapter_volume == None and dl_range["start"]["volume"] == "u") or \
			   (chapter_volume == dl_range["start"]["volume"]):
				if dl_range["end"]["volume"] == None:
					volume_last = chapter_volume
				if chapter_name == dl_range["start"]["chapter"] or \
				   dl_range["start"]["chapter"] == None:
					# flag this chapters to add in list
					is_in_range = True
					if dl_range["end"]["volume"] == None and dl_range["start"]["chapter"] != None:
						chapter_last = chapter_name
			# range end point check
			if (chapter_volume == None and dl_range["end"]["volume"] == "u") or \
			   (chapter_volume == dl_range["end"]["volume"]):
				# this volume is the last 
				volume_last = chapter_volume
				if chapter_name == dl_range["end"]["chapter"]:
					chapter_last = chapter_name
			
			# add chapter to list
			if is_in_range:
				requested_chapters.append(chapter)
	if len(requested_chapters) == 0:
		raise ValueError("Empty list of chapters. Make sure you enter the correct download range!")
	
	return requested_chapters
