import tkinter as tk
import tkinter.messagebox
import customtkinter
import threading
import subprocess

import numpy as np
import simpleaudio as sa
import pyaudio
import wave
import re
import pandas as pd
import os 
import psutil
from distutils.dir_util import copy_tree
from parse import *
import requests

import os
from os import listdir, mkdir
from os.path import isfile, join, exists
from PIL import Image, ImageTk
import time

from searcher import Searcher
from player import Player
from songlist import Songlist
#from p2p_ import P2P

customtkinter.set_appearance_mode("dark") 
# customtkinter.set_default_color_theme("./ref/dark-blue.json") 

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.current_song = 0  # id of song in songlist
        self.current_song_length = 0

        # handle failed stream termination
        self.retry_start_second = 0
        self.retry_play_song = False
        self.retry_state = "play"
        # self.stop_song_event = threading.Event()

        self.songs_directory = "./songs/"
        self.lyrics_directory = "./lyrics/"

        # gui stuff 
        self.grid_columnconfigure(1, weight=5)  # menu
        self.grid_columnconfigure(2, weight=2)  # player
        self.grid_rowconfigure(1, weight=1)     # menu: searcher
        self.grid_rowconfigure(2, weight=10)    # menu: song list    

        self.current_ui = []
        self.theme_count = 0
        self.theme_id = 0
        self.theme_name = "dark"

        ####### server setup #######
        self.IP_list = []
        self.PORT = 8000

        self.song_folder = 'songs'
        self.lyrics_folder = 'lyrics'

        ###### Songlist ######
        # list of all songs (only altered by edit/delete)
        self.songlist = None

        # songname, artist, album, local, nonlocal
        self.songlist_songs = None    
        self.songlist_song_count = None

        self.fetch_songs()

        self.player = None
        self.searcher = None
        self.songlist = None 

        ###### Set Theme ######
        # default theme is dark
        self.set_theme(0)

        # start playing song
        self.player.play_song(0, "pause")

    def load_themes(self):
        self.themes = pd.read_csv("./themes.csv")
        self.theme_count = len(self.themes.index)   

    def get_theme_image(self, img_name):
        folder = "themes/" + self.themes.loc[self.theme_id]["theme_name"]
        path = folder + "/" + img_name + ".png"
        img = Image.open(path)
        return img

    def set_theme(self, theme_index):
        # continue playing song after
        retry_playsong = False 
 
        if self.player != None:
            retry_playsong = True

            # get current song second from progress text
            cur_time = self.player.progress.cget("text")
            parsed_time = parse("{}:{}/{}:{}", cur_time)
            self.retry_start_second = int(parsed_time[0]) * 60 + int(parsed_time[1])

            self.retry_state = self.play_state

        # get all theme names and colors from themes.csv
        self.load_themes()

        # load selected theme
        self.theme_id = theme_index
        theme = self.themes.loc[self.theme_id]
        print(f"loading theme {theme['theme_name']}... ", end="")

        elements = ["window_colour","frame_colour","text_colour","text_hidden_colour","border_colour","control_hover","control_normal","entry_colour"]

        # setup color scheme json file
        with open(r'./themes/template.json', 'r') as file:
            data = file.read()

            for element in elements:
                search_text = element
                replace_text = str(theme.loc[element])
                data = data.replace(search_text, replace_text)
        
        self.theme_name = theme.loc["theme_name"]
        
        # the theme directory is empty
        theme_path = f'./themes/{self.theme_name}'
        if not exists(theme_path):
            src_folder = f"./themes/{theme['mode']}"
            copy_tree(src_folder, theme_path)

            print(f"Theme directory not found, using default {theme['mode']} icons")

        theme_json_path = f'./themes/{self.theme_name}/{self.theme_name}.json'
        with open(theme_json_path, 'w+') as file:
            file.write(data)
        
        mode = theme.loc["mode"]

        customtkinter.set_appearance_mode(mode) 
        customtkinter.set_default_color_theme(theme_json_path) 
        
        self.reset_current_ui()

        if retry_playsong:
            self.retry_play_song = True

        self.parse_gif()
        print("theme updated!")

    def parse_gif(self):
        gif_path = f'./themes/{self.theme_name}/player.gif'
        image_object = Image.open(gif_path)

        gif_dir_path = f'./themes/{self.theme_name}/gif/'
        if not exists(gif_dir_path):
            mkdir(gif_dir_path)
        for frame in range(0, image_object.n_frames):
            image_object.seek(frame)
            #frame_img_path = gif_dir_path + 'frame' + str(frame) + '.bmp'
            #image_object.save(frame_img_path)

            self.player.gif_list.append(image_object.copy())

    def reset_current_ui(self):
        for widget in self.current_ui:
            widget.destroy()
        self.player = Player(self)
        self.current_ui.append(self.player)

        self.searcher = Searcher(self)
        self.current_ui.append(self.searcher)

        self.songlist = Songlist(self)
        self.current_ui.append(self.songlist)


    def fetch_songs(self):
        # check if a local path is invalid
        def check_local_path(path, dir):
            if path == "None":
                return False 
            return os.path.exists(dir + path)
        
        def check_nonlocal_path(path, dir, ip):
            request_url = f"http://{ip}:{self.PORT}/{dir}/{path}"
            try:
                request = requests.get(request_url)
            except:
                return False

            if request.status_code != 200:
                return False
            return True

        self.songlist_songs = pd.DataFrame(columns=["song_name", "artist", "album", "local", "nonlocal"])
        songname_list = []  # has song appeared

        # load local songs
        self.songlist_local_songs_path = dict()
        self.songlist_local_lyrics_path = dict()

        local_df = pd.read_csv("./database.csv").fillna("None")

        for index, row in local_df.iterrows():
            songlist_row = [row["song_name"], row["artist"], row["album"], True, False]

            # if song path is invalid, skip song
            if not check_local_path(row["song_path"], self.songs_directory):
                print(f"invalid path {row['song_path']} for song {row['song_name']}")
                continue
            
            songname_list.append(row["song_name"])
            self.songlist_songs.loc[len(self.songlist_songs)] = songlist_row

            self.songlist_local_songs_path[row["song_name"]] = self.songs_directory + row["song_path"]

            # no lyrics path provided
            if check_local_path(row["lyrics_path"], self.lyrics_directory):
                self.songlist_local_lyrics_path[row["song_name"]] = self.lyrics_directory + row["lyrics_path"]
            else:
                self.songlist_local_lyrics_path[row["song_name"]] = None


        self.songlist_nonlocal_songs_url = dict()
        self.songlist_nonlocal_lyrics_url = dict()

        # load online songs
        if self.IP_list:
            for index, IP in enumerate(self.IP_list):
                csv_path = f"./database{index+2}.csv"
                df = pd.read_csv(csv_path).fillna("None")

                for index, row in df.iterrows():
                    songname = row["song_name"]

                    song_url = f"http://{IP}:{self.PORT}/{self.song_folder}/{row['song_path']}"
                    lyrics_url = f"http://{IP}:{self.PORT}/{self.lyrics_folder}/{row['lyrics_path']}"
                    
                    # new song name
                    if songname not in songname_list:
                        # add song info
                        songlist_row = [row["song_name"], row["artist"], row["album"], False, True]

                        # if song path is invalid, skip song
                        if not check_nonlocal_path(row["song_path"], self.song_folder, IP):
                            continue

                        if check_nonlocal_path(row["lyrics_path"], self.lyrics_folder, IP):
                            self.songlist_nonlocal_lyrics_url[songname] = [lyrics_url]
                        else:
                            self.songlist_nonlocal_lyrics_url[songname] = []

                        songname_list.append(songname)
                        self.songlist_songs.loc[len(self.songlist_songs)] = songlist_row

                    else:
                        # locate row containing song
                        id = self.songlist_songs.index[self.songlist_songs['song_name'] == songname].tolist()[0]
                        self.songlist_songs.loc[id, "nonlocal"] = True

                        if check_nonlocal_path(row["lyrics_path"], self.lyrics_folder, IP):
                            if songname not in self.songlist_nonlocal_lyrics_url:
                                self.songlist_nonlocal_lyrics_url[songname] = [lyrics_url]
                            else:
                                self.songlist_nonlocal_lyrics_url[songname].append(lyrics_url)

                    # add song_url
                    if songname in self.songlist_nonlocal_songs_url:
                        self.songlist_nonlocal_songs_url[songname].append(song_url)
                    else:
                        self.songlist_nonlocal_songs_url[songname] = [song_url]


        self.songlist_song_count = len(self.songlist_songs.index)

        # print(self.songlist_nonlocal_songs_url)
        # print(self.songlist_nonlocal_lyrics_url)
        print(f"{self.songlist_song_count} songs loaded")


    def display_songs(song_index):
        self.songlist.display_songs(song_index)


