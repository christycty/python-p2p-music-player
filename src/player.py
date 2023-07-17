import tkinter as tk
import tkinter.messagebox
import customtkinter
import threading
import requests

import numpy as np
import simpleaudio as sa
import pyaudio
import wave
import re
from parse import *
import time
import pysrt

import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib import collections as mc
import colorsys

from os import listdir
from os.path import isfile, join
from PIL import Image

from edit_file import P2PWindow

class Player(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # load current music file
        # 3 states: stop (no stream), pause (paused stream), play (ongoing stream)
        self.master.play_state = "stop"
        self.master = master

        # p2p stuff
        self.p2p_setup_window = None
        self.song_switch = 0
        self.lyric_switch = 0
        self.server_count = 0
        self.stream_type = "local"  # online or local

        # UI design

        self.grid(row=1, column=2, padx=(20,20), pady=(20,20), sticky="nesw", rowspan=2)
        
        self.grid_rowconfigure(1, weight=8)   # graphics visualization
        self.grid_rowconfigure(2, weight=1)    # song name
        self.grid_rowconfigure(3, weight=1)    # artist
        self.grid_rowconfigure(4, weight=5)   # lyrics
        self.grid_rowconfigure(5, weight=1)   # progress bar
        self.grid_rowconfigure(6, weight=2)    # control buttons
        self.grid_rowconfigure(7, weight=1)    # volume control

        self.grid_columnconfigure(0, weight=10)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=10)

        # add widgets to player
        self.theme_options = []
        for i in range(self.master.theme_count):
            name = self.master.themes.loc[i]["theme_name"]
            self.theme_options.append(name)
        self.theme_menu = customtkinter.CTkOptionMenu(master=self,
                                                      values=self.theme_options,
                                                      command=self.theme_option_click)
        self.theme_menu.grid(row=1, column=2, padx=(0,10), pady=(10,0), sticky="ne")
        self.theme_menu.set(self.theme_options[self.master.theme_id])


        p2p_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/cloud.png"), size=(35,35))
        self.p2p_button = customtkinter.CTkButton(master=self, 
                                                width=35,
                                                height=3,
                                                border_width=0,
                                                corner_radius=0,
                                                fg_color="transparent",
                                                text="",
                                                image=p2p_button_img)
        
        self.p2p_button.grid(row=1, column=0, padx=(5,0), pady=(5,0), sticky="nw")
        self.p2p_button.configure(command=lambda: self.p2p_button_click())


        graphics_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/player.jpg"), size=(144,144))
        self.graphics = customtkinter.CTkButton(master=self, 
                                                   width=4,
                                                   height=5,
                                                   border_width=5,
                                                   #border_color="black",
                                                   corner_radius=0,
                                                   fg_color="transparent",
                                                   text="",
                                                   state="disabled",
                                                   image=graphics_img)
        self.graphics.grid(row=1, column=0, padx=10, pady=10, sticky="s", columnspan=3)

        self.gif_list = []
        self.song_name = customtkinter.CTkLabel(self, text="", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.song_name.grid(row=2, column=0, padx=10, pady=(0,0), sticky="ews", columnspan=3)

        self.artist = customtkinter.CTkLabel(self, text="", font=customtkinter.CTkFont(size=12, weight="normal"))
        self.artist.grid(row=3, column=0, padx=10, pady=(0,0), sticky="ews", columnspan=3)                
        
        # lyrics UI
        self.lyrics_frame = customtkinter.CTkFrame(self, height=120, fg_color="transparent")
        self.lyrics_frame.grid(row=4, column=0, padx=5, pady=5, sticky="", columnspan=3, rowspan=1)

        self.lyrics = customtkinter.CTkLabel(self.lyrics_frame, text="", font=customtkinter.CTkFont(size=14, weight="bold"))
        self.lyrics.configure(wraplength = 280)
        self.lyrics.grid(row=0, column=0, padx=0, pady=0, sticky="", columnspan=1)

        # progress bar
        self.progressbar = customtkinter.CTkSlider(master=self,
                                                   width=200,
                                                   number_of_steps=200)         # approx. song length (second)
                                                   #fg_color="gray",
                                                   #progress_color="light gray")
                                                   # command=self.progress_slider)
        self.progressbar.grid(row=5, column=0, padx=(10,0), pady=0, sticky="e", columnspan=2)
        # bind with mouse left button up
        self.progressbar.bind("<ButtonRelease-1>", self.progress_slider)  
        # bind with mouse left button down
        self.progressbar.bind("<ButtonPress-1>", self.progress_slider_pressing)
        self.progress_bar_down = False
        self.progressbar.set(0)

        self.progress_text = "00:00/00:00"
        self.progress = customtkinter.CTkLabel(self, text=self.progress_text, font=customtkinter.CTkFont(size=12))
        self.progress.grid(row=5, column=2, padx=(30,30), pady=0, sticky="ws")

        # function buttons
        self.play_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/play.png"), size=(30,30))
        self.pause_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/pause.png"), size=(30,30))
        self.play_button = customtkinter.CTkButton(master=self, 
                                                   width=30,
                                                   height=30,
                                                   border_width=0,
                                                   corner_radius=0,
                                                   fg_color="transparent",
                                                   text="",
                                                   command=self.play_button_click,
                                                   image=self.play_button_img)
        self.play_button.grid(row=6, column=1, padx=10, pady=(0,10), sticky="s")

        prevsong_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/prevsong.png"), size=(30,30))
        self.prevsong_button = customtkinter.CTkButton(master=self,
                                                       width=75,
                                                       height=30,
                                                       border_width=0,
                                                       corner_radius=0,
                                                       fg_color="transparent",
                                                       text="",
                                                       command=self.prevsong_button_click, 
                                                       image=prevsong_button_img)
        self.prevsong_button.grid(row=6, column=0, padx=0, pady=(0,10), sticky="es")

        nextsong_button_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/nextsong.png"), size=(30,30))
        self.nextsong_button = customtkinter.CTkButton(master=self, 
                                                       width=75,
                                                       height=30,
                                                       border_width=0,
                                                       corner_radius=0,
                                                       fg_color="transparent",
                                                       text="",
                                                       command=self.nextsong_button_click, 
                                                       image=nextsong_button_img)
        self.nextsong_button.grid(row=6, column=2, padx=0, pady=(0,10), sticky="ws", columnspan=2)

        # volume control
        volume_img = customtkinter.CTkImage(light_image=Image.open(f"./themes/{self.master.theme_name}/volume.png"), size=(15,15))
        self.volume_icon = customtkinter.CTkButton(master=self, 
                                                       width=15,
                                                       height=15,
                                                       fg_color="transparent",
                                                       text="",
                                                       state="disabled",
                                                       image=volume_img)       
        self.volume_icon.grid(row=7, column=2, pady=(0,5), sticky="ws")

        frame_colour = self.cget("fg_color")
        self.volumebar = customtkinter.CTkSlider(master=self,
                                                   width=120,
                                                   height=15,
                                                   number_of_steps=100)
        self.volumebar.grid(row=7, column=2, padx=0, pady=(0,5), sticky="s")


    # replace f.read()
    def get_data(self, num_bytes, start_byte=0, filename=None, request=None, media="song"):
        if self.stream_type == "local":
            with open(filename, "rb") as f:
                f.seek(start_byte) 
                data = f.read(num_bytes)
            f.close()
            return data 
        
        elif self.stream_type == "online":
            if media == "song":
                # if request[self.song_switch] failed: cut song, re-check ip address 
                # print(request, self.song_switch)
                end_byte = min(start_byte + num_bytes, len(request[self.song_switch].content) - 1)
                data = request[self.song_switch].content[start_byte:end_byte]
                # print(f"get {start_byte} to {end_byte} from {self.song_switch}")
                self.song_switch = (self.song_switch + 1) % len(request)
                return data 
            
            elif media == "lyric":
                # print(request, self.lyric_switch, len(request))
                end_byte = min(start_byte + num_bytes, len(request[self.lyric_switch].content) - 1)
                data = request[self.lyric_switch].content[start_byte:end_byte]
                self.lyric_switch = (self.lyric_switch + 1) % len(request)
                return data 
            
            else:
                end_byte = min(start_byte + num_bytes, len(request[self.song_switch].content) - 1)
                data = request[self.song_switch].content[start_byte:end_byte]
                self.song_switch = (self.song_switch + 1) % len(request)

    # parse wav file header, return dict
    def parse_header(self, filename=None, request=None):
        print("loading header... ", end="")
        header_data = self.get_data(44, 0, filename, request)

        chunk_id = int.from_bytes(header_data[:4], "big")
        chunk_size = int.from_bytes(header_data[4:8], "little")

        file_format = header_data[8:12].decode("utf-8")

        subchunk_1_id = header_data[12:16].decode("utf-8")
        subchunk_1_size = int.from_bytes(header_data[16:20], "little")

        audio_format = int.from_bytes(header_data[20:22], "little")
        num_channels = int.from_bytes(header_data[22:24], "little")

        sample_rate = int.from_bytes(header_data[24:28], "little")

        byte_rate = int.from_bytes(header_data[28:32], "little")

        block_align = int.from_bytes(header_data[32:34], "little")

        bits_per_sample = int.from_bytes(header_data[34:36], "little")

        subchunk_2_id = header_data[36:40].decode("utf-8")

        subchunk_2_size = int.from_bytes(header_data[40:44], "little")

        # some wav files contain LIST subchunk
        if subchunk_2_id == "LIST":
            # skip this chunk
            self.get_data(subchunk_2_size, 44, filename, request)

            data = self.get_data(8, subchunk_2_size+44, filename, request)

            data_chunk_id = data[:4].decode("utf-8")
            data_chunk_size = int.from_bytes(data[4:8], "little")

        else:
            data_chunk_id = subchunk_2_id
            data_chunk_size = subchunk_2_size

        header = dict()
        header["chunk_id"] = chunk_id
        header["chunk_size"] = chunk_size
        header["file_format"] = file_format
        header["subchunk_1_id"] = subchunk_1_id
        header["subchunk_1_size"] = subchunk_1_size
        header["audio_format"] = audio_format
        header["num_channels"] = num_channels
        header["sample_rate"] = sample_rate
        header["byte_rate"] = byte_rate
        header["block_align"] = block_align
        header["bits_per_sample"] = bits_per_sample
        header["data_chunk_id"] = data_chunk_id
        header["data_chunk_size"] = data_chunk_size

        # print(header)
        return header


    def calc_song_length(self, header):
        num_bytes = header["data_chunk_size"] - 8
        num_bits = num_bytes * 8
        num_samples = num_bits / header["bits_per_sample"] / header["num_channels"]
        num_sec = num_samples / header["sample_rate"]
        return int(num_sec)

    # parse srt lyric file
    def parse_lyric(self, start_second, lyric_path=None, request=None):
        print("loading lyrics... ", end="")
        # obtain lyrics by interleaving, store in a temp local file
        if self.stream_type == "online":
            lyric_path = "cur_song.srt"
            chunk = 8192
            cur_start = 0
            with open(lyric_path, 'wb') as f:
                while True:
                    data = self.get_data(chunk, start_byte=cur_start, request=request, media="lyric")
                    f.write(data)
                    cur_start += chunk

                    if(cur_start >= len(request[0].content) - 1):
                        break
            f.close()

        lyric_srt = pysrt.open(lyric_path)
        lyric_srt = lyric_srt.slice(ends_after={'minutes':start_second//60, 'seconds': start_second % 60})

        n = len(lyric_srt)
        lyric = []  # list of dict ({start_time, end_time, text})
        time_fmt = "{}:{}:{},{}"  # hh:mm:ss,ms
        for i in range(n):
            cur_srt = lyric_srt[i]
            
            parsed_start = parse(time_fmt, str(cur_srt.start))
            start_time = int(parsed_start[0]) * 3600 + int(parsed_start[1]) * 60 + int(parsed_start[2]) + int(parsed_start[3]) * 0.001

            parsed_end = parse(time_fmt, str(cur_srt.end))
            end_time = int(parsed_end[0]) * 3600 + int(parsed_end[1]) * 60 + int(parsed_end[2]) + int(parsed_end[3]) * 0.001

            cur_lyr = {"start_time" : start_time, "end_time" : end_time, "text" : cur_srt.text}
            lyric.append(cur_lyr)
        return lyric

    def set_volume(self, data, bytes_per_sample, channels, volume):
        frame_count = len(data) // bytes_per_sample
        res = b""
        sample_len = bytes_per_sample // channels

        # multiply amplitude by volume ([0, 1])
        for i in range(frame_count):
            if channels == 2:
                data1 = int.from_bytes(data[sample_len*i*2:sample_len*i*2+sample_len], "little", signed=True)
                data2 = int.from_bytes(data[sample_len*i*2+sample_len:sample_len*2*(i+1)], "little", signed=True)

                data1 = int(volume * data1)
                data2 = int(volume * data2)

                res += data1.to_bytes(sample_len, "little", signed=True) 
                res += data2.to_bytes(sample_len, "little", signed=True)
            else:
                data1 = int.from_bytes(data[sample_len*i:sample_len*(i+1)], "little", signed=True)
                data1 = int(volume * data1)
                res += data1.to_bytes(sample_len, "little", signed=True)
        return res

    # threadded for playing music, parallel run with ctk mainloop
    def start_stream_local(self, song_path, lyric_path, start_second):
        # set frame rates (seconds per frame)
        music_frame_spf = 0.01
        lyric_frame_spf = 0.01
        progress_bar_frame_spf = 0.5
        player_gif_frame_spf = 0.05

        # parse header
        header = self.parse_header(filename=song_path)

        # prepare player gif
        player_gif_update_frame_count = int(player_gif_frame_spf * header["sample_rate"])
        player_gif_cur_frame = 0
        player_gif_total_frame = len(self.gif_list)

        song_length = self.calc_song_length(header)
        self.master.current_song_length = song_length
        song_minute = song_length // 60
        song_second = song_length % 60

        # prepare lyrics
        if lyric_path != None:
            lyric = self.parse_lyric(start_second, lyric_path=lyric_path)
            lyric_count = len(lyric)
            lyric_id = 0

        lyric_update_frame_count = int(lyric_frame_spf * header["sample_rate"])

        # prepare audio playing
        pya = pyaudio.PyAudio()
        bytes_per_sample = int(header["bits_per_sample"] / 8 * header["num_channels"])
        sample_per_frame = int(header["sample_rate"] * music_frame_spf)
        bytes_per_frame = int(sample_per_frame * bytes_per_sample)

        skip_bytes = bytes_per_sample * header["sample_rate"] * start_second

        progress_bar_frame_count = int(progress_bar_frame_spf * header["sample_rate"])
        self.progressbar.configure(number_of_steps=song_length)

        with open(song_path, "rb") as f:
            f.read(44)  # skip header
            f.read(skip_bytes)  # skip to start at certain second

            stream = pya.open(format =
                        pya.get_format_from_width(header["bits_per_sample"] / 8),
                        channels = header["num_channels"],
                        rate = header["sample_rate"],
                        output = True)
            sample_count = 0
            second_count = start_second
            
            data = f.read(bytes_per_frame)
            data = self.set_volume(data, bytes_per_sample, header["num_channels"], self.volumebar.get())

            track_second = start_second

            print("finish loading")
            # while song not yet end
            while data != b"" and self.master.play_state != "stop":
                if self.master.play_state == "play":
                    sample_count += sample_per_frame
                    stream.write(data)
                    data = f.read(bytes_per_frame)
                    data = self.set_volume(data, bytes_per_sample, header["num_channels"], self.volumebar.get())
                    
                    if self.master.play_state == "stop":
                        break
                    
                    try:
                        if sample_count % progress_bar_frame_count == 0:
                            if not self.progress_bar_down:
                                self.progressbar.set(second_count / song_length)

                        if sample_count % player_gif_update_frame_count == 0:
                            gif_img = self.gif_list[player_gif_cur_frame]
                            ctk_gif_img = customtkinter.CTkImage(light_image=gif_img, size=(144,144))
                            self.graphics.configure(image=ctk_gif_img)
                            player_gif_cur_frame = (player_gif_cur_frame + 1) % player_gif_total_frame

                        if sample_count % lyric_update_frame_count < lyric_update_frame_count / 2:
                            second_count += lyric_frame_spf

                            # end current line 
                            if lyric_path != None:
                                if lyric_id < lyric_count and second_count >= lyric[lyric_id]["end_time"]:
                                    self.lyrics.configure(text="")
                                    lyric_id += 1

                                # display new line lyric
                                if lyric_id < lyric_count and second_count >= lyric[lyric_id]["start_time"]:
                                    self.lyrics.configure(text=lyric[lyric_id]["text"])
                            
                            # update current progress
                            progress_bar_sec = song_length * self.progressbar.get()
                            if self.progress_bar_down:
                                self.progress_text = "%02d:%02d/%02d:%02d" % (progress_bar_sec//60, progress_bar_sec%60, song_minute, song_second)
                            else:
                                self.progress_text = "%02d:%02d/%02d:%02d" % (second_count//60, int(second_count%60), song_minute, song_second)
                            self.progress.configure(text=self.progress_text)
                    except:
                        pass

                elif self.master.play_state == "pause":
                    time.sleep(0.1)
                
                else:
                    break
            
            # if data == b""
            self.master.play_state = "stop"
            stream.close()
            pya.terminate()
    
    def start_stream_online(self, start_second, song_url, lyric_url):
        # song streaming
        song_request = []
        for url in song_url:
            print(f"streaming from {url}")
            song_request.append(requests.get(url, stream=True))

        song_content_length = len(song_request[0].content)
        # assert song_content_length == len(song_request[1].content)

        if lyric_url != None:
            lyric_request = []
            for url in lyric_url:
                lyric_request.append(requests.get(url, stream=True))

            lyric_content_length = len(lyric_request[0].content)

        # set frame rates (seconds per frame)
        music_frame_spf = 0.005

        lyric_frame_spf = 0.01
        progress_bar_frame_spf = 1

        player_gif_frame_spf = 0.05
        # parse header
        header = self.parse_header(request=song_request)

        # prepare player gif
        player_gif_update_frame_count = int(player_gif_frame_spf * header["sample_rate"])
        player_gif_cur_frame = 0
        player_gif_total_frame = len(self.gif_list)

        song_length = self.calc_song_length(header)
        self.master.current_song_length = song_length
        song_minute = song_length // 60
        song_second = song_length % 60

        # prepare lyrics
        if lyric_url != None and len(lyric_url) > 0:
            lyric = self.parse_lyric(start_second, request=lyric_request)
            lyric_count = len(lyric)
            lyric_id = 0

        lyric_update_frame_count = int(lyric_frame_spf * header["sample_rate"])

        # prepare audio playing
        pya = pyaudio.PyAudio()
        bytes_per_sample = int(header["bits_per_sample"] / 8 * header["num_channels"])
        sample_per_frame = int(header["sample_rate"] * music_frame_spf)
        bytes_per_frame = int(sample_per_frame * bytes_per_sample)

        skip_bytes = bytes_per_sample * header["sample_rate"] * start_second

        progress_bar_frame_count = int(progress_bar_frame_spf * header["sample_rate"])
        self.progressbar.configure(number_of_steps=song_length)

        cur_start = 0
        # skip header
        self.get_data(44, start_byte=cur_start, request=song_request)  
        cur_start += 44

        # skip to start at certain second
        self.get_data(skip_bytes, start_byte=cur_start, request=song_request)  
        cur_start += skip_bytes

        stream = pya.open(format = 
                    pya.get_format_from_width(header["bits_per_sample"] / 8),
                    channels = header["num_channels"],
                    rate = header["sample_rate"],
                    output = True)

        sample_count = 0
        second_count = start_second
        
        # get a frame of music stream 
        data = self.get_data(bytes_per_frame, start_byte=cur_start, request=song_request)  
        cur_start += bytes_per_frame

        data = self.set_volume(data, bytes_per_sample, header["num_channels"], self.volumebar.get())

        track_second = start_second

        print("finish loading")
        # while song not stopped
        while self.master.play_state != "stop":
            if self.master.play_state == "play":
                # if self.master.stop_song_event.is_set():
                #     break 
                
                sample_count += sample_per_frame
                stream.write(data)

                # end song (reached end of stream content)
                if self.stream_type == "online":
                    if cur_start >= len(song_request[0].content):
                        break

                # get a frame of music stream
                data = self.get_data(bytes_per_frame, start_byte=cur_start,request=song_request)  
                cur_start += bytes_per_frame
                
                data = self.set_volume(data, bytes_per_sample, header["num_channels"], self.volumebar.get())

                
                if self.master.play_state == "stop":
                    break
                
                # prevent error when stream stopped (e.g. changing theme)
                try:
                    if sample_count % progress_bar_frame_count == 0:
                        if not self.progress_bar_down:
                            self.progressbar.set(second_count / song_length)

                    if sample_count % player_gif_update_frame_count == 0:
                            gif_img = self.gif_list[player_gif_cur_frame]
                            ctk_gif_img = customtkinter.CTkImage(light_image=gif_img, size=(144,144))
                            self.graphics.configure(image=ctk_gif_img)
                            player_gif_cur_frame = (player_gif_cur_frame + 1) % player_gif_total_frame

                    if sample_count % lyric_update_frame_count == 0:
                        second_count += lyric_frame_spf

                        if lyric_url != None:
                            # end current line 
                            if lyric_id < lyric_count and second_count >= lyric[lyric_id]["end_time"]:
                                self.lyrics.configure(text="")
                                lyric_id += 1

                            # display new line lyric
                            if lyric_id < lyric_count and second_count >= lyric[lyric_id]["start_time"]:
                                self.lyrics.configure(text=lyric[lyric_id]["text"])
                    
                        # update current progress
                        progress_bar_sec = song_length * self.progressbar.get()
                        if self.progress_bar_down:
                            self.progress_text = "%02d:%02d/%02d:%02d" % (progress_bar_sec//60, progress_bar_sec%60, song_minute, song_second)
                        else:
                            self.progress_text = "%02d:%02d/%02d:%02d" % (second_count//60, int(second_count%60), song_minute, song_second)
                        self.progress.configure(text=self.progress_text)
                except:
                    pass 

            elif self.master.play_state == "pause":
                time.sleep(0.1)
            
            else:
                break

        self.master.play_state = "stop"
        stream.close()
        pya.terminate()

    def play_song(self, start_second, new_state):
        # terminate prev stream
        self.master.play_state = "stop"          
        
        # kill thread failed, redo
        if threading.active_count() > 1:
            self.master.retry_state = new_state
            self.master.retry_play_song = True
            self.master.retry_start_second = start_second
            return False
        
        song = self.master.songlist_songs.loc[self.master.current_song]
        songname = song["song_name"]

        # load gui items
        self.song_name.configure(text=songname)
        self.artist.configure(text=song["artist"])
        self.lyrics.configure(text="")
        if start_second == 0:
            self.progressbar.set(0)

        if song["local"]:
            if start_second == 0:
                print(f"now loading: {songname} (local)")
            self.stream_type = "local"

            song_path = self.master.songlist_local_songs_path[songname]
            lyrics_path = self.master.songlist_local_lyrics_path[songname]

            threading.Thread(target=self.start_stream_local, args=[song_path, lyrics_path, start_second], daemon=True).start()

        elif song["nonlocal"]:
            if start_second == 0:
                print(f"now loading: {songname} (online)")
            self.stream_type = "online"

            # start streaming song
            song_url = self.master.songlist_nonlocal_songs_url[songname]
            lyric_url = self.master.songlist_nonlocal_lyrics_url[songname]

            threading.Thread(target=self.start_stream_online, args=[start_second, song_url, lyric_url], daemon=True).start() 

        self.master.play_state = new_state
        self.update_play_button()

        # success, no need to retry
        self.master.retry_play_song = False 
        return True

    def update_play_button(self):
        if self.master.play_state == "play":
            self.play_button.configure(image=self.pause_button_img)
        else:
            self.play_button.configure(image=self.play_button_img)

    def play_button_click(self):
        if self.master.play_state == "pause":
            self.master.play_state = "play"
        else:
            self.master.play_state = "pause"
        self.update_play_button()

    def prevsong_button_click(self):
        prev_song_id = (self.master.current_song + self.master.songlist_song_count - 1) % self.master.songlist_song_count
        self.master.current_song = prev_song_id
        self.play_song(0, "play")


    def nextsong_button_click(self):
        next_song_id = (self.master.current_song + 1) % self.master.songlist_song_count
        # print("play song", next_song_id)
        self.master.current_song = next_song_id
        self.play_song(0, "play")

    def progress_slider_pressing(self, arg):
        self.progress_bar_down = True

    def progress_slider(self, arg):
        original_state = self.master.play_state

        progress_bar_val = self.progressbar.get()
        start_second = int(self.master.current_song_length * progress_bar_val)
        # print("move to second", start_second)

        self.play_song(start_second, original_state)
        self.progress_bar_down = False

    def p2p_button_click(self):
        if self.p2p_setup_window == None or not self.p2p_setup_window.winfo_exists():
            self.p2p_setup_window = P2PWindow(self.master)
        
        self.p2p_setup_window.focus()

    def theme_option_click(self, choice):
        theme_id = self.theme_options.index(choice)
        self.master.set_theme(theme_id)
