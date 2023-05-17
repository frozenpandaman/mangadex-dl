"""
Mangadex-dl: gui.py
Initializes GUI version.
"""

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import json
import traceback
import concurrent.futures
from pathlib import Path

from mangadex_dl import utils
from mangadex_dl import parse
from mangadex_dl import archive as ar
from mangadex_dl import download as dl
from mangadex_dl import duplicate as dup

def init_gui(args):
    if args.manga_urls:
        for manga_url in args.manga_urls:
            _dl_gui(manga_url, args)
    else:
        _dl_gui("", args)

def _dl_gui(manga_url, args):
    root = Tk()
    root.geometry("850x530")
    try:
        app = _MangadexDlGui(root, manga_url, args)
        root.protocol("WM_DELETE_WINDOW", app.cb_on_closing)
        root.mainloop()
    except Exception as e:
        print(traceback.format_exc())
        messagebox.showinfo(message=f"Error: {e}\n\nSkip download.")

class _MangadexDlGui:

    def __init__(self, root, manga_url, args):
        # technical elements
        self.root = root
        self.block = False
        self.tree_a = None
        self.tree_b = None
        self.padding = 5 # i don't see how to add a margin through the global styles, so we add this every time in each widget
        self.indicator = None
        self.status = StringVar(value="Enter a URL or search query in the searchbar")
        self.future = None
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.lib_options = {"set": True, "exit": False, "thread_pool": None,
                            "progress_chapter": DoubleVar(value=0.0),
                            "progress_page": DoubleVar(value=0.0),
                            "progress_chapter_text": StringVar(value="[ - / - ]"),
                            "progress_page_text": StringVar(value="[ - / - ]")}

        # manga-relative vars
        self.manga_info = None
        self.chapters_list = []
        self.scanlation_groups = []
        self.chapters_list_selected = []
        self.duplicated_chapters_list = []
        self.manga_text_info = StringVar(value="Insert URL and press Search.")
        self.manga_url = StringVar(value=manga_url)
        self.manga_list_found = []
        self.manga_list_found_var = StringVar(value=self.manga_list_found)
        self.chapters_len_available = StringVar(value="Available chapters")
        self.chapters_len_download = StringVar(value="Chapters to download")

        # process command-line arguments
        args.outdir = utils.check_output_directory(args.outdir)
        self.args = args
        self.convert_args_to_stringvar(args)

        # init interface
        self.root.title("Mangadex-dl")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        mainframe = ttk.Notebook(self.root)
        mainframe.grid(column=0, row=0, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

        self.tab_settings = self.init_tab_settings()
        self.tab_search = self.init_tab_search()
        self.tab_scanlate = self.init_tab_scanlate()
        self.tab_download = self.init_tab_download()

        mainframe.add(self.tab_settings, text="Settings")
        mainframe.add(self.tab_search, text="Search")
        mainframe.add(self.tab_scanlate, text="Group Priority")
        mainframe.add(self.tab_download, text="Download")

        statusbar = self.init_statusbar(self.root)
        statusbar.grid(column=0, row=1, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

    ##########################
    #   FUNCTIONS SECTION    #
    ##########################

    def async_run(self, f, *args):
        if not self.block:
            self.future = self.thread_pool.submit(lambda: self.async_wrap(f, *args))
        else:
            messagebox.showinfo(message="Wait until the current operation completes.")

    def async_wrap(self, f, *args):
        try:
            self.block = True
            self.set_interface_state(False)
            self.indicator.start()
            f(*args)
        except Exception as e:
            print(traceback.format_exc())
            self.status.set("Something went wrong! Please try again.")
            messagebox.showinfo(message=f"Error: {e}")
        finally:
            self.future = None
            self.block = False
            self.set_interface_state(True)
            self.indicator.stop()

    def set_interface_state(self, state=True):
        frames = [self.tab_settings, self.tab_search, self.tab_scanlate, self.tab_download]
        for frame in frames:
            self.set_widget_state(frame, state)

    def set_widget_state(self, widget, state):
        childrens = widget.winfo_children()
        if childrens:
            for child in childrens:
                self.set_widget_state(child, state)
        else:
            try:
                if widget.winfo_class() == "Listbox": # i cant take it anymore
                    widget.configure(state="normal" if state else "disable")
                else:
                    widget.configure(state="enable" if state else "disable")
            except:
                pass

    def update_manga_info(self):
        s = f"Title: {self.manga_info.title}\n"\
            f"Author: {', '.join(self.manga_info.authors)}\n"\
            f"Artist: {', '.join(self.manga_info.artists)}\n"\
            f"Year: {self.manga_info.year}\n"\
            f"Status: {self.manga_info.status}\n\n"\
            f"Last Volume: {self.manga_info.last_volume}\n"\
            f"Last Chapter: {self.manga_info.last_chapter}\n\n"\
            f"Original Language: {self.manga_info.original_language}\n"\
            f"Content Rating: {self.manga_info.content_rating}\n"\
            f"Demographic: {self.manga_info.demographic}\n\n"\
            f"Format: {', '.join(self.manga_info.tags.format)}\n"\
            f"Themes: {', '.join(self.manga_info.tags.theme)}\n"\
            f"Genres: {', '.join(self.manga_info.tags.genre)}\n\n"\
            f"Description: {self.manga_info.description}"
        self.manga_text_info.set(s)

    def resolve_duplicates_manual_gui(self, chapters_list, duplicated_chapters_list, scanlation_groups):
        self.duplicated_chapters_list = duplicated_chapters_list
        self.scanlation_groups = scanlation_groups
        self.scanlation_groups_priority = [StringVar(value="5") for i in self.scanlation_groups]

        self.destroy_resolve_gui()

        index = 0
        for group in self.scanlation_groups:
            label = ttk.Label(self.tab_scanlate, text=group["attributes"]["name"])
            label.grid(column=0, row=index+1, sticky=(E), pady=self.padding, padx=self.padding)

            combobox = ttk.Combobox(self.tab_scanlate, state="readonly", textvariable=self.scanlation_groups_priority[index])
            combobox["values"] = ("1", "2", "3", "4", "5")
            combobox.grid(column=1, row=index+1, sticky=(W), pady=self.padding, padx=self.padding)

            index += 1

        label = ttk.Label(self.tab_scanlate, text="Highest priority: 1.\nLowest priority: 5.")
        label.grid(column=0, row=0, sticky=(W), pady=self.padding, padx=self.padding)

        button = ttk.Button(self.tab_scanlate, text="Apply", command=self.cb_resolve_duplicates)
        button.grid(column=1, row=0, sticky=(E), pady=self.padding, padx=self.padding)

        return chapters_list

    def destroy_resolve_gui(self):
        for widget in self.tab_scanlate.winfo_children():
            widget.destroy()

    def get_chapters_list(self):
        return utils.get_chapters_list(self.manga_info.uuid, self.args.language.get())

    def update_search_results_list(self):
        name_list = [f"{manga.title} ({manga.year}) by {', '.join(manga.authors)}" for manga in self.manga_list_found]
        self.manga_list_found_var.set(name_list)

    def load_tree_chapters(self):
        # Each volume in the tree is open by default.
        # Tkinter does not provide a way to automatically update
        # the list along with the tree or a way to keep open volumes between trees.
        # Doing it manually is fraught with a bunch of synchronization errors and others,
        # and is generally not worth the time.
        self.chapters_list.sort(key=self.sort_chapters_list_key)
        self.chapters_list_selected.sort(key=self.sort_chapters_list_key)

        self.load_tree(self.tree_a, self.chapters_list)
        self.load_tree(self.tree_b, self.chapters_list_selected)

        self.chapters_len_available.set(f"Available chapters: {len(self.chapters_list)}")
        self.chapters_len_download.set(f"Chapters to download: {len(self.chapters_list_selected)}")

    def load_tree(self, tree, array):
        """
        Note: This function modifies the given array.
        Adds text value to each chapter dict:
        ['volume'], ['chapter'] and ['scanlate_name']
        """
        self.clear_tree(tree)

        volume_name = None
        for chapter in array:
            c_v = chapter["attributes"]["volume"] or "Unknown"
            c_n = chapter["attributes"]["chapter"] or "Oneshot"
            c_t = chapter["attributes"]["title"] or ""

            chapter_volume = f"Volume {c_v}"
            chapter_name = f"Chapter {c_n}"
            chapter_title = f"{chapter_name} {c_t}"

            if self.args.resolve.get() != "one":
                if "scanlate_name" not in chapter:
                    scanlate_id = dup.get_chapter_scanlation_id(chapter)
                    if scanlate_id:
                        scanlate_json = dup.get_scanlation_group_info(scanlate_id)
                        chapter["scanlate_name"] = scanlate_json["attributes"]["name"]
                    else:
                        chapter["scanlate_name"] = "No Scanlate Group"
                chapter_title += f" [{chapter['scanlate_name']}]"

            chapter["volume"] = chapter_volume
            chapter["chapter"] = chapter_name
            if volume_name != chapter_volume:
                volume_name = chapter_volume
                tree.insert("", "end", volume_name, text=volume_name, values=("volume", json.dumps(chapter)))
                tree.item(volume_name, open=True)
            tree.insert(volume_name, "end", text=chapter_title, values=("chapter", json.dumps(chapter)))

    def tree_item_move(self, tree_a, tree_b, list_a, list_b, item):
        item_type = item["values"][0]
        item_chap = json.loads(item["values"][1])

        if item_type == "volume":
            target_volume = item_chap["volume"]
            selected_list = []

            for chapter in list_a:
                if chapter["volume"] == target_volume:
                    selected_list.append(chapter)
            for chapter in selected_list:
                list_a.remove(chapter)
                list_b.append(chapter)

        elif item_type == "chapter":
            list_a.remove(item_chap)
            list_b.append(item_chap)

        self.load_tree_chapters()

    def clear_tree(self, tree):
        tree.delete(*tree.get_children())

    def sort_chapters_list_key(self, chapter):
        c_v = chapter["attributes"]["volume"] or 0.0
        c_c = chapter["attributes"]["chapter"] or 0.0
        option_a = float(c_v)
        option_b = float(c_c)
        return (option_a, option_b)

    def convert_args_to_stringvar(self, args):
        # tk doesnt support python's types like None, so convert to string
        self.args.outdir = StringVar(value=args.outdir)
        self.args.archive = StringVar(value=str(args.archive))
        self.args.download = StringVar(value=str(args.download))
        self.args.language = StringVar(value=args.language)
        self.args.keep = BooleanVar(value=args.keep)
        self.args.datasaver = BooleanVar(value=args.datasaver)
        self.args.resolve = StringVar(value=args.resolve)

    ##########################
    #       CALLBACKS        #
    ##########################
    def cb_on_closing(self):
        try:
            self.thread_pool.shutdown(wait=False, cancel_futures=True)
            if self.lib_options["thread_pool"]:
                self.lib_options["thread_pool"].shutdown(wait=False, cancel_futures=True)
            self.root.destroy()
        except Exception as e:
            pass

    def cb_search_result_select(self, e):
        if e:
            self.manga_info = self.manga_list_found[e[0]]
            self.manga_url.set(self.manga_info.uuid)
            self.update_manga_info()

    def cb_get_manga_info(self):
        if not self.manga_url.get():
            messagebox.showinfo(message="Paste the URL first.\nChange to the English keyboard layout if you cannot paste text.")
            return

        # clearing old results
        self.destroy_resolve_gui()
        self.clear_tree(self.tree_a)
        self.clear_tree(self.tree_b)
        self.chapters_list = []
        self.chapters_list_selected = []
        self.chapters_len_available.set("Available chapters")
        self.chapters_len_download.set("Chapters to download")

        # start downloading
        self.status.set("Receiving manga's info...")

        if not utils.get_uuid(self.manga_url.get()):
            self.manga_list_found = utils.search_manga(self.manga_url.get(), self.args.language.get())
            if not self.manga_list_found:
                self.status.set("Nothing was found according to your request")
            else:
                self.status.set("Select title and search again")
            self.update_search_results_list()
            return

        self.manga_info = utils.get_manga_info(self.manga_url.get(), self.args.language.get())
        self.update_manga_info()

        self.status.set("Receiving available chapters...")
        self.chapters_list = self.get_chapters_list()

        self.status.set("Resolving duplicated chapters...")
        self.chapters_list = dup.resolve_duplicated_chapters(self.chapters_list, self.args.resolve.get(), self.resolve_duplicates_manual_gui)

        if self.args.download.get() != "False":
            self.status.set("Parsing download range...")
            dl_list = parse.parse_range(self.args.download.get())
            self.chapters_list_selected = parse.get_requested_chapters(self.chapters_list, dl_list)
            for chapter in self.chapters_list_selected:
                if chapter in self.chapters_list:
                    self.chapters_list.remove(chapter)

        self.status.set("Updating chapters tree...")
        self.load_tree_chapters()

        self.status.set("Manga info received")

    def cb_change_outdir(self):
        self.args.outdir.set(filedialog.askdirectory())

    def cb_resolve_duplicates(self):
        index = 0
        # merge already selected chapters into
        self.chapters_list += self.chapters_list_selected
        self.chapters_list_selected = []
        for group in self.scanlation_groups:
            group["priority"] = self.scanlation_groups_priority[index].get()
            index += 1
        self.chapters_list = dup.resolve_scanlate_priority_function(self.chapters_list,
                                                                    self.duplicated_chapters_list,
                                                                    self.scanlation_groups)
        self.load_tree_chapters()
        self.status.set("Chapters filtered")

    def cb_tree_item_move(self, tree_a, tree_b, list_a, list_b):
        if self.block:
            messagebox.showinfo(message="Wait for the download to complete.")
            return
        item = tree_a.item(tree_a.focus())
        if not isinstance(item["open"], bool) and item["text"] != "":
            self.tree_item_move(tree_a, tree_b, list_a, list_b, item)

    def cb_move_all_to_selected(self):
        self.chapters_list_selected += self.chapters_list
        self.chapters_list = []
        self.load_tree_chapters()

    def cb_download_chapters(self):
        if not self.chapters_list_selected:
            messagebox.showinfo(message="First click on chapters from the list on the left to move them to the download list.")
            return

        self.status.set("Downloading started...")

        manga_directory = utils.create_manga_directory(Path(self.args.outdir.get()),
                                                       self.manga_info.title_en,
                                                       self.manga_info.uuid)
        dl.download_chapters(self.chapters_list_selected,
                             manga_directory,
                             self.args.datasaver.get(),
                             self.lib_options)

        if self.args.archive.get() != "False":
            self.lib_options["progress_chapter"].set(0)
            self.lib_options["progress_page"].set(0)
            self.lib_options["progress_chapter_text"].set("[ - / - ]")
            self.lib_options["progress_page_text"].set("[ - / - ]")
            self.status.set("Archive downloaded chapters...")
            ar.archive_manga(manga_directory, self.args.archive.get(), self.args.keep.get(), self.lib_options)

        self.lib_options["progress_chapter"].set(0)
        self.lib_options["progress_page"].set(0)
        self.lib_options["progress_chapter_text"].set("[ - / - ]")
        self.lib_options["progress_page_text"].set("[ - / - ]")

        self.status.set("Manga was downloaded {}successfully".format("and archived " if self.args.archive.get() != "False" else ""))

    def cb_show_help(self):
        help_str = "1. Check Settings tab. The settings are applied immediately when changed, but the old search results are preserved.\n"\
            "2. Paste URL or search query in searchbar and press Search. Change to the English keyboard layout if you cannot paste text.\n"\
            "3. Select desired chapters in Download tab, then press Download. Mouse click on individual volumes or chapters entry.\n\n"\
            "If you specify two or more manga links on the command line, close the main window after downloading, the following window should open.\n\n"\
            "The options specified on the command line will be the default values in the current Settings tab."
        messagebox.showinfo(message=help_str)

    ##########################
    # INIT INTERFACE SECTION #
    ##########################
    def init_tab_settings(self):
        frame = ttk.Frame()

        # language
        label_lang = ttk.Label(frame, text="Language:")
        label_lang.grid(column=0, row=0, sticky=(E), pady=self.padding, padx=self.padding)

        combobox_lang = ttk.Combobox(frame, textvariable=self.args.language)
        combobox_lang["values"] = ("en", "ru", "fr", "uk", "ja", "zh", "ko", "id")
        combobox_lang.grid(column=1, row=0, sticky=(W), pady=self.padding, padx=self.padding)

        separator_a = ttk.Separator(frame, orient=HORIZONTAL)
        separator_a.grid(column=0, row=1, columnspan=5, sticky=(W, E))

        # out directory
        label_dir = ttk.Label(frame, text="Output directory:")
        label_dir.grid(column=0, row=2, sticky=(E), pady=self.padding, padx=self.padding)

        label_dir_view = ttk.Label(frame)
        label_dir_view["textvariable"] = self.args.outdir
        label_dir_view.grid(column=1, row=2, sticky=(W), pady=self.padding, padx=self.padding)

        button_dir = ttk.Button(frame, text="Change", command=self.cb_change_outdir)
        button_dir.grid(column=2, row=2, sticky=(W), pady=self.padding, padx=self.padding)

        separator_b = ttk.Separator(frame, orient=HORIZONTAL)
        separator_b.grid(column=0, row=3, columnspan=5, sticky=(W, E))

        # archive
        label_archive = ttk.Label(frame, text="Archive:")
        label_archive.grid(column=0, row=4, sticky=(E), pady=self.padding, padx=self.padding)

        radio_archive_a = ttk.Radiobutton(frame, text="None", variable=self.args.archive, value="False")
        radio_archive_b = ttk.Radiobutton(frame, text="Whole manga", variable=self.args.archive, value="manga")
        radio_archive_c = ttk.Radiobutton(frame, text="Volume", variable=self.args.archive, value="volume")
        radio_archive_d = ttk.Radiobutton(frame, text="Chapter", variable=self.args.archive, value="chapter")

        radio_archive_a.grid(column=1, row=4, sticky=(W), pady=self.padding, padx=self.padding)
        radio_archive_b.grid(column=1, row=5, sticky=(W), pady=self.padding, padx=self.padding)
        radio_archive_c.grid(column=2, row=4, sticky=(W), pady=self.padding, padx=self.padding)
        radio_archive_d.grid(column=2, row=5, sticky=(W), pady=self.padding, padx=self.padding)

        separator_c = ttk.Separator(frame, orient=HORIZONTAL)
        separator_c.grid(column=0, row=6, columnspan=5, sticky=(W, E))

        # keep original
        label_archive = ttk.Label(frame, text="Keep original\nafter archiving:", justify=RIGHT)
        label_archive.grid(column=0, row=7, sticky=(E), pady=self.padding, padx=self.padding)

        check_keep = ttk.Checkbutton(frame, text="", variable=self.args.keep, onvalue="1", offvalue="0")
        check_keep.grid(column=1, row=7, sticky=(W), pady=self.padding, padx=self.padding)

        separator_d = ttk.Separator(frame, orient=HORIZONTAL)
        separator_d.grid(column=0, row=8, columnspan=5, sticky=(W, E))

        # data saver
        label_datasaver = ttk.Label(frame, text="Download in\nworse quality:", justify=RIGHT)
        label_datasaver.grid(column=0, row=9, sticky=(E), pady=self.padding, padx=self.padding)

        check_datasaver = ttk.Checkbutton(frame, text="", variable=self.args.datasaver, onvalue="1", offvalue="0")
        check_datasaver.grid(column=1, row=9, sticky=(W), pady=self.padding, padx=self.padding)

        separator_e = ttk.Separator(frame, orient=HORIZONTAL)
        separator_e.grid(column=0, row=10, columnspan=5, sticky=(W, E))

        # resolve duplicate
        label_resolve = ttk.Label(frame, text="How to resolve\nduplicates:", justify=RIGHT)
        label_resolve.grid(column=0, row=11, sticky=(E), pady=self.padding, padx=self.padding)

        radio_resolve_a = ttk.Radiobutton(frame, text="Display all", variable=self.args.resolve, value="all")
        radio_resolve_b = ttk.Radiobutton(frame, text="Display only one", variable=self.args.resolve, value="one")
        radio_resolve_c = ttk.Radiobutton(frame, text="Manually set scanlate priorities", variable=self.args.resolve, value="manual")

        radio_resolve_a.grid(column=1, row=11, sticky=(W), pady=self.padding, padx=self.padding)
        radio_resolve_b.grid(column=1, row=12, sticky=(W), pady=self.padding, padx=self.padding)
        radio_resolve_c.grid(column=2, row=11, sticky=(W), pady=self.padding, padx=self.padding)

        separator_d = ttk.Separator(frame, orient=HORIZONTAL)
        separator_d.grid(column=0, row=13, columnspan=5, sticky=(W, E))

        # help
        label_help = ttk.Label(frame, text="Note: after changing language or duplicate settings reload URL in Search tab again.")
        label_help.grid(column=0, row=14, columnspan=5, sticky=(W, E), pady=self.padding, padx=self.padding)

        return frame

    def init_tab_search(self):
        frame = ttk.Frame()
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=0, minsize=320)
        frame.columnconfigure(1, weight=1)

        ###
        searchbar_frame = ttk.Frame(frame)
        searchbar_frame.grid(column=0, row=0, columnspan=2, sticky=(E, W))
        searchbar_frame.columnconfigure(0, weight=0)
        searchbar_frame.columnconfigure(1, weight=1)
        searchbar_frame.columnconfigure(2, weight=0)

        label = ttk.Label(searchbar_frame, text="URL or search query:")
        label.grid(column=0, row=0, pady=self.padding, padx=self.padding)

        entry = ttk.Entry(searchbar_frame, textvariable=self.manga_url)
        entry.grid(column=1, row=0, sticky=(E, W), pady=self.padding, padx=self.padding)

        button = ttk.Button(searchbar_frame, text="Search", command=lambda:self.async_run(self.cb_get_manga_info))
        button.grid(column=2, row=0, pady=self.padding, padx=self.padding)
        ###
        search_results_frame = ttk.Labelframe(frame, text="Search Results")
        search_results_frame.grid(column=0, row=1, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)
        search_results_frame.rowconfigure(0, weight=1)
        search_results_frame.rowconfigure(1, weight=0)
        search_results_frame.columnconfigure(0, weight=1)
        search_results_frame.columnconfigure(1, weight=0)

        result_listbox = Listbox(search_results_frame, listvariable=self.manga_list_found_var)
        result_listbox.grid(column=0, row=0, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

        scrollbar_a = ttk.Scrollbar(search_results_frame, orient=VERTICAL, command=result_listbox.yview)
        scrollbar_a.grid(column=1, row=0, sticky=(N, S))
        scrollbar_b = ttk.Scrollbar(search_results_frame, orient=HORIZONTAL, command=result_listbox.xview)
        scrollbar_b.grid(column=0, row=1, columnspan=2, sticky=(E, W))

        result_listbox.configure(yscrollcommand=scrollbar_a.set)
        result_listbox.configure(xscrollcommand=scrollbar_b.set)
        result_listbox.bind("<<ListboxSelect>>", lambda e: self.cb_search_result_select(result_listbox.curselection()))
        ###
        frame_info = ttk.Labelframe(frame, text="Info")
        frame_info.grid(column=1, row=1, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

        label_info = ttk.Label(frame_info, textvariable=self.manga_text_info, wraplength=500)
        label_info.grid(column=0, row=0, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)
        return frame

    def init_tab_download(self):
        frame = ttk.Frame()
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=0)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=0)

        # labels
        label_a = ttk.Label(frame, textvariable=self.chapters_len_available)
        label_a.grid(column=0, row=0, pady=self.padding, padx=self.padding)

        label_b = ttk.Label(frame, textvariable=self.chapters_len_download)
        label_b.grid(column=2, row=0, pady=self.padding, padx=self.padding)

        # trees
        self.tree_a = ttk.Treeview(frame)
        self.tree_a.grid(column=0, row=1, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

        self.tree_b = ttk.Treeview(frame)
        self.tree_b.grid(column=2, row=1, sticky=(N, S, E, W), pady=self.padding, padx=self.padding)

        scrollbar_a = ttk.Scrollbar(frame, orient=VERTICAL, command=self.tree_a.yview)
        scrollbar_a.grid(column=1, row=1, sticky=(N, S))

        scrollbar_b = ttk.Scrollbar(frame, orient=VERTICAL, command=self.tree_b.yview)
        scrollbar_b.grid(column=3, row=1, sticky=(N, S))

        self.tree_a.configure(yscrollcommand=scrollbar_a.set)
        self.tree_b.configure(yscrollcommand=scrollbar_b.set)

        self.tree_a.bind("<ButtonRelease-1>", lambda x: self.cb_tree_item_move(self.tree_a, self.tree_b,
                                                                               self.chapters_list, self.chapters_list_selected))
        self.tree_b.bind("<ButtonRelease-1>", lambda x: self.cb_tree_item_move(self.tree_b, self.tree_a,
                                                                               self.chapters_list_selected, self.chapters_list))

        # action bar
        button_move_all = ttk.Button(frame, text="Move all", command=self.cb_move_all_to_selected)
        button_move_all.grid(column=0, row=2, sticky=(W), pady=self.padding, padx=self.padding)

        button_download = ttk.Button(frame, text="Start download", command=lambda:self.async_run(self.cb_download_chapters))
        button_download.grid(column=2, row=2, sticky=(E), pady=self.padding, padx=self.padding)

        return frame

    def init_tab_scanlate(self):
        # ok, we can't make scrollbar for frame in tk
        frame = ttk.Frame()

        label = ttk.Label(frame, text="You can manually prioritize scanlate groups.\n"\
                          "Specify this in the settings tab, reload the URL and set the priorities in this tab.")
        label.grid(column=0, row=0, pady=self.padding, padx=self.padding)

        return frame

    def init_statusbar(self, root):
        frame = ttk.Frame(root)
        frame.rowconfigure(0, weight=0) # progressbar_chap, indicator
        frame.rowconfigure(1, weight=0) # progressbar_page, help button
        frame.rowconfigure(2, weight=0) # status text
        frame.columnconfigure(0, weight=0) # progressbar labels
        frame.columnconfigure(1, weight=1) # progressbar, status
        frame.columnconfigure(2, weight=0) # progress numbers
        frame.grid_columnconfigure(2, minsize=90)
        frame.columnconfigure(3, weight=0) # separator
        frame.columnconfigure(4, weight=0) # indicator, help button

        ###
        label_a = ttk.Label(frame, text="Chapters: ")
        label_a.grid(column=0, row=0, sticky=(E), pady=self.padding, padx=self.padding)

        label_b = ttk.Label(frame, text="Pages: ")
        label_b.grid(column=0, row=1, sticky=(E), pady=self.padding, padx=self.padding)

        label_c = ttk.Label(frame, text="Status: ")
        label_c.grid(column=0, row=2, sticky=(E), pady=self.padding, padx=self.padding)
        ###
        progressbar_chap = ttk.Progressbar(frame, orient=HORIZONTAL, mode="determinate", variable=self.lib_options["progress_chapter"])
        progressbar_chap.grid(column=1, row=0, sticky=(E, W), pady=self.padding, padx=self.padding)

        progressbar_page = ttk.Progressbar(frame, orient=HORIZONTAL, mode="determinate", variable=self.lib_options["progress_page"])
        progressbar_page.grid(column=1, row=1, sticky=(E, W), pady=self.padding, padx=self.padding)

        status = ttk.Label(frame, textvariable=self.status)
        status.grid(column=1, row=2, sticky=(W), pady=self.padding, padx=self.padding)
        ###
        progress_chapter_text = ttk.Label(frame, textvariable=self.lib_options["progress_chapter_text"])
        progress_chapter_text.grid(column=2, row=0, sticky=(E, W), pady=self.padding, padx=self.padding)

        progress_page_text = ttk.Label(frame, textvariable=self.lib_options["progress_page_text"])
        progress_page_text.grid(column=2, row=1, sticky=(E, W), pady=self.padding, padx=self.padding)
        ###
        separator = ttk.Separator(frame, orient=VERTICAL)
        separator.grid(column=3, row=0, rowspan=3, sticky=(N, S))
        ###
        self.indicator = ttk.Progressbar(frame, orient=HORIZONTAL, mode="indeterminate")
        self.indicator.grid(column=4, row=0, sticky=(E, W), pady=self.padding, padx=self.padding)

        button = ttk.Button(frame, text="?", command=self.cb_show_help)
        button.grid(column=4, row=1, sticky=(E, W), pady=self.padding, padx=self.padding)
        ###

        return frame
