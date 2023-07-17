A P2P music player that supports music control, file management and P2P music streaming from other computers. It is a school project with the parsing and streaming of wav chunk data, and the P2P connection requests implemented in the code. 

![]("sample_ui.png")

# Setup and Execution
## Installation
1. clone the repository
2. create a ```songs``` folder in the root directory
3. install required libraries from ```pip install -r requirements.txt```

## Import Music
1. add the wav song files into the ```songs``` folder
2. add the srt lyrics files into the ```lyrics``` folder (optional)
3. open ```database.csv```, and add an entry for each song to be accessed by the app
   * lyrics_path, artist and album information are optional

## Run Program
```python ./src/app.py```
