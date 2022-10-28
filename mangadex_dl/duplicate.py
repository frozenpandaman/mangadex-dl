"""
Mangadex-dl: duplicate.py
Sometimes chapters are duplicated by several scanlate groups, these functions allow you to filter out unnecessary ones.
"""

from .download import *

def resolve_duplicated_chapters(chapters_list, resolve, resolve_manual_function):
	"""
	Returns a list of chapters based on the given argument 'resolve'.
	'resolve_manual_function' is required to manually specify the priority of groups in the console or in the GUI.
	"""
	if resolve == "all":
		return chapters_list
	
	duplicates_list = get_duplicated_chapters(chapters_list)
	
	if len(duplicates_list) == 0:
		return chapters_list
	
	if resolve == "one":
		for duplicates_set in duplicates_list:
			first = True
			for duplicate in duplicates_set:
				if first:
					first = False
				else:
					if duplicate in chapters_list:
						chapters_list.remove(duplicate)
		return chapters_list
	
	# manually set scanlate groups priority
	print("Receiving scanlate groups info...")
	scanlation_groups = get_scanlation_groups_from_duplicates(duplicates_list)
	print("Duplicated chapters have {} scanlate groups".format(len(scanlation_groups)))
	
	if len(scanlation_groups) == 0:
		return
	
	return resolve_manual_function(chapters_list, duplicates_list, scanlation_groups)

def get_duplicated_chapters(chapters_list):
	"""
	Return a nested list of duplicates like:
	[[chap1_1, chap1_2], [chap2_1, chap2_2, chap2_3]...]
	"""
	duplicates_list = []
	
	check_list = chapters_list.copy()
	for chapter_i in check_list:
		duplicates_set = []
		for chapter_j in check_list:
			if chapter_i["id"] == chapter_j["id"]:
				continue
			if chapter_i["attributes"]["volume"] == chapter_j["attributes"]["volume"] and \
			   chapter_i["attributes"]["chapter"] == chapter_j["attributes"]["chapter"]:
				if chapter_i not in duplicates_list:
					duplicates_set.append(chapter_i)
				if chapter_j not in duplicates_list:
					duplicates_set.append(chapter_j)
		if len(duplicates_set) != 0:
			duplicates_list.append(duplicates_set)
		if chapter_i in check_list:
			check_list.remove(chapter_i)
	
	return duplicates_list

def get_scanlation_groups_from_duplicates(duplicates_list):
	scanlation_groups_id = set()
	scanlation_groups = []
	
	for duplicates_set in duplicates_list:
		for duplicate in duplicates_set:
			group_id = _get_chapter_scanlation_id(duplicate)
			if group_id != None:
				scanlation_groups_id.add(group_id)

	for group_id in scanlation_groups_id:
		scanlation_groups.append(_get_scanlation_group_info(group_id))
	
	return scanlation_groups

def resolve_scanlate_priority_function(chapters_list, duplicates_list, scanlation_groups):
	"""
	Filter out duplicate chapters from low priority groups in favor of higher priority groups.
	Note: Every group in list should have ['priority'] parameter.
	      It should be insert manually in resolve_manual_function.
	      The function also inserts the JSON scanlate group name and priority into each duplicated chapter.
	"""
	scanlation_groups.sort(key=lambda x: x["priority"])
	
	for duplicates_set in duplicates_list:
		prior_chapter = None
		for duplicate in duplicates_set:
			duplicate_group_id = _get_chapter_scanlation_id(duplicate)
			for group in scanlation_groups:
				if duplicate_group_id == group["id"]:
					duplicate["scanlate-name"] = group["attributes"]["name"]
					duplicate["scanlate-priority"] = group["priority"]
					if prior_chapter == None:
						prior_chapter = duplicate
					elif prior_chapter["scanlate-priority"] > duplicate["scanlate-priority"]:
						if prior_chapter in chapters_list:
							chapters_list.remove(prior_chapter)
						prior_chapter = duplicate
		
		for duplicate in duplicates_set:
			if duplicate != prior_chapter and duplicate in chapters_list:
				chapters_list.remove(duplicate)
	
	return chapters_list

def _get_chapter_scanlation_id(chapter):
	for relation in chapter["relationships"]:
		if relation["type"] == "scanlation_group":
			return(relation["id"])

def _get_scanlation_group_info(group_id):
	return get_json("https://api.mangadex.org/group/{}".format(group_id))["data"]