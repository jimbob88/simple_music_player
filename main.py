try:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.messagebox as tkMessageBox
except:
    import Tkinter as tk
    import ttk
    import tkMessageBox
try:
    import ttkthemes
except:
    pass
import platform
import sys
import os
import time
import tinytag
import collections
import random
import ast
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gst


class music_player:
    def __init__(self, master):
        self.master = master
        self.master.geometry('1432x764')

        style = ttk.Style(self.master)

        self.menubar = tk.Menu(self.master)
        self.master.configure(menu=self.menubar)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Add Folder", command=self.add_folder_dialog)
        self.filemenu.add_command(label="Open M3U", command=self.add_m3u_dialog)
        self.filemenu.add_command(label="Save to Cache", command=self.save_to_cache)
        self.menubar.add_cascade(label="File", menu=self.filemenu)


        self.sidemenubar_frame = tk.Frame(self.master, width=250)
        self.sidemenubar_frame.grid(row=0, column=0, rowspan=2, sticky="ns")
        self.sidemenubar_frame.grid_rowconfigure(0, weight=1)
        self.sidemenubar_frame.grid_columnconfigure(0, weight=1)

        self.sidemenubar_treeview = ScrolledTreeView(self.sidemenubar_frame)
        self.sidemenubar_treeview.grid(row=0, column=0, sticky="nsew", pady=5)

        self.sidemenubar_treeview.heading("#0", text='Options')
        self.local_collection = self.sidemenubar_treeview.insert('', 'end', text='Local Collection', open=tk.TRUE)
        self.sidemenubar_treeview.insert(self.local_collection, 0, text='Music Collection')
        self.online_sources = self.sidemenubar_treeview.insert('', 'end', text='Online Sources')
        self.sidemenubar_treeview.insert(self.online_sources, 0, text='Radio Collection')
        self.sidemenubar_treeview.selection_set('I002')
        self.sidemenubar_treeview.focus('I002')

        self.main_frame = tk.Frame(self.master)
        self.main_frame.grid(row=0, column=1, columnspan=3, rowspan=2, sticky='nsew')

        self.radio_stations = collections.OrderedDict()
        self.artists = {}
        self.albums = {}
        self.genres = {}
        self.songs = collections.OrderedDict()

        self.controls_frame = tk.Frame(self.master, bg='white')
        self.controls_frame.grid(row=2, column=0, columnspan=4, sticky="nsew")
        self.main_frame_change()


        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_columnconfigure(2, weight=1)
        self.master.grid_columnconfigure(3, weight=1)



        self.genre_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        self.artist_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        self.album_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        self.music_treeview.bind('<<TreeviewSelect>>', lambda e: self.play_song())
        self.sidemenubar_treeview.bind('<<TreeviewSelect>>', lambda e: self.main_frame_change())
        self.master.bind('f5', lambda e: self.refresh_treeviews('music'))


        Gst.init()
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        #self.player.connect("about-to-finish",  lambda: print('CHANGE SONG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'))

        self.is_paused = tk.BooleanVar()
        self.is_paused.set(True)
        self.is_random = tk.BooleanVar()
        self.is_random.trace('w', lambda *args: self.shuffle_butt.state(['pressed' if self.is_random.get() else '!pressed']))
        self.is_random.set(False)
        self.is_repeat = tk.BooleanVar()
        self.is_repeat.trace('w', lambda *args: self.repeat_butt.state(['pressed' if self.is_repeat.get() else '!pressed']))
        self.is_repeat.set(False)

        self.curr_song = None
        self.curr_radio_station = None
        self.skip_trace = False

        self.open_cache()

    def main_frame_change(self):
        if self.sidemenubar_treeview.focus() == 'I002':
            self.music_collection_init()
        elif self.sidemenubar_treeview.focus() == 'I004':
            self.radio_collection_init()

    def music_collection_init(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.genre_treeview = ScrolledTreeView(self.main_frame)
        self.genre_treeview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.genre_treeview.heading("#0", text="Genre")

        self.artist_treeview = ScrolledTreeView(self.main_frame)
        self.artist_treeview.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.artist_treeview.heading("#0", text="Artist")

        self.album_treeview = ScrolledTreeView(self.main_frame)
        self.album_treeview.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.album_treeview.heading("#0", text="Album")

        self.music_treeview = ScrolledTreeView(self.main_frame)
        self.music_treeview.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.music_treeview["columns"] = ("Title", "Genre", "Artist", "Album", "Time")
        self.music_treeview.heading("#0", text='Track', command=lambda: self.refresh_treeviews('music', sort_by='Track Number'))
        self.music_treeview.column("#0", width=20)
        for col in self.music_treeview["columns"]:
            if col == "Time":
                self.music_treeview.column(col, width=30)
                self.music_treeview.heading(col, text=col, command=lambda: self.refresh_treeviews('music', sort_by='Duration'))
            else:
                self.music_treeview.heading(col, text=col, command=lambda sort_by=col: self.refresh_treeviews('music', sort_by=sort_by))

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        ########################################## Controls Frame ###################################################
        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        self.previous_track = ttk.Button(self.controls_frame, text="Previous Track", command=lambda: self.change_song(-1))
        self.previous_track.grid(row=0, column=0)

        self.play_butt = ttk.Button(self.controls_frame, text="Play/Pause", command=lambda: self.play_pause())
        self.play_butt.grid(row=0, column=1)

        self.next_track = ttk.Button(self.controls_frame, text="Next Track", command=lambda: self.change_song(1))
        self.next_track.grid(row=0, column=2)

        self.album_icon = tk.Label(self.controls_frame, bg='white')
        self.album_icon.grid(row=0, column=3)

        self.song_title = tk.Label(self.controls_frame, bg='white')
        self.song_title.grid(row=0, column=4)

        self.song_prog_scl_var = tk.StringVar()
        self.song_prog_scl_var.set(0)
        self.song_prog_scl_var.trace('w', self.slider_change)
        self.song_prog_scl = ttk.Scale(self.controls_frame, from_=0, to=100, orient='horizontal', variable=self.song_prog_scl_var)
        self.song_prog_scl.grid(row=0, column=5, sticky='ew')
        self.controls_frame.grid_columnconfigure(5, weight=1)
        self.controls_frame.grid_columnconfigure(0, weight=0)

        self.song_prog_lbl = tk.Label(self.controls_frame, bg='white')
        self.song_prog_lbl.grid(row=0, column=6)

        self.repeat_butt = ttk.Button(self.controls_frame, text='Repeat', command=lambda: self.is_repeat.set(not self.is_repeat.get()))
        self.repeat_butt.grid(row=0, column=7)

        self.shuffle_butt = ttk.Button(self.controls_frame, text='Shuffle Play', command=lambda: self.is_random.set(not self.is_random.get()))
        self.shuffle_butt.grid(row=0, column=8)

        self.refresh_treeviews('all')


    def radio_collection_init(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        radio_select_frame = ttk.Frame(self.main_frame)
        ttk.Button(radio_select_frame, text="All Radio Stations", command=lambda: self.radio_refresh_treeviews('all')).grid(row=0, column=0)
        ttk.Button(radio_select_frame, text="All Main BBC Stations", command=lambda: self.radio_refresh_treeviews('main')).grid(row=0, column=1)
        ttk.Button(radio_select_frame, text="All BBC Stations", command=lambda: self.radio_refresh_treeviews('bbc')).grid(row=0, column=2)
        ttk.Button(radio_select_frame, text="All Custom Stations", command=lambda: self.radio_refresh_treeviews('custom')).grid(row=0, column=3)
        ttk.Button(radio_select_frame, text="Add Radio Station Url", command=self.add_radio_url).grid(row=0, column=4)
        radio_select_frame.grid(row=0, column=0, sticky='nsew')

        self.radio_station_treeview = ScrolledTreeView(self.main_frame)
        self.radio_station_treeview.grid(row=1, column=0, sticky="nsew")
        self.radio_station_treeview.heading("#0", text='Station Name')
        self.radio_station_treeview["columns"] = ("URL",)
        self.radio_station_treeview.heading("URL", text='URL')

        self.bbc_radio_stations = { # SOURCE: http://steveseear.org/high-quality-bbc-radio-streams/
            'BBC Radio 1': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1_mf_p',
			'BBC Radio 1xtra': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio1xtra_mf_p',
			'BBC Radio 2': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio2_mf_p',
			'BBC Radio 3': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio3_mf_p',
			'BBC Radio 4FM': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4fm_mf_p',
			'BBC Radio 4LW': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4lw_mf_p',
			'BBC Radio 4 Extra': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio4extra_mf_p',
			'BBC Radio 5 Live': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5live_mf_p',
			'BBC Radio 5 Live Sportsball Extra': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_radio5extra_mf_p',
			'BBC Radio 6 Music': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_6music_mf_p',
			'BBC Asian Network': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_asianet_mf_p',
			'BBC World Service UK stream': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-eieuk',
            'BBC World Service News stream': 'http://bbcwssc.ic.llnwd.net/stream/bbcwssc_mp1_ws-einws',
            'Radio Cymru': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_cymru_mf_p',
			'BBC Radio Foyle': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_foyle_mf_p',
			'BBC Radio nan Gàidheal': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_nangaidheal_mf_p',
			'BBC Radio Scotland': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_scotlandfm_mf_p',
			'BBC Radio Ulster': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_ulster_mf_p',
			'BBC Radio Wales': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_walesmw_mf_p',
			'BBC Radio Berkshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrberk_mf_p',
			'BBC Radio Bristol': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrbris_mf_p',
			'BBC Radio Cambridgeshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcambs_mf_p',
			'BBC Radio Cornwall': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcorn_mf_p',
			'BBC Coventry & Warwickshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwmcandw_mf_p',
			'BBC Radio Cumbria': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrcumbria_mf_p',
			'BBC Radio Derby': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrderby_mf_p',
			'BBC Radio Devon': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrdevon_mf_p',
			'BBC Essex': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lressex_mf_p',
			'BBC Radio Gloucestershire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrgloucs_mf_p',
			'BBC Radio Guernsey': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrguern_mf_p',
			'BBC Hereford & Worcester': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrhandw_mf_p',
			'BBC Radio Humberside': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrhumber_mf_p',
			'BBC Radio Jersey': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrjersey_mf_p',
			'BBC Radio Kent': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrkent_mf_p',
			'BBC Radio Lancashire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrlancs_mf_p',
			'BBC Radio Leeds': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrleeds_mf_p',
			'BBC Radio Leicester': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrleics_mf_p',
			'BBC Radio Lincolnshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrlincs_mf_p',
			'BBC Radio London': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrldn_mf_p',
			'BBC Radio Manchester': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrmanc_mf_p',
			'BBC Radio Merseyside': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrmersey_mf_p',
			'BBC Newcastle': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnewc_mf_p',
			'BBC Radio Norfolk': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnorfolk_mf_p',
			'BBC Radio Northampton': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnthhnts_mf_p',
			'BBC Radio Nottingham': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrnotts_mf_p',
			'BBC Radio Oxford': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lroxford_mf_p',
			'BBC Radio Sheffield': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsheff_mf_p',
			'BBC Radio Shropshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrshrops_mf_p',
			'BBC Radio Solent': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsolent_mf_p',
			'BBC Somerset': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsomer_mf_p',
			'BBC Radio Stoke': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsomer_mf_p',
			'BBC Radio Suffolk': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsuffolk_mf_p',
			'BBC Surrey': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsurrey_mf_p',
			'BBC Sussex': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrsussex_mf_p',
			'BBC Tees': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrtees_mf_p',
			'BBC Three Counties Radio': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lr3cr_mf_p',
			'BBC Wiltshire': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwilts_mf_p',
			'BBC WM 95.6': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lrwm_mf_p',
			'BBC Radio York': 'http://bbcmedia.ic.llnwd.net/stream/bbcmedia_lryork_mf_p'
        }
        self.main_bbc_radio_stations = {station: url for station, url in self.bbc_radio_stations.items() if station in ['BBC Radio 1', 'BBC Radio 2', 'BBC Radio 3', 'BBC Radio 4FM', 'BBC Radio 4LW', 'BBC Radio 6 Music']}
        self.other_bbc_radio_stations = {station: url for station, url in self.bbc_radio_stations.items() if station not in ['BBC Radio 1', 'BBC Radio 2', 'BBC Radio 3', 'BBC Radio 4FM', 'BBC Radio 4LW', 'BBC Radio 6 Music']}
        self.not_bbc_radio_stations = {station: url for station, url in self.radio_stations.items() if station not in list(self.bbc_radio_stations.keys())}
        self.radio_stations.update(self.bbc_radio_stations)

        self.radio_refresh_treeviews()
        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(3, weight=0)

        ########################################## Controls Frame ###################################################
        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        self.play_butt = ttk.Button(self.controls_frame, text="Play/Stop", command=lambda: self.radio_play_stop())
        self.play_butt.grid(row=0, column=0, sticky='nsew')

        self.controls_frame.grid_columnconfigure(5, weight=0)
        self.controls_frame.grid_columnconfigure(0, weight=1)


    def add_folder_dialog(self):
        folder = []
        def run_dialog(_None):
            open_folder_dialog = Gtk.FileChooserDialog(title="Please choose a folder", parent=None,
                        action=Gtk.FileChooserAction.SELECT_FOLDER,
                        )
            open_folder_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK)
            response = open_folder_dialog.run()
            if response == Gtk.ResponseType.OK:
                folder.append(open_folder_dialog.get_filename())
            elif response == Gtk.ResponseType.CANCEL:
                pass

            open_folder_dialog.destroy()
            Gtk.main_quit()
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT, run_dialog, None)
        Gtk.main()
        self.add_folder(folder[0])

    def add_folder(self, folder):
        for root, directories, filenames in os.walk(folder):
            filenames = [os.path.join(root, filename) for filename in filenames]
            self.import_array(filenames)

    def refresh_treeviews(self, tree='all', sort_by='Track Number'):
        def refresh_genre():
            self.genre_treeview = ScrolledTreeView(self.main_frame)
            self.genre_treeview.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            self.genre_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.genre_treeview.heading("#0", text="Genre")
            self.genre_treeview.insert('', 'end', text='All Genres')
            id = self.genre_treeview.get_children()[0] if self.genre_treeview.focus() == '' else self.genre_treeview.focus()
            self.genre_treeview.selection_set(id)
            self.genre_treeview.focus(id)
            for genre, value in sorted(self.genres.items()):
                self.genre_treeview.insert('', 'end', text=genre)
        def refresh_artist():
            self.artist_treeview = ScrolledTreeView(self.main_frame)
            self.artist_treeview.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
            self.artist_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.artist_treeview.heading("#0", text="Artist")
            self.artist_treeview.insert('', 'end', text='All Artists')
            id = self.artist_treeview.get_children()[0] if self.artist_treeview.focus() == '' else self.artist_treeview.focus()
            self.artist_treeview.selection_set(id)
            self.artist_treeview.focus(id)
            for artist, value in sorted(self.artists.items()):
                self.artist_treeview.insert('', 'end', text=artist)
        def refresh_album():
            self.album_treeview = ScrolledTreeView(self.main_frame)
            self.album_treeview.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
            self.album_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.album_treeview.heading("#0", text="Album")
            self.album_treeview.insert('', 'end', text='All Albums')
            id = self.album_treeview.get_children()[0] if self.album_treeview.focus() == '' else self.album_treeview.focus()
            self.album_treeview.selection_set(id)
            self.album_treeview.focus(id)
            for album, value in sorted(self.albums.items()):
                self.album_treeview.insert('', 'end', text=album)
        def refresh_music(sort_by):
            self.music_treeview = ScrolledTreeView(self.main_frame)
            self.music_treeview.grid(row=1, column=0, columnspan=3, sticky="nsew")
            #self.music_treeview.bind('<<TreeviewSelect>>', lambda e: self.play_song())
            self.music_treeview["columns"] = ("Title", "Genre", "Artist", "Album", "Time")

            self.music_treeview.heading("#0", text='Track', command=lambda: self.refresh_treeviews('music', sort_by='Track Number'))
            self.music_treeview.column("#0", width=20)
            for col in self.music_treeview["columns"]:
                if col == "Time":
                    self.music_treeview.column(col, width=30)
                    self.music_treeview.heading(col, text=col, command=lambda: self.refresh_treeviews('music', sort_by='Duration'))
                else:
                    self.music_treeview.heading(col, text=col, command=lambda sort_by=col: self.refresh_treeviews('music', sort_by=sort_by))

            all_songs = collections.OrderedDict()
            if self.genre_treeview.focus() == 'I001':
                for genre, value in sorted(self.genres.items()): all_songs.update(value)
            else:
                all_songs.update(self.genres[self.genre_treeview.item(self.genre_treeview.selection())['text']])
            if self.artist_treeview.focus() != 'I001':
                for title, value in sorted(all_songs.items()):
                    if value['Artist'] != self.artist_treeview.item(self.artist_treeview.selection())['text']:
                        del all_songs[title]
            if self.album_treeview.focus() != 'I001':
                for title, value in sorted(all_songs.items()):
                    if value['Album'] != self.album_treeview.item(self.album_treeview.selection())['text']:
                        del all_songs[title]
            #os.system('clear')
            #print('all_songs=', list(all_songs.items()))
            if sort_by != 'Track Number':
                sort = collections.OrderedDict(sorted(all_songs.items(), key=lambda x: x[1][sort_by]))
                if sort == self.songs: sort = collections.OrderedDict(sorted(all_songs.items(), key=lambda x: x[1][sort_by], reverse=True))
            else:
                sort = collections.OrderedDict(sorted(all_songs.items(), key=lambda x: (x[1]['Album'], float(x[1]['Disc']), float(x[1]['Track Number']))))
                if sort == self.songs: sort = collections.OrderedDict(sorted(all_songs.items(), key=lambda x: (x[1]['Album'], float(x[1]['Disc']), float(x[1]['Track Number'])), reverse=True))
            all_songs = sort
            self.songs = all_songs
            for title, song in sort.items():
                values = (song['Title'], song['Genre'], song['Artist'], song['Album'], time.strftime('%M:%S', time.gmtime(song['Duration'])))
                self.music_treeview.insert('', 'end', text="{:02d}".format(int(song['Track Number'])), values=values)


        if tree == 'all':
            refresh_genre()
            refresh_artist()
            refresh_album()
            refresh_music(sort_by)
        elif tree == 'genre':
            refresh_genre()
        elif tree == 'artist':
            refresh_artist()
        elif tree == 'album':
            refresh_album()
        elif tree == 'music':
            refresh_music(sort_by)
    def play_song(self):
        if self.music_treeview.focus()[1:] != '':
            print(list(self.songs)[int(self.music_treeview.focus()[1:], 16)-1])
            song = self.songs[list(self.songs.keys())[int(self.music_treeview.focus()[1:], 16)-1]]
            self.song_title['text'] = song['Title']
            if song != self.curr_song: self.player.set_state(Gst.State.NULL)
            self.player.set_property("uri", "file://" + os.path.realpath(song['File']))
            self.curr_song = song
        self.player.set_state(Gst.State.PLAYING)

    def play_pause(self):
        print(self.player.get_state(10).state)
        if self.is_paused.get():
            self.play_song()
            self.start_time = time.time()
            self.master.after(500, self.increase_slider)
        else:
            if self.music_treeview.focus()[1:] != '':
                if self.songs[list(self.songs.keys())[int(self.music_treeview.focus()[1:], 16)-1]] != self.curr_song:
                    self.player.set_state(Gst.State.NULL)
                    self.play_song()
                    self.increase_slider(repeat=False)
                else:
                    self.player.set_state(Gst.State.PAUSED)
            else:
                self.player.set_state(Gst.State.PAUSED)

        self.is_paused.set(not self.is_paused.get())

    def increase_slider(self, repeat=True):
        if self.player.get_state(1).state == Gst.State.PLAYING:
            status,position = self.player.query_position(Gst.Format.TIME)
            success, duration = self.player.query_duration(Gst.Format.TIME)
            percentage_passed = float(position) / Gst.SECOND * (100 / (duration / Gst.SECOND))
            self.skip_trace = True
            self.song_prog_scl_var.set(percentage_passed)
            self.song_prog_scl.update()
            self.skip_trace = False
            self.song_prog_lbl['text'] = '{0}/{1}'.format(time.strftime('%M:%S', time.gmtime(float(position) / Gst.SECOND)), time.strftime('%M:%S', time.gmtime(duration / Gst.SECOND)))
            if int(float(self.song_prog_scl_var.get())) == 100:
                self.change_song(1)
            if repeat: self.master.after(500, self.increase_slider)

    def change_song(self, change):
        self.player.set_state(Gst.State.NULL)
        if self.is_repeat.get():
            id = self.music_treeview.get_children()[int(self.music_treeview.focus()[1:], 16)-1]
        elif self.is_random.get():
            id = random.choice(self.music_treeview.get_children())
        else:
            id = self.music_treeview.get_children()[int(self.music_treeview.focus()[1:], 16)+change-1]
        self.music_treeview.selection_set(id)
        self.music_treeview.focus(id)
        self.play_pause()
        self.play_pause()

    def slider_change(self, *args):
        if not self.skip_trace:
            success, duration = self.player.query_duration(Gst.Format.TIME)
            self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, (float(self.song_prog_scl_var.get())/100)*duration)
            self.master.after(1000, self.increase_slider)

    def add_m3u_dialog(self):
        m3u = []
        def run_dialog(_None):
            open_m3u_dialog = Gtk.FileChooserDialog(title="Please choose a .m3u file", parent=None,
                        action=Gtk.FileChooserAction.OPEN,
                        )
            open_m3u_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Select", Gtk.ResponseType.OK)
            m3u_filter=Gtk.FileFilter()
            m3u_filter.set_name("M3U (*.m3u)")
            m3u_filter.add_pattern("*.[Mm][3][Uu]")
            open_m3u_dialog.add_filter(m3u_filter)
            response = open_m3u_dialog.run()
            if response == Gtk.ResponseType.OK:
                m3u.append(open_m3u_dialog.get_filename())
            elif response == Gtk.ResponseType.CANCEL:
                pass

            open_m3u_dialog.destroy()
            Gtk.main_quit()
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT, run_dialog, None)
        Gtk.main()
        self.add_m3u(m3u[0])

    def add_m3u(self, m3u):
        def createAbsolutePath(path):
        	if not os.path.isabs(path):
        		currentDir = os.path.dirname(os.path.realpath(m3u))
        		path = os.path.join(currentDir, path)

        	return path
        files = []
        with open(m3u, 'r') as f:
            for line in f:
                if os.path.isfile(createAbsolutePath(line.strip())):
                    files.append(createAbsolutePath(line.strip()))
        self.import_array(files)


    def import_array(self, arr):
        prog_win = tk.Toplevel(master=self.master)
        prog_win.title("Progress")
        prog_win.resizable(False, False)
        prog_win.wm_attributes('-type', 'splash')
        prog_win.attributes("-topmost", True)

        curr_file = tk.Label(prog_win, text="")
        curr_file.grid(sticky='nsew')
        progress = ttk.Progressbar(prog_win, orient="horizontal",
                                        length=200, mode="determinate")
        progress["maximum"] = len(arr)
        progress.grid(sticky='nsew')
        for idx, filename in enumerate(arr):
            progress["value"] = idx
            curr_file["text"] = '{filename} - ({idx}/{max})'.format(filename=os.path.basename(filename)[0:9]+'~1'+os.path.splitext(filename)[1], idx=idx, max=len(arr))
            if not any(substring in filename.casefold() for substring in ['.mp3', '.wav', '.flac', '.wma', '.mp4', '.m4a', '.ogg', '.opus']):
                continue
            audio_file = tinytag.TinyTag.get(filename, image=True)
            song = {
                'Artist': audio_file.artist,
                'Album': audio_file.album,
                'Album Artist':  audio_file.albumartist,
                'Title': audio_file.title,
                'Track Number': audio_file.track,
                'Genre':  audio_file.genre,
                'Disc': audio_file.disc,
                'Duration': audio_file.duration,
                'Image': audio_file.get_image(),
                'File': filename
                }
            title = 'Disc {0} - {1} - {2}'.format(song['Disc'], song['Track Number'], song['Title'])
            try:
                self.artists[song['Artist']][title] = song
            except KeyError:
                self.artists[song['Artist']] = {title: song}
            try:
                self.albums[song['Album']][title] = song
            except KeyError:
                self.albums[song['Album']] = {title: song}
            try:
                self.genres[song['Genre']][title] = song
            except KeyError:
                self.genres[song['Genre']] = {title: song}
            prog_win.update()
        self.refresh_treeviews()
        prog_win.destroy()

    def save_to_cache(self):
        with open('cache.txt', 'w') as f:
            f.write('artists\xa7{artists}\n'.format(artists=dict({key: dict(value) for key, value in self.artists.items()})))
            f.write('albums\xa7{albums}\n'.format(albums=dict({key: dict(value) for key, value in self.albums.items()})))
            f.write('genres\xa7{genres}\n'.format(genres=dict({key: dict(value) for key, value in self.genres.items()})))
    def open_cache(self):
        if os.path.isfile('cache.txt'):
            with open('cache.txt', 'r') as f:
                for line in f:
                    if line.strip().split('\xa7')[0] == 'artists':
                        self.artists = collections.OrderedDict({key: collections.OrderedDict(value) for key, value in ast.literal_eval(line.strip().split('\xa7')[1]).items()})
                    elif line.strip().split('\xa7')[0] == 'albums':
                        self.albums = collections.OrderedDict({key: collections.OrderedDict(value) for key, value in ast.literal_eval(line.strip().split('\xa7')[1]).items()})
                    elif line.strip().split('\xa7')[0] == 'genres':
                        self.genres = collections.OrderedDict({key: collections.OrderedDict(value) for key, value in ast.literal_eval(line.strip().split('\xa7')[1]).items()})
            self.refresh_treeviews(tree='all')

    def radio_play_stop(self):
        print(list(self.visible_stations.values())[int(self.radio_station_treeview.focus()[1:], 16)-1])

        if self.radio_station_treeview.focus()[1:] != '':
            radio_station = list(self.visible_stations.keys())[int(self.radio_station_treeview.focus()[1:], 16)-1]
            if radio_station != self.curr_radio_station:
                self.player.set_state(Gst.State.NULL)
                self.player.set_property("uri", list(self.visible_stations.values())[int(self.radio_station_treeview.focus()[1:], 16)-1])
                self.curr_radio_station = list(self.visible_stations.keys())[int(self.radio_station_treeview.focus()[1:], 16)-1]
                self.player.set_state(Gst.State.PLAYING)
            else:
                self.player.set_state(Gst.State.NULL)
        else:
            self.player.set_state(Gst.State.NULL)

    def radio_refresh_treeviews(self, stations='all'):
        self.radio_station_treeview = ScrolledTreeView(self.main_frame)
        self.radio_station_treeview.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.radio_station_treeview.heading("#0", text='Station Name')
        self.radio_station_treeview["columns"] = ("URL",)
        self.radio_station_treeview.heading("URL", text='URL')


        self.main_bbc_radio_stations = {station: url for station, url in self.bbc_radio_stations.items() if station in ['BBC Radio 1', 'BBC Radio 2', 'BBC Radio 3', 'BBC Radio 4FM', 'BBC Radio 4LW', 'BBC Radio 6 Music']}
        self.other_bbc_radio_stations = {station: url for station, url in self.bbc_radio_stations.items() if station not in ['BBC Radio 1', 'BBC Radio 2', 'BBC Radio 3', 'BBC Radio 4FM', 'BBC Radio 4LW', 'BBC Radio 6 Music']}
        self.not_bbc_radio_stations = {station: url for station, url in self.radio_stations.items() if station not in list(self.bbc_radio_stations.keys())}
        self.visible_stations = self.main_bbc_radio_stations if stations == 'main' else self.bbc_radio_stations if stations == 'bbc' else self.radio_stations if stations == 'all' else {k: v for k, v in self.radio_stations.items() if k not in self.bbc_radio_stations}


        print(list(self.radio_stations.keys()))
        for station, url in self.visible_stations.items():
            self.radio_station_treeview.insert('', 'end', text=station, values=(url,))

    def add_radio_url(self):
        def add():
            self.radio_stations.update({station_name_ent.get(): station_url_ent.get()})

        def cancel():
            add_url_win.quit()
            add_url_win.destroy()
        add_url_win = tk.Toplevel(bg='white')
        style = ttk.Style(add_url_win)
        style.configure("TLabel", background='white')
        ttk.Label(add_url_win, text='Radio Station Name: ', style='TLabel').grid(row=0, column=0)
        station_name_ent = ttk.Entry(add_url_win)
        station_name_ent.grid(row=0, column=1)
        ttk.Label(add_url_win, text='Radio Station URL: ', style='TLabel').grid(row=1, column=0)
        station_url_ent = ttk.Entry(add_url_win)
        station_url_ent.grid(row=1, column=1)
        ttk.Button(add_url_win, text='Add', command=add).grid(row=2, column=0)
        ttk.Button(add_url_win, text='Cancel').grid(row=2, column=1)

