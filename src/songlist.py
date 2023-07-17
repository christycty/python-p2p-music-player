import tkinter as tk
import tkinter.messagebox
import customtkinter
import threading

import numpy as np
import simpleaudio as sa
import pyaudio
import wave
import re
import pandas as pd

from os import listdir
from os.path import isfile, join
from PIL import Image

from edit_file import DeleteWindow, EditWindow

# the list itself is the songlist frame
''' 
todo
1. add dataframe/whatever storage for database (with song file, author, etc info)
- add a column to store if it is local or nonlocal file
2. change search function (to search on other attributes (author, lyrics) too)
3. display author (or artist) on song list
4. (minor) remove the file extension from song name display
5. do edit and delete functions if possible
'''
class Songlist(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master

        # grid configuration
        self.grid(row=2, column=1, padx=(20,20), pady=(0,20), sticky="nsew")
        
        self.grid_columnconfigure(0, weight=15)     # song name
        self.grid_columnconfigure(1, weight=10)     # artist
        self.grid_columnconfigure(2, weight=10)     # album
        self.grid_columnconfigure(3, weight=1)      # play button
        self.grid_columnconfigure(4, weight=1)      # edit button
        self.grid_columnconfigure(5, weight=1)      # delete button

        
        # display songs and controls (regenerate at every edit, delete, search operation)
        # list of index of songs to display
        self.songlist_display_index = range(self.master.songlist_song_count)

        # list storing current display elements
        self.songlist_elements = []  # list of lists (songname, artist, album, play, edit, delete)
        self.display_songs()

        self.delete_window = None
        self.edit_window = None
    

    def add_song(self, i, song_id):
        song = self.master.songlist_songs.loc[song_id]

        # print(f"add song {song_id} songname {song['song_name']}")
        # file name label
        label = customtkinter.CTkTextbox(master=self,
                                             height=45,
                                             fg_color="transparent")
        #label = customtkinter.CTkLabel(master=self, text=songname, font=customtkinter.CTkFont(size=14))
        label.grid(row=i, column=0, padx=0, pady=(0,0), sticky="nw")

        if self.master.songlist_songs.loc[song_id]["local"]:
            symbol = "💻 "  
        else:
            symbol = "☁︎"
        # print(f'{symbol + song["song_name"]}||{symbol}||{song["song_name"]}')
        label.insert("0.%d" % i, symbol + song["song_name"])
        label.configure(state="disabled")

        # artist label
        label_artist = customtkinter.CTkTextbox(master=self,
                                             height=45,
                                             fg_color="transparent")
        label_artist.grid(row=i, column=1, padx=0, pady=(0,0), sticky="ne")
        label_artist.insert("0.%d" % i, song["artist"])
        label_artist.configure(state="disabled")

        # album label
        label_album = customtkinter.CTkTextbox(master=self,
                                             height=45,
                                             fg_color="transparent")
        label_album.grid(row=i, column=2, padx=0, pady=(0,0), sticky="ne")
        label_album.insert("0.%d" % i, song["album"])
        label_album.configure(state="disabled")

        # play button
        play_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/play.png"), size=(25,25))
        play_button = customtkinter.CTkButton(master=self, 
                                                width=30,
                                                height=30,
                                                border_width=0,
                                                corner_radius=0,
                                                fg_color="transparent",
                                                text="",
                                                image=play_button_img)
        play_button.grid(row=i, column=3, padx=0, pady=(0, 10), sticky="e")
        play_button.configure(command=lambda : self.play_song_button_click(song_id))

        if self.master.songlist_songs.loc[song_id]["local"] == True:
            # edit button (need fix functionality)
            edit_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/edit.png"), size=(30,30))
            edit_button = customtkinter.CTkButton(master=self, 
                                                    width=30,
                                                    height=30,
                                                    border_width=0,
                                                    corner_radius=0,
                                                    fg_color="transparent",
                                                    text="",
                                                    image=edit_button_img)
            edit_button.grid(row=i, column=4, padx=0, pady=(0, 10), sticky="e")
            edit_button.configure(command=lambda : self.edit_songinfo(song_id))

            # delete button (need fix functionality)
            delete_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/delete.png"), size=(30,30))
            delete_button = customtkinter.CTkButton(master=self, 
                                                    width=30,
                                                    height=30,
                                                    border_width=0,
                                                    corner_radius=0,
                                                    fg_color="transparent",
                                                    text="",
                                                    image=delete_button_img)
            delete_button.grid(row=i, column=5, padx=0, pady=(0, 10), sticky="e")
            delete_button.configure(command=lambda : self.delete_song_button_click(song_id))

            self.songlist_elements.append([label, label_artist, label_album, play_button, edit_button, delete_button])
        else:
            self.songlist_elements.append([label, label_artist, label_album, play_button])


    # display songs on menu
    def display_songs(self):
        # remove all original elements
        for song_element in self.songlist_elements:
            for element in song_element:
                element.destroy()

        self.songlist_elements = []

        # add new elements
        for row, i in enumerate(self.songlist_display_index):
            self.add_song(row, i)

    
    def play_song_button_click(self, song_id):
        self.master.current_song = song_id
        self.master.player.play_song(0, "play")

    def edit_songinfo(self, song_id):
        if self.edit_window == None or not self.edit_window.winfo_exists():
            self.edit_window = EditWindow(self, song_id)

        print("edited song:", self.master.songlist_songs.loc[song_id]["song_name"])
        self.master.fetch_songs()
        

    def delete_song_button_click(self, song_id):
        if self.delete_window == None or not self.delete_window.winfo_exists():
            self.delete_window = DeleteWindow(self, song_id)
        
        self.delete_window.focus()
    
    def delete_song(self, song_id):
        if song_id == self.master.current_song:
            self.master.player.nextsong_button_click()

        print("deleted song:", self.master.songlist_songs.loc[song_id]["song_name"])
        self.master.fetch_songs()
        
