
import  requests, json ,sqlite3, time, shutil, os ,re , zipfile , html 




conn = sqlite3.connect('manga.db')

c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS manga (
          _id blob,
          manga_name text,
          last_ch text     
          )""")



def viewdb():
    c.execute('SELECT * FROM manga')
    stuff =c.fetchall()

    txt = """"""

    end = len(stuff)

    for i in range(0,end):
        _id = stuff[i][0]
        name = stuff[i][1]
        last_ch = stuff[i][2]
        txt += f"""---\nid = {_id}\nName = {name}\nLast chapter = {last_ch}\n"""

    if txt ==None:
        print("Db is empty")
    else:
        print(txt)



def adddb(_id):
    u = "https://api.mangadex.org/manga/{}".format(_id)
    url = "https://api.mangadex.org/manga/{}/feed?order[chapter]=desc&order[volume]=desc&limit=1&translatedLanguage[]=en&offset=0".format(_id)
    r = requests.get(u)
    req = requests.get(url)
    name_data = r.json()
    ch_data = req.json()
    chap_num = ch_data["data"][0]["attributes"]["chapter"]
    name = name_data['data']['attributes']['title']['en']
    try:    
        c.execute('INSERT INTO manga VALUES (:_id, :name, :last_ch)', {"_id":_id, "name": name, "last_ch": chap_num})
        conn.commit()
        print(f'{name} has been added to db')
    except Exception as e:
        print(e)


def edit_ch(_id):
    new_ch = input("Enter chapter number: ").strip()
    c.execute("""UPDATE manga SET last_ch = :last_ch
                 WHERE _id = :_id""",
                 {'_id': _id,  'last_ch': new_ch})
    print(f'Chapter updated to {new_ch}')
    conn.commit()


def removedb(_id):
    c.execute('SELECT * FROM manga WHERE _id= :_id', {'_id': _id})
    stuff = c.fetchall()
    name = stuff[0][1]
    last_ch = stuff[0][2]
    try:
        c.execute("DELETE from manga WHERE _id = :_id AND manga_name = :name AND last_ch = :last_ch",{"_id":_id, "name": name, "last_ch": last_ch})
        conn.commit()
        print(f'{name} removed from db.')
    except Exception as e:
        print(e)


def updater():
    c.execute('SELECT * FROM manga')
    stuff =c.fetchall()

    end = len(stuff)
    updates = []

    for i in range(0,end):
        _id = stuff[i][0]
        name = stuff[i][1]
        last_ch = stuff[i][2]
        chaps = []
        conv = []
        url = 'https://api.mangadex.org/manga/{}/feed?order[chapter]=desc&order[volume]=desc&limit=500&translatedLanguage[]=en&offset=0'.format(_id)
        time.sleep(2)
        req = requests.get(url)
        results = req.json()
        for chapter in results["data"]:
            chap_num = chapter["attributes"]["chapter"]
            chap_uuid = chapter["id"]
            conv.append(str(chap_num))
            chaps.append(str(chap_uuid))

        index = conv.index(last_ch)
        if index>0:
            print(f"{index} chapters available for {name}\n")
            conv = (conv[:index])[::-1]
            chaps = (chaps[:index])[::-1]
            for x in range(0,index):
                updates.append([conv[x], chaps[x]])
                #updates.append(chaps[x])
                downloader(updates,name)
                chap_num = conv[x]
                c.execute("""UPDATE manga SET last_ch = :last_ch
                 WHERE _id = :_id""",
                 {'_id': _id,  'last_ch': chap_num})
                conn.commit()
                updates.pop(0)
            continue
        else:
            continue

    
#removedb("80c4c4bc-be9c-400a-8cc0-57b1d0b8a87f")
#dddb("80c4c4bc-be9c-400a-8cc0-57b1d0b8a87f")
#viewdb()
#edit_ch("0aea9f43-d4a9-4bf7-bebc-550a512f9b95")
#updater()


def downloader(requested_chapters, title,zip_up=1,  ds=0):
	try:
		for chapter_info in requested_chapters:
			print("Downloading chapter {}...".format(chapter_info[0]))
			r = requests.get("https://api.mangadex.org/chapter/{}".format(chapter_info[1]))
			chapter = json.loads(r.text)

			r = requests.get("https://api.mangadex.org/at-home/server/{}".format(chapter_info[1]))
			baseurl = r.json()["baseUrl"]

			# make url list
			images = []
			accesstoken = ""
			chaphash = chapter["data"]["attributes"]["hash"]
			datamode = "dataSaver" if ds else "data"
			datamode2 = "data-saver" if ds else "data"

			for page_filename in chapter["data"]["attributes"][datamode]:
				images.append("{}/{}/{}/{}".format(baseurl, datamode2, chaphash, page_filename))

			# get group names & make combined name
			group_uuids = []
			for entry in chapter["data"]["relationships"]:
				if entry["type"] == "scanlation_group":
					group_uuids.append(entry["id"])

			groups = ""
			for i, group in enumerate(group_uuids):
				if i > 0:
					groups += " & "
				r = requests.get("https://api.mangadex.org/group/{}".format(group))
				name = r.json()["data"]["attributes"]["name"]
				groups += name
			groupname = re.sub('[/<>:"/\\|?*]', '-', groups)

			title = re.sub('[/<>:"/\\|?*]', '-', html.unescape(title))
			chapnum = zpad(chapter_info[0])
			if chapnum != "Oneshot":
				chapnum = 'c' + chapnum

			dest_folder = uniquify(title, chapnum, groupname)
			if not os.path.exists(dest_folder):
				os.makedirs(dest_folder)

			# download images
			for pagenum, url in enumerate(images, 1):
				filename = os.path.basename(url)
				ext = os.path.splitext(filename)[1]

				dest_filename = pad_filename("{}{}".format(pagenum, ext))
				outfile = os.path.join(dest_folder, dest_filename)

				r = requests.get(url)
				if r.status_code == 200:
					with open(outfile, 'wb') as f:
						f.write(r.content)
						print(" Downloaded page {}.".format(pagenum))
				else:
					# silently try again
					time.sleep(2)
					r = requests.get(url)
					if r.status_code == 200:
						with open(outfile, 'wb') as f:
							f.write(r.content)
							print(" Downloaded page {}.".format(pagenum))
					else:
						print(" Skipping download of page {} - error {}.".format(pagenum, r.status_code))
				time.sleep(0.5) # safely within limit of 5 requests per second
				# not reporting https://api.mangadex.network/report telemetry for now, sorry

			if zip_up:
				zip_name = os.path.join(os.getcwd(), "download", title, "{} {} [{}]".format(title, chapnum, groupname)) + ".cbz"
				chap_folder = os.path.join(os.getcwd(), "download", title, "{} [{}]".format(chapnum, groupname))
				with zipfile.ZipFile(zip_name, 'w') as myzip:
					for root, dirs, files in os.walk(chap_folder):
						for file in files:
							path = os.path.join(root, file)
							myzip.write(path, os.path.basename(path))
				print("\nChapter successfully packaged into .cbz file.\n")
				shutil.rmtree(chap_folder) # remove original folder of loose images
	except Exception as e:
		print(e)

def pad_filename(str):
	digits = re.compile('(\\d+)')
	pos = digits.search(str)
	if pos:
		return str[1:pos.start()] + pos.group(1).zfill(3) + str[pos.end():]
	else:
		return str

def float_conversion(tupl):
	try:
		x = float(tupl[0]) # (chap_num, chap_uuid)
	except ValueError: # empty string for oneshot
		x = 0
	return x

def find_id_in_url(url_parts):
	for part in url_parts:
		if "-" in part:
			return part

def zpad(num):
	if "." in num:
		parts = num.split('.')
		return "{}.{}".format(parts[0].zfill(3), parts[1])
	else:
		return num.zfill(3)


def uniquify(title, chapnum, groupname):
	counter = 1
	dest_folder = os.path.join(os.getcwd(), "download", title, "{} [{}]".format(chapnum, groupname))
	while os.path.exists(dest_folder):
		dest_folder = os.path.join(os.getcwd(), "download", title, "{}-{} [{}]".format(chapnum, counter, groupname))
		counter += 1
	return dest_folder


