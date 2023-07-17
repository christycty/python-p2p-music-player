import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import os
import threading

class P2P():
    def __init__(self, master):
        self.master = master

        # IP Address of PC1: 10.13.155.193 (mec)
        # IP Address of PC2: 10.13.118.142 (chelsea)
        # IP Address of PC3: 10.13.168.207 (christy)

        self.PORT = 8000

        # set up local host as server (macOS)
        #appscript.app('Terminal').do_script('python3 -m http.server')

        # for music
        '''
        self.song_folder = 'songs'
        self.ext = 'wav'
        self.search_song = "The Beginning.wav"
        '''

        # for image
        self.image_file = '1-2.bmp'
        self.image_path = f'image/{self.image_file}'

        # for database
        self.database_file = "database"
        self.database_ext = ".csv"


        # for searching for particular file and downloading (interleave)
        # self.total_song_list = self.get_total_song_list(self.master.IP_list)
        # self.interleave_url = self.get_interleave(self.total_song_list)

        self.download_image(self.master.IP_list)

        # for downloading database
        self.download_database(self.master.IP_list)


    '''
    # get all the song list from a single IP
    def get_song_list(self, PC):
        url = f'http://{PC}:{self.PORT}/{self.song_folder}/'
        song_list = []

        # get all song list of the current PC
        page = requests.get(url, timeout=3).text
        soup = BeautifulSoup(page, 'html.parser')
        return [unquote(node.get('href')) for node in soup.find_all('a') if node.get('href').endswith(self.ext)]


    # store all remote pc and their song list in total_song_list
    def get_total_song_list(self, connection):
        total_song_list = {}
        for PC in connection:
            s = self.get_song_list(PC)
            print(s)
            total_song_list[PC] = s

        print(f"total list: {total_song_list}")
        return total_song_list


    # store all url that contains the required file
    def get_interleave(self, total_song_list):
        interleave_url = []
        for PC in total_song_list:
            if self.search_song in total_song_list[PC]:
                url = f"http://{PC}:{self.PORT}/{self.song_folder}/{self.search_song}"
                interleave_url.append(url)

        print(f"url that contain the song: {interleave_url}")
        return interleave_url

    '''

        
    # download file by streaming
    def download_image(self, connection):
        request = []
        for IP in connection:
            url = f"http://{IP}:{self.PORT}/{self.image_path}"
            request.append(requests.get(url, stream=True))

        length = len(request[0].content)
        request_num = len(request)

        print(f"length: {length}")

        # assert length == len(request[1].content)

        chunk_length = 8192
        start = 0
        end = chunk_length
        switch = 0

        with open(self.image_file, 'wb') as f:
            while True:
                f.write(request[switch].content[start:end])
                start = min(end, length-1)
                end = min(end + chunk_length, length)

                #print(f"start: {start}")
                #print(f"end: {end}")
                if(start == length-1 and end == length):
                    break
                switch = (switch + 1) % request_num


    def download_database(self, connection):
        for i, PC in enumerate(connection):
            url = f'http://{PC}:{self.PORT}/{self.database_file}{self.database_ext}'
            r = requests.get(url, stream=True)

            local_filename = self.database_file + str(i+2) + self.database_ext

            with open(local_filename, 'wb') as f:
                f.write(r.content)