def center_window(app_width, app_height):
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = (screen_width/2) - (app_width/2)
    y = (screen_height/2) - (app_height/2)

    app.geometry('%dx%d+%d+%d' % (app_width, app_height, x, y))

if __name__ == "__main__":
    print("hello, welcome to P2P music player :)")

    wd = os.getcwd()
    # p = subprocess.Popen('start python -m http.server', stdout=subprocess.PIPE,shell=True, cwd=wd)
    p = subprocess.Popen(['python','-m', 'http.server'], stdout=subprocess.PIPE,cwd=wd)
    p_pid = p.pid
    # p_name = p.command 
    print(f"local server (pid: {p_pid}) started for file sharing")

    app = App()
    app.title("WAV Music Player")
    center_window(1100, 580)

    # event listener during loop
    def check_stream():
        # print(f"check {app.current_song}")
        if app.retry_play_song:
            # print("retry stream")
            app.player.play_song(app.retry_start_second, app.retry_state)
            
        app.after(100, check_stream)

    app.after(100, check_stream)

    def handle_close():
        print("thanks for using the player, have a nice day :)")
        # clear temp database files
        ip_count = len(app.IP_list)
        for i in range(ip_count):
            os.remove(f"database{i+2}.csv")

        # clear temp files
        try:
            os.remove("cur_song.srt")
        except:
            pass 

        try:
            os.rmdir("src/__pychache__")
        except:
            pass 

        try:
            os.remove("1-2.bmp")
        except:
            pass 

        # destroy window
        app.destroy()

        # kill the server subprocess and all of its children
        def kills(pid):
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()

        kills(p.pid)

    app.protocol("WM_DELETE_WINDOW", handle_close)
    app.mainloop()