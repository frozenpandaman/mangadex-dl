"""
Mangadex-dl: archive.py
Functions for archiving the manga directory.
"""

import os, shutil, zipfile

def archive_manga(manga_directory, archive_mode, is_keep,  gui={"set": False}):
	if archive_mode == None:
		return
	
	print("\nArchive downloaded chapters...")
	
	directory_list = []
	
	if archive_mode == "manga":
		# archive whole manga directory
		directory_list.append(manga_directory)
	elif archive_mode == "volume":
		# archive volume directories
		directory_list += map(lambda d: os.path.join(manga_directory, d), next(os.walk(manga_directory))[1])
	else:
		for volume_dir in os.listdir(manga_directory):
			volume_dir_path = os.path.join(manga_directory, volume_dir)
			if os.path.isdir(volume_dir_path):
				# archive chapter directories
				directory_list += map(lambda d: os.path.join(volume_dir_path, d), next(os.walk(volume_dir_path))[1])
	
	# skip directories that have already been archived before
	directory_list = list(filter(lambda x: not os.path.exists(x + ".zip"), directory_list))
	
	directory_count_archived = 1
	directory_count_max = len(directory_list)
	
	# gui progress should be tk.DoubleVar
	if gui["set"]:
		gui["progress"].set(directory_count_archived)
	
	if directory_count_max == 0:
			print("  Looks like there is nothing to archive here.", end="")
	
	for directory in directory_list:
		_archive_directory(directory, is_keep)
		print("\r  Archiving [{:3}/{:3}]...".format(directory_count_archived, directory_count_max), end="")
		directory_count_archived += 1

		if gui["set"]:
			gui["progress"].set((directory_count_archived/directory_count_max)*100)
			if gui["exit"]:
				break
		
	print("\nArchiving completed successfully")

def _archive_directory(directory, is_keep):
	archive_format = "zip" # you can change that to cbz
	zip_name = "{}.{}".format(directory, archive_format)
	
	with zipfile.ZipFile(zip_name, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as zip_file:
		for root, dirs, files in os.walk(directory):
			for file in files:
				filename = os.path.join(root, file)
				arcname = os.path.relpath(os.path.join(root, file), directory)
				zip_file.write(filename, arcname)
	if not is_keep:
		shutil.rmtree(directory)