class AutoScroll(object):
    '''Configure the scrollbars for a widget.'''

    def __init__(self, master):
        #  Rozen. Added the try-except clauses so that this class
        #  could be used for scrolled entry widget for which vertical
        #  scrolling is not supported. 5/7/14.
        try:
            vsb = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        except:
            pass
        hsb = ttk.Scrollbar(master, orient='horizontal', command=self.xview)

        #self.configure(yscrollcommand=_autoscroll(vsb),
        #    xscrollcommand=_autoscroll(hsb))
        try:
            self.configure(yscrollcommand=self._autoscroll(vsb))
        except:
            pass
        self.configure(xscrollcommand=self._autoscroll(hsb))

        self.grid(column=0, row=0, sticky='nsew')
        try:
            vsb.grid(column=1, row=0, sticky='ns')
        except:
            pass
        hsb.grid(column=0, row=1, sticky='ew')

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Copy geometry methods of master  (taken from Scrolledtext.py)
        if sys.version_info >= (3, 0):
            methods = tk.Pack.__dict__.keys() | tk.Grid.__dict__.keys() \
                  | tk.Place.__dict__.keys()
        else:
            methods = tk.Pack.__dict__.keys() + tk.Grid.__dict__.keys() \
                  + tk.Place.__dict__.keys()

        for meth in methods:
            if meth[0] != '_' and meth not in ('config', 'configure'):
                setattr(self, meth, getattr(master, meth))

    @staticmethod
    def _autoscroll(sbar):
        '''Hide and show scrollbar as needed.'''
        def wrapped(first, last):
            first, last = float(first), float(last)
            if first <= 0 and last >= 1:
                sbar.grid_remove()
            else:
                sbar.grid()
            sbar.set(first, last)
        return wrapped

    def __str__(self):
        return str(self.master)

