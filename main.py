try:
    import tkinter as tk
    import tkinter.ttk as ttk
except:
    import Tkinter as tk
    import ttk

import Pmw
import platform
import sys
import os
import time
import tinytag
import collections
import random
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gst


class music_player:
    def __init__(self, master):
        self.master = master
        self.master.geometry('1432x764')

        self.menubar = tk.Menu(self.master)
        self.master.configure(menu=self.menubar)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Add Folder", command=self.add_folder_dialog)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.sidemenubar_frame = Pmw.ScrolledFrame(self.master, usehullsize=1, hull_width=250)
        self.sidemenubar_frame.grid(row=0, column=0, rowspan=2, sticky="ns")

        self.genre_treeview = ScrolledTreeView(self.master)
        self.genre_treeview.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.genre_treeview.heading("#0", text="Genre")

        self.artist_treeview = ScrolledTreeView(self.master)
        self.artist_treeview.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.artist_treeview.heading("#0", text="Artist")

        self.album_treeview = ScrolledTreeView(self.master)
        self.album_treeview.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
        self.album_treeview.heading("#0", text="Album")

        self.music_treeview = ScrolledTreeView(self.master)
        self.music_treeview.grid(row=1, column=1, columnspan=3, sticky="nsew")
        self.music_treeview["columns"] = ("Title", "Genre", "Artist", "Album", "Time")
        self.music_treeview.heading("#0", text='Track', command=lambda: self.refresh_treeviews('music', sort_by='Track Number'))
        self.music_treeview.column("#0", width=20)
        for col in self.music_treeview["columns"]:
            if col == "Time":
                self.music_treeview.column(col, width=30)
                self.music_treeview.heading(col, text=col, command=lambda: self.refresh_treeviews('music', sort_by='Duration'))
            else:
                self.music_treeview.heading(col, text=col, command=lambda sort_by=col: self.refresh_treeviews('music', sort_by=sort_by))

        self.controls_frame = tk.Frame(self.master)
        self.controls_frame.grid(row=2, column=0, columnspan=4, sticky="nsew")

        self.previous_track = tk.Button(self.controls_frame, text="Previous Track", command=lambda: self.change_song(-1))
        self.previous_track.grid(row=0, column=0)

        self.play_butt = tk.Button(self.controls_frame, text="Play/Pause", command=lambda: self.play_pause())
        self.play_butt.grid(row=0, column=1)

        self.next_track = tk.Button(self.controls_frame, text="Next Track", command=lambda: self.change_song(1))
        self.next_track.grid(row=0, column=2)

        self.album_icon = tk.Label(self.controls_frame)
        self.album_icon.grid(row=0, column=3)

        self.song_title = tk.Label(self.controls_frame)
        self.song_title.grid(row=0, column=4)

        self.song_prog_scl = ttk.Scale(self.controls_frame, from_=0, to=100, orient='horizontal')
        self.song_prog_scl.grid(row=0, column=5, sticky='ew')
        self.controls_frame.grid_columnconfigure(5, weight=1)

        self.song_prog_lbl = tk.Label(self.controls_frame)
        self.song_prog_lbl.grid(row=0, column=6)

        self.repeat_butt = tk.Button(self.controls_frame, text='Repeat', command=lambda: self.is_repeat.set(not self.is_repeat.get()))
        self.repeat_butt.grid(row=0, column=7)

        self.shuffle_butt = tk.Button(self.controls_frame, text='Shuffle Play', command=lambda: self.is_random.set(not self.is_random.get()))
        self.shuffle_butt.grid(row=0, column=8)

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_columnconfigure(2, weight=1)
        self.master.grid_columnconfigure(3, weight=1)

        self.artists = {}
        self.albums = {}
        self.genres = {}

        self.genre_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        self.artist_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        self.album_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
        #self.music_treeview.bind('<<TreeviewSelect>>', lambda e: self.play_song())
        self.master.bind('f5', lambda e: self.refresh_treeviews('music'))

        self.songs = collections.OrderedDict()

        Gst.init()
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        #self.player.connect("about-to-finish",  lambda: print('CHANGE SONG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'))
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message)

        self.is_paused = tk.BooleanVar()
        self.is_paused.set(True)
        self.is_random = tk.BooleanVar()
        self.is_random.set(False)
        self.is_repeat = tk.BooleanVar()
        self.is_repeat.set(False)

        self.curr_song = None

    def add_folder_dialog(self):
        folder = []
        def run_dialog(_None):
            open_folder_dialog = Gtk.FileChooserDialog("Please choose a folder", None,
                        Gtk.FileChooserAction.SELECT_FOLDER,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                        "Select", Gtk.ResponseType.OK))
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
            for filename in filenames:
                if not any(substring in filename.casefold() for substring in ['.mp3', '.wav', '.flac', '.wma', '.mp4', '.m4a', '.ogg', '.opus']):
                    continue
                audio_file = tinytag.TinyTag.get(os.path.join(root, filename), image=True)
                song = collections.OrderedDict({
                    'Artist': audio_file.artist,
                    'Album': audio_file.album,
                    'Album Artist':  audio_file.albumartist,
                    'Title': audio_file.title,
                    'Track Number': audio_file.track,
                    'Genre':  audio_file.genre,
                    'Disc': audio_file.disc,
                    'Duration': audio_file.duration,
                    'Image': audio_file.get_image(),
                    'File': os.path.join(root, filename)
                    })
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

        self.refresh_treeviews()

    def refresh_treeviews(self, tree='all', sort_by='Track Number'):
        def refresh_genre():
            self.genre_treeview = ScrolledTreeView(self.master)
            self.genre_treeview.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
            self.genre_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.genre_treeview.heading("#0", text="Genre")
            self.genre_treeview.insert('', 'end', text='All Genres')
            id = self.genre_treeview.get_children()[0] if self.genre_treeview.focus() == '' else self.genre_treeview.focus()
            self.genre_treeview.selection_set(id)
            self.genre_treeview.focus(id)
            for genre, value in sorted(self.genres.items()):
                self.genre_treeview.insert('', 'end', text=genre)
        def refresh_artist():
            self.artist_treeview = ScrolledTreeView(self.master)
            self.artist_treeview.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
            self.artist_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.artist_treeview.heading("#0", text="Artist")
            self.artist_treeview.insert('', 'end', text='All Artists')
            id = self.artist_treeview.get_children()[0] if self.artist_treeview.focus() == '' else self.artist_treeview.focus()
            self.artist_treeview.selection_set(id)
            self.artist_treeview.focus(id)
            for artist, value in sorted(self.artists.items()):
                self.artist_treeview.insert('', 'end', text=artist)
        def refresh_album():
            self.album_treeview = ScrolledTreeView(self.master)
            self.album_treeview.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")
            self.album_treeview.bind('<<TreeviewSelect>>', lambda e: self.refresh_treeviews('music'))
            self.album_treeview.heading("#0", text="Album")
            self.album_treeview.insert('', 'end', text='All Albums')
            id = self.album_treeview.get_children()[0] if self.album_treeview.focus() == '' else self.album_treeview.focus()
            self.album_treeview.selection_set(id)
            self.album_treeview.focus(id)
            for album, value in sorted(self.albums.items()):
                self.album_treeview.insert('', 'end', text=album)
        def refresh_music(sort_by):
            self.music_treeview = ScrolledTreeView(self.master)
            self.music_treeview.grid(row=1, column=1, columnspan=3, sticky="nsew")
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
        print(list(self.songs)[int(self.music_treeview.focus()[1:], 16)])
        song = self.songs[list(self.songs.keys())[int(self.music_treeview.focus()[1:], 16)-1]]
        self.song_title['text'] = song['Title']
        if song != self.curr_song: self.player.set_state(Gst.State.NULL)
        self.player.set_property("uri", "file://" + os.path.realpath(song['File']))
        self.player.set_state(Gst.State.PLAYING)
        self.curr_song = song

    def play_pause(self):
        print(self.player.get_state(10).state)
        if self.is_paused.get():
            self.play_song()
            self.start_time = time.time()
            self.master.after(500, self.increase_slider)
        else:
            self.player.set_state(Gst.State.PAUSED)

        self.is_paused.set(not self.is_paused.get())

    def increase_slider(self):
        print(Gst.State.PLAYING, self.player.get_state(1).state)
        print(self.player.get_state(1))
        self.bus.peek()
        if self.player.get_state(1).state == Gst.State.PLAYING:
            self.time_passed = time.time()- self.start_time
            percentage_passed = (self.time_passed / self.curr_song['Duration'])*100
            self.song_prog_scl.set(percentage_passed)
            self.song_prog_scl.update()
            self.master.after(500, self.increase_slider)

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

    def on_message(self, bus, message):
        print(message)
        if message.type == Gst.Message.EOS:
            self.change_song(1)
        elif message.type == Gst.Message.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: {0}, {1}".format(err, debug))

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
    root = tk.Tk()
    music_player_gui = music_player(root)
    root.mainloop()

if __name__ == '__main__':
    main()
