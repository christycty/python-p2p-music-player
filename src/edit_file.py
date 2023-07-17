import tkinter as tk
import tkinter.messagebox
import customtkinter
import pandas as pd
import requests

from p2p_ import P2P

class DeleteWindow(customtkinter.CTkToplevel):
    def __init__(self, songlist, song_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.songlist = songlist 
        self.song_id = song_id
        # print(self.song_id)

        self.geometry("480x200")
        self.grid_columnconfigure((0, 1), weight=0)
        self.grid_rowconfigure((0, 1), weight=0)

        self.notif_text = "Are you sure you want to remove the song from your local storage?"
        self.label = customtkinter.CTkLabel(self, text=self.notif_text, wraplength=380)
        self.label.grid(row=0, column=0, columnspan=2, padx=50, pady=20)

        self.yes_button = customtkinter.CTkButton(self, text="Yes", command=lambda : self.choose("yes"))
        self.yes_button.grid(row=1, column=1, padx=20, pady=20)

        self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=lambda : self.choose("cancel"))
        self.cancel_button.grid(row=1, column=0, padx=20, pady=20)
    
    def choose(self, choice):
        if choice == "yes":
            database = pd.read_csv("./database.csv")
            database.drop(self.song_id, axis=0, inplace=True)
            database.to_csv("./database.csv", index=False, encoding='utf8')

            self.songlist.delete_song(self.song_id)
        
        self.destroy()

class EditWindow(customtkinter.CTkToplevel):
    def __init__(self, songlist, song_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.songlist = songlist 
        self.song_id = song_id

        self.geometry("500x400")
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7), weight=1)

        # self.notif_text = "Please input your edits:"
        # self.label = customtkinter.CTkLabel(self, text=self.notif_text, height=10)
        # self.label.grid(row=0, column=0, columnspan=2, padx=50, pady=20)

        song = self.songlist.master.songlist_songs.loc[song_id]

        # song name
        self.songname_text = customtkinter.CTkLabel(self, text="New Song Name", height=10)
        self.songname_text.grid(row=1, column=0, padx=50, pady=(1, 0), sticky="w", columnspan=2)

        self.songname_edit = customtkinter.CTkEntry(self, height=10)
        self.songname_edit.insert(0, song["song_name"])
        self.songname_edit.grid(row=2, column=0, padx=50, pady=0, sticky="new", columnspan=2)

        # artist
        self.artist_text = customtkinter.CTkLabel(self, text="New Artist", height=10)
        self.artist_text.grid(row=3, column=0, padx=50, pady=(1, 0), sticky="w", columnspan=2)

        self.artist_edit = customtkinter.CTkEntry(self, height=10)
        self.artist_edit.insert(0, song["artist"])
        self.artist_edit.grid(row=4, column=0, padx=50, pady=0, sticky="new", columnspan=2)

        # album 
        self.album_text = customtkinter.CTkLabel(self, text="New Album", height=10)
        self.album_text.grid(row=5, column=0, padx=50, pady=(1, 0), sticky="w", columnspan=2)

        self.album_edit = customtkinter.CTkEntry(self, height=10)
        self.album_edit.insert(0, song["album"])
        self.album_edit.grid(row=6, column=0, padx=50, pady=0, sticky="new", columnspan=2)

        self.yes_button = customtkinter.CTkButton(self, text="Confirm", command=lambda : self.choose("confirm"))
        self.yes_button.grid(row=7, column=1, padx=30, pady=10, sticky="w")

        self.cancel_button = customtkinter.CTkButton(self, text="Cancel", command=lambda : self.choose("cancel"))
        self.cancel_button.grid(row=7, column=0, padx=30, pady=10, sticky="e")

    def choose(self, choice):
        if choice == "confirm":

            database = pd.read_csv("./database.csv")

            song_name = self.songname_edit.get()
            artist = self.artist_edit.get()
            album = self.album_edit.get()

            dict = {"song_name":song_name, "artist":artist, "album":album}
            print(dict)
            changed = 0
            for element in dict:
                if dict[element] != '':
                    database.loc[self.song_id, [element]] = dict[element]
                    changed = 1
            if changed:
                database.to_csv("./database.csv", index=False, encoding='utf8')
                self.songlist.edit_songinfo(self.song_id)
        
        self.destroy()