def _create_container(func):
    '''Creates a ttk Frame with a given master, and use this new frame to
    place the scrollbars and the widget.'''
    def wrapped(cls, master, **kw):
        container = ttk.Frame(master)
        container.bind('<Enter>', lambda e: _bound_to_mousewheel(e, container))
        container.bind('<Leave>', lambda e: _unbound_to_mousewheel(e, container))
        return func(cls, container, **kw)
    return wrapped

class ScrolledListBox(AutoScroll, tk.Listbox):
    '''A standard Tkinter text widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        tk.Listbox.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)

class ScrolledTreeView(AutoScroll, ttk.Treeview):
    '''A standard ttk Treeview widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        ttk.Treeview.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)

def _bound_to_mousewheel(event, widget):
    child = widget.winfo_children()[0]
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        child.bind_all('<MouseWheel>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Shift-MouseWheel>', lambda e: _on_shiftmouse(e, child))
    else:
        child.bind_all('<Button-4>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Button-5>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Shift-Button-4>', lambda e: _on_shiftmouse(e, child))
        child.bind_all('<Shift-Button-5>', lambda e: _on_shiftmouse(e, child))

def _unbound_to_mousewheel(event, widget):
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        widget.unbind_all('<MouseWheel>')
        widget.unbind_all('<Shift-MouseWheel>')
    else:
        widget.unbind_all('<Button-4>')
        widget.unbind_all('<Button-5>')
        widget.unbind_all('<Shift-Button-4>')
        widget.unbind_all('<Shift-Button-5>')

def _on_mousewheel(event, widget):
    if platform.system() == 'Windows':
        widget.yview_scroll(-1*int(event.delta/120),'units')
    elif platform.system() == 'Darwin':
        widget.yview_scroll(-1*int(event.delta),'units')
    else:
        if event.num == 4:
            widget.yview_scroll(-1, 'units')
        elif event.num == 5:
            widget.yview_scroll(1, 'units')

def _on_shiftmouse(event, widget):
    if platform.system() == 'Windows':
        widget.xview_scroll(-1*int(event.delta/120), 'units')
    elif platform.system() == 'Darwin':
        widget.xview_scroll(-1*int(event.delta), 'units')
    else:
        if event.num == 4:
            widget.xview_scroll(-1, 'units')
        elif event.num == 5:
            widget.xview_scroll(1, 'units')

def main():
    if 'ttkthemes' in sys.modules:
        root = ttkthemes.ThemedTk()
        music_player_gui = music_player(root)
        root.set_theme("plastik")
        root.mainloop()
    else:
        root = tk.Tk()
        music_player_gui = music_player(root)
        root.mainloop()

if __name__ == '__main__':
    main()
