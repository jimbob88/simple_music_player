# simple_music_player
A Simple Tkinter Music Player for Ubuntu based off [Rhythmbox](https://github.com/GNOME/rhythmbox "Rhythmbox's Home Page")

The idea of this program was less of making a usable music player and more a test of what I could build with Tkinter (Built as a test for what I could make a GUI do), hence the lack of some features, ~like continual playing of music via playlists~, ~and also lack of support for opening windows playlists~, I may add these features later down the line.

Setup:
```
python3 -m pip install tinytag
python3 -m pip install pygobject
```

#### Why have Gtk?

From personal experience Ubuntu's/Linux's file browser built into Tkinter is hell to use, without proper options, but Gtk's seems to work rather well, I personally had the requirement of opening a NAS drive which would require me traversing to a directory like: `/run/user/1000/gvfs/smb-share:server=*******,share=music`, which would take a while using the built in Tkinter file browser