class P2PWindow(customtkinter.CTkToplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.songlist = songlist 
        #self.song_id = song_id
        self.master = master

        self.IP_count = 1
        self.IP = []
        self.IP_entry = []

        self.geometry("500x400")
        self.title("Input IP Address")

        self.grid_rowconfigure(0, weight=10)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)


        # create top frame (IP connection)
        self.topframe = customtkinter.CTkScrollableFrame(master=self)
        self.topframe.grid(row=0, column=0, padx=10, pady=10, sticky="news")
        self.topframe.grid_rowconfigure((0, 1, 2), weight=1)
        self.topframe.grid_columnconfigure((0, 1), weight=10)
        self.topframe.grid_columnconfigure(2, weight=1)

        # add button
        self.add_button = customtkinter.CTkButton(master=self.topframe, text="+", 
                                                  width=30,
                                                  height=30,
                                                  command=lambda : self.add())
        self.add_button.grid(row=0, column=2, padx=(0,10), pady=(10, 0), sticky="ne")

        # Enter IP address box (The first IP)
        self.IP_text = customtkinter.CTkLabel(master=self.topframe,
                                               text=f"Enter IP address {self.IP_count}:", 
                                               height=10)
        self.IP_text.grid(row=1, column=0, padx=50, pady=(1, 0), sticky="w", columnspan=2)

        self.IP_edit = customtkinter.CTkEntry(master=self.topframe, height=10)
        self.IP_edit.grid(row=2, column=0, padx=50, pady=(10, 30), sticky="new", columnspan=2)
        self.IP_entry.append(self.IP_edit)




        # create bottom frame (confirm / cancel)
        self.bottomframe = customtkinter.CTkFrame(master=self)
        self.bottomframe.grid(row=1, column=0, padx=10, pady=10, sticky="news")
        self.bottomframe.grid_rowconfigure((0, 1, 2), weight=1)
        self.bottomframe.grid_columnconfigure((0, 1), weight=10)
        self.bottomframe.grid_columnconfigure(2, weight=1)
    
        self.yes_button = customtkinter.CTkButton(master=self.bottomframe, 
                                                  text="Confirm", 
                                                  command=lambda : self.choose("confirm"))
        self.yes_button.grid(row=3, column=1, padx=30, pady=10, sticky="w")

        self.cancel_button = customtkinter.CTkButton(master=self.bottomframe, 
                                                     text="Cancel", 
                                                     command=lambda : self.choose("cancel"))
        self.cancel_button.grid(row=3, column=0, padx=30, pady=10, sticky="e")


    def add(self):
        self.IP_count += 1
        self.IP_text = customtkinter.CTkLabel(master=self.topframe,
                                               text=f"Enter IP address {self.IP_count}:", 
                                               height=10)
        self.IP_text.grid(row=self.IP_count*2-1, column=0, padx=50, pady=(1, 0), sticky="w", columnspan=2)

        self.IP_edit = customtkinter.CTkEntry(master=self.topframe, height=10)
        self.IP_edit.grid(row=self.IP_count*2, column=0, padx=50, pady=(10, 30), sticky="new", columnspan=2)
        self.IP_entry.append(self.IP_edit)

    def valid_ip(self, ip):
        request_url = f"http://{ip}:{self.master.PORT}"
        try:
            request = requests.get(request_url)
        except:
            return False

        if request.status_code != 200:
            return False
        return True


    def choose(self, choice):
        if choice == "confirm":
            # 1.3 save interleave image in directory
            # 1.4 download song database from all IPs
            for IP_box in self.IP_entry:
                # get input IP address
                ip_addr = IP_box.get()
                
                # strip extra spaces / new line characters
                ip_addr = str.strip(ip_addr)

                # ignore empty and connected ip
                if ip_addr == "" or ip_addr in self.master.IP_list:
                    continue

                # check if can connect to ip
                if self.valid_ip(ip_addr):
                    self.master.IP_list.append(ip_addr)
                    print(f"successfully connected to {ip_addr}")
                else:
                    print(f"failed to connect to {ip_addr}")
            
            # self.master.IP_list = self.IP

            self.p2p_connection = P2P(self.master)

            print("loading online songs...")
            self.master.fetch_songs()
            print("finish loading online songs")

            self.master.songlist.songlist_display_index = range(self.master.songlist_song_count)
            self.master.songlist.display_songs()

        self.destroy()


    #def add_row():

    #def insert_row():
