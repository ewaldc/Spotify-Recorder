*** WORK IN PROGRESS ***
# Architecture
Spotify-Recorder is implemented in Python, using classes and threads for parallel encoding and tagging.
Spotify-Recorder makes very limited use of Spotipy as it mostly uses its own code for interfacing with the Spotify Web based API.
Mutagen is used for reading, setting and updating tags/metadata.
Pyaudiowpatch is used as stand-in for PyAudio as it provides better support for loopback devices.
Psutil is used to increment the process priority

# Advanced Installation on Windows
Alternatively you can build your own copy from the sources in this repository:
- Clone or download this repository
- Install Python3 e.g. Python3.10.x.
The use of Portable Python is absolutely fine, just ensure ``%APPDIR%\Python3\App\Python`` and ``%APPDIR%\Python3\App\Python\Scripts`` are part of the user environment PATH setting (``%APPDIR%`` is the root of your portable apps directory).
- Install [Ffmpeg](https://ffmpeg.org/download.html). It's possible to use a portable version, just make sure *ffmpeg.exe* is part of the PATH (edit environment variables e.g. ``%APPDIR%\AudioVideo\ffmpeg-5.1.2\bin``)
- Open a Python Shell (typically PowerShell) to install the required dependencies:
```
pip install mutagen psutil colorama pyaudiowpatch spotipy python-dotenv
```
- Optionally, you can create your personal packaged Windows binary using ``pyinstaller`` in the current directory or directory of choice (distpath)
```
pyinstaller spotify-recorder.spec
```

# Config settings

For options that you want set on every run, you can use a config file named ``config.ini`` in the settings folder (defaults to ``~/.spotify-recorder`` on Linux and ``%USERPROFILE%\.spotify-recorder``).  Alternatively, a config file directory of choice can be specified using the -S option (e.g. -S ./local_config). The options in the config file use the same name as the command line options with the exception that dashes are translated to underscores.  Any option specified in the command line will overwrite any setting in the config file.  Please put all options under the ``[main]`` section.

Here is an example config file
```
    [main]
    ascii = True
    filename = M:/{ext}/{artist:1l}/{artist} - {track_name}.{ext}
    last = True
    genres = album
```
