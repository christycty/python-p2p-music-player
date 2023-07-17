import tkinter as tk
import tkinter.messagebox
import customtkinter
import threading

import numpy as np
import simpleaudio as sa
import pyaudio
import wave
import re

from os import listdir
from os.path import isfile, join
from PIL import Image

class Searcher(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.master = master
        # UI design
        self.grid(row=1, column=1, padx=(20,20), pady=(20,0), sticky="new")
        self.grid_columnconfigure(1, weight=10)  # insert
        self.grid_columnconfigure(2, weight=1)   # search button
        self.grid_rowconfigure(1, weight=1) 
        
        # place search bar
        self.searchbar = customtkinter.CTkEntry(master=self,
                                                placeholder_text="Search song by Song Name, Artist, or Album")
        self.searchbar.grid(row=1, column=1, padx=(10,0), pady=10, sticky="ew")

        # search button
        search_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/search.png"), size=(30,30))
        self.search_button = customtkinter.CTkButton(master=self, 
                                                width=30,
                                                height=30,
                                                border_width=0,
                                                corner_radius=0,
                                                fg_color="transparent",
                                                text="",
                                                command=self.search_song, 
                                                image=search_button_img)
        self.search_button.grid(row=1, column=2, padx=0, pady=(0, 0), sticky="we")

    def search_song(self):
        search_text = self.searchbar.get()
        
        result_index = []
        match_string = f".*{search_text}"
        p = re.compile(match_string, re.IGNORECASE)

        for i in range(self.master.songlist_song_count):
            songname = self.master.songlist_songs.loc[i].at["song_name"]
            artist = self.master.songlist_songs.loc[i].at["artist"]
            album = self.master.songlist_songs.loc[i].at["album"]
            
            if p.match(songname) or p.match(artist) or p.match(album):
                result_index.append(i)
        # print("searching for", search_text, "result", result_index)
        self.master.songlist.songlist_display_index = result_index
        # refresh song list
        self.master.songlist.display_songs()