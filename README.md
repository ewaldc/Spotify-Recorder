# Spotify-Recorder

A replacement for ``spotify-ripper`` which is now  obsolete due to the sunset of the Spotify libraries (aka libspotify) for Windows/Linux.
Spotify-Recorder provides 5 main functions:
- Plays and records tracks, albums or playlists from Spotify using loopback audio devices
- Encodes the recorded audio in PCM (WAV) IEEE-FLOAT format by default and in multiple other formats (FLAC, AAC, OPUS, MP3, VORBIS, AC3) on request
- Generates filenames for the encode audio based on formatting rules, with ability to execute character replacements
- Sets metadata tags on the encoded audio files
- Generates relative or absolute playlists of existing or generated audio files e.g. for import on Android

# Architecture
Spotify-Recorder is implemented in Python, using classes and threads for parallel encoding and tagging.
Spotify-Recorder makes very limited use of Spotipy as it mostly uses its own code for interfacing with the Spotify Web based API.
Mutagen is used for reading, setting and updating tags/metadata.
Pyaudiowpatch is used as stand-in for PyAudio as it provides better support for loopback devices.
Psutil is used to increment the process priority

# Limitations and defects
At this first release, the code is not supported/tested on Linux.
The code is for **educational purposes only**. Its use does not meat production quality and recording of audio streams violates the Spotify terms and conditions (ToS). In most countries though, it is legal to your record audio/video streams from owned subscriptions for personal use only. Reproducing this content as your own or distributing it, is illegal.
- Not all functions are properly tested.
- The code does not catch all exceptions (e.g. random/unexplained failures of Spotify API)

**Please note: Spotify’s highest quality setting is 320 kbps. Hence it’s not possible to produce true lossless quality. The benefit of encoding to a lossless format is primarily to not double encode the audio data and reduce the quality further.**

# Requirements
A Spotify developer account and premium account is required for overall operation.
Take a look at: https://developer.spotify.com/console/ for setting up your Spotify Developer account.

Once you have obtained your credentials create a ``.env`` file in the top folder with following content:
```
# Variables for Spotify Web API
SPOTIPY_CLIENT_ID="<client ID>"
SPOTIPY_CLIENT_SECRET="<client secret>"
SPOTIPY_REDIRECT_URI="http://www.purple.com/"
```

Spotify-recorder uses *Ffmpeg* to encode the raw recordings which are saved in PCM 32 bit IEEE float format (.wav container) by default. 

# Installation on Windows
**The easiest way** to get started is to download a precompiled, zipped version from the ``releases`` folder

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

# Usage
spotify-recorder is a command line tool only that takes many command-line options:

```
spotify-recorder [-h] [-S SETTINGS] [--ascii] [--all-artists] [--artist-album-type ARTIST_ALBUM_TYPE]
                 [--artist-album-market ARTIST_ALBUM_MARKET] [--ascii-path-only] [-d DIRECTORY] [-e CODECS] [--codec-args CODEC_ARGS]
                 [--format ENCODER_FORMAT] [--fail-log FAIL_LOG] [-f FILENAME]
                 [--filename-replace FILENAME_REPLACE [FILENAME_REPLACE ...]] [--filename-windows-safe]
                 [--format-case {upper,lower,capitalize}] [-g {artist,album}] [--id3-v23] [-u USER] [-p PASSWORD] [-l] [-L LOG]
                 [--normalize] [-na] [--partial-check {none,weak,weak:<%>,strict}] [--play-token-resume RESUME_AFTER] [--playlist]
                 [--playlist-create PLAYLIST_CREATE [PLAYLIST_CREATE ...]] [--tags TAGS [TAGS ...]] [--remove-from-playlist]
                 [--recording-format {PCM:8,PCM:16,PCM:24,PCM:32,IEEE_FLOAT}] [--recording {keep,skip}] [--search SEARCH] [--strip-colors]
                 [--stereo-mode {j,s,f,d,m,l,r}] [--stop-after STOP_AFTER] [-V] [-y]
                 [uri ...]<br>

positional arguments:
  uri                   One or more Spotify URI(s) (playlist, track, album or file of URIs)

options:
  -h, --help            show this help message and exit
  -S SETTINGS, --settings SETTINGS
                        Path to settings, config and temp files directory [Default=~/.spotify-recorder]
  --ascii               Convert the file name and the metadata tags to ASCII encoding [Default=utf-8]
  --all-artists         Store all artists, rather than just the main artist, in the track's metadata tag
  --artist-album-type ARTIST_ALBUM_TYPE
                        Only load albums of specified types when passing a Spotify artist URI [Default=album,single,ep,compilation,appears_on]
  --artist-album-market ARTIST_ALBUM_MARKET
                        Only load albums with the specified ISO2 country code when passing a Spotify artist URI. You may get duplicate albums if not set. [Default=any]
  --ascii-path-only     Convert the file name (but not the metadata tags) to ASCII encoding [Default=utf-8]
  -d DIRECTORY, --directory DIRECTORY
                        Base directory where recorded files are saved [Default=cwd]
  -e CODECS, --encode CODECS
                        String containing one or a comma separated list of audio encoders to be used for post-processing the recorded tracks.-e|--encode option can be used multiple times as is "-e flac -e aac"Valid/supported codecs: flac, aac, opus, mp3, vorbis, ac3, pcm.
  --codec-args CODEC_ARGS
                        String in assignment form "<codec>=<codec-options>". Repeat --codec-args option for each codec as required.Example: --codec-args "flac=-af aformat=s16:48000" , --codec-args "opus=-vbr off"
  --format ENCODER_FORMAT
                        String in assignment form "<codec>=<format>". Repeat --format option for each codec as required.Example: --format "aac=m4a" , --format "opus=wbem"
  --fail-log FAIL_LOG   Logs the list of track URIs that failed to record
  -f FILENAME, --filename FILENAME
                        Save songs using this path/filename format (see below)
  --filename-replace FILENAME_REPLACE [FILENAME_REPLACE ...]
                        pattern to replace the output filename separated by "/". The following example replaces all spaces with "_" and all "-" with ".":    spotify-recorder --replace " /_" "\-/." uri
  --filename-windows-safe
                        Make filename safe for Windows file system (eleimate invalid characters, truncate filename to 255 characters)
  --format-case {upper,lower,capitalize}
                        Convert all words of the file name to upper-case, lower-case, or capitalized
  -g {artist,album}, --genres {artist,album}
                        Attempt to retrieve genre information from Spotify's Web API [Default=skip]
  --id3-v23             Store ID3 tags using version v2.3 [Default=v2.4]
  -u USER, --user USER  Spotify username
  -p PASSWORD, --password PASSWORD
                        Spotify password [Default=ask interactively]
  -l, --last            Use last login credentials
  -L LOG, --log LOG     Log in a log-friendly format to a file (use - to log to stdout)
  --normalize           Normalize volume levels of tracks
  -na, --normalized-ascii
                        Convert the file name to normalized ASCII with unicodedata.normalize (NFKD)
  --partial-check {none,weak,weak:<%>,strict}
                        Check for and overwrite partially recorded files. "weak" will err on the side of not re-recording the file if it is unsure (up to 5% deviation), whereas "strict" will re-record the file.  You can fine-tune the amount of deviation in % of reference audio playback lengthfor the "weak" check using "weak:<%s>" [Default=weak]
  --play-token-resume RESUME_AFTER
                        If the 'play token' is lost to a different device using the same Spotify account, the script will wait a speficied amount of time before restarting. This argument takes the same values as --resume-after [Default=abort]
  --playlist            Record the named playlist. In this case no uri specifier is needed or if provided, it will be ignored
  --playlist-create PLAYLIST_CREATE [PLAYLIST_CREATE ...]
                        Create a m3u/wpl playlist file using a series of optionstype="m3u"|"wpl": type of playlist (default: "m3u")path-type="relative"|"absolute": path type (default: "relative")path="<path-name-formatted>": path prefix (see README for path name formatting) to use for relative playlists (Default=absolute or relative path from current directory based on path-type)target-directory="<directory>": path (with {ext} replaced by codec extention) to use storing the generated playlist (Default=current directory)source-directory="<directory>": creates the playlist from files in this directory (default: current directory) matching the container extension (see README for path name formatting)
  --tags TAGS [TAGS ...]
                        Set, check or update tags/metadata on encoded audio filesaction="set|check|update: set, check or update metadata on existing or recorder and encoded files [default="set"]comment=<comment>: set comment metadata tag for all songs. Can include same tags as --formatcover="<file name>|embed": save album cover image to file name (e.g "cover.jpg") [default="embed"]cover-size="small|medium|large": size of covert art [default="large" (640x640)]grouping=<formatted text>: set grouping metadata tag to all songs. Can include same tags as --format.
  --remove-from-playlist
                        [WARNING: SPOTIFY IS NOT PROPROGATING PLAYLIST CHANGES TO THEIR SERVERS] Delete tracks from playlist after successful recording [Default=no]
  --recording-format {PCM:8,PCM:16,PCM:24,PCM:32,IEEE_FLOAT}
                        Raw (lossless) recording format to use. Select from: "PCM:8", "PCM:16", "PCM:24", "PCM:32", "IEEE_FLOAT". The default format is IEEE_FLOAT with WAV container format
  --recording {keep,skip}
                        "keep": Keep raw temporary (lossless) PCM/WAV files from recordings."skip": Skip all recording and encodeing operations e.g. to just create a playlist
  --search SEARCH       Search given folder name (see README for folder name formatting) recursively for encoded recording and create a symlink to this file (given permissions) if found to avoid duplication
  --strip-colors        Strip coloring from terminal output [Default=colors]
  --stereo-mode {j,s,f,d,m,l,r}
                        Advanced stereo settings for Lame MP3 encoder only
  --stop-after STOP_AFTER
                        Stops script after a certain amount of time has passed (e.g. 1h30m).Alternatively, accepts a specific time in 24hr format to stop after (e.g 03:30, 16:15)
  -V, --version         show program's version number and exit
  -y, --overwrite       Overwrite existing output files [Default=skip]
```

 # Examples
- record a single track using user from API keys. The audio file will use the defaukt codec (32 bit IEEE float PCM) with the default ".wav" format/container) and will located in the current directory.  The temporary raw recording can be found at "%USERPROFILE%\AppData\Local\Temp" and will be named: "<artist name> - <track name>.wav". From there you can encode it using e.g. ffmpeg: <br>*spotify-recorder spotify:track:52xaypL0Kjzk0ngwv3oBPR*
- record a single track using user from API keys and encode it using the "flac" codec. The raw audio file in 32 bit IEEE float PCM (.wav container) can be found at "%USERPROFILE%\AppData\Local\Temp" and will be named: "<artist name> - <track name>.wav". From there you can encode it using e.g. ffmpeg: <br>*spotify-recorder -e "flac" spotify:track:52xaypL0Kjzk0ngwv3oBPR*
- record entire playlist from playlist URI: <br>*spotify-recorder spotify:playlist:4vkGNcsS8lRXj4q945NIA4*
- record entire named playlist: <br>*spotify-recorder --playlist myplaylist*
- record a list of URIs from text file: <br>*spotify-recorder list_of_uris.txt*
- record entire named playlist "myplaylist", encode recorded WAV files to Opus format, create a M3U playlist (named "playlist_myplaylist_opus.m3u", use a relative directory with the first letter of the artist as prefix, saving the Opus output in drive "M:" in for example directory "/opus/myplaylist/a/Adele - Chasing Pavements.opus". Search "M:/opus" if an encoded Opus file already exists, and if that is the case, use0a symlink or copy to that file instead.  The search function is useful to avoid re-recording e.g. when several playlists contain the same tracks.<br>*spotify-recorder -e "opus" --playlist "myplaylist" --playlist-create "type:m3u" "path:./{artist:1l}/"*<br>*--search "M:/{ext}" --filename "M:/{ext}/{playlist}/{artist:1l}/{artist} - {track_name}.{ext}"*
- update metadata on files already ripped, rip new URIs: <br>*spotify-recorder --update-metadata spotify:track:52xaypL0Kjzk0ngwv3oBPR*
- record entire named playlist "myplaylist", encode recorded WAV files to Opus and FLAC formats, pass "-af aformat=s16:48000" to ffmpeg for encoding to FLAC format: <br>*spotify-recorder -e "opus" -e "flac" --codec-args", "flac=-af aformat=s16:48000" --filename "M:/{ext}/{playlist}/{artist:1l}/{artist} - {track_name}.{ext}"*

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

# Formatting rules for filename, directories and path prefixes

The format string dictates how ``Spotify-Recorder`` will organize your recorded files.  This is controlled through the ``-f | --filename`` option.  The string should include the format of the file name and optionally a directory structure.   If you do not include a format string, the default format will be used: ``{album_artist}/{album}/{artist} - {track_name}.{ext}``.

Additionally, you can now use a substring function.  The typical use case is to classify e.g. all artists in folders using the first digit of the artist name, converted to lower or upper case: ``{artist:1l}/{artist} - {track_name}.{ext}``
Your format string can include the following variables names, which are case-sensitive and wrapped in curly braces, if you want your file/path name to be overwritten with Spotify metadata.

+-----------------------------------------+-----------------------------------------------+
| Names and Aliases                       | Description                                   |
+=========================================+===============================================+
| ``{track_artist}``, ``{artist}``        | The track's artist                            |
+-----------------------------------------+-----------------------------------------------+
| ``{track_artists}``, ``{artists}``      | Similar to ``{track_artist}`` but will join   |
|                                         | multiple artists with a comma                 |
|                                         | (e.g. "artist 1, artist 2")                   |
+-----------------------------------------+-----------------------------------------------+
| ``{album_artist}``                      | When passing an album, the album's artist     |
|                                         | (e.g. "Various Artists").  If no album artist |
|                                         | exists, the track artist is used instead      |
+-----------------------------------------+-----------------------------------------------+
| ``{album}``                             | Album name                                    |
+-----------------------------------------+-----------------------------------------------+
| ``{album_track_count}``                 | Number of tracks in album                     |
+-----------------------------------------+-----------------------------------------------+
| ``{track_name}``, ``{track}``           | Track name                                    |
+-----------------------------------------+-----------------------------------------------+
| ``{year}``                              | Release year of the album                     |
+-----------------------------------------+-----------------------------------------------+
| ``{ext}``, ``{extension}``              | Filename extension (i.e. "mp3", "ogg", "flac",|
|                                         | ...)                                          |
+-----------------------------------------+-----------------------------------------------+
| ``{idx}``, ``{index}``                  | Playlist index                                |
|                                         |                                               |
+-----------------------------------------+-----------------------------------------------+
| ``{track_num}``, ``{track_idx}``,       | The track number of the disc                  |
| ``{track_index}``                       |                                               |
+-----------------------------------------+-----------------------------------------------+
| ``{disc_num}``, ``{disc_idx}``,         | The disc number of the album                  |
| ``{disc_index}``                        |                                               |
+-----------------------------------------+-----------------------------------------------+
| ``{playlist}``, ``{playlist_name}``     | Name of playlist if passed a playlist uri,    |
|                                         | otherwise "No Playlist"                       |
+-----------------------------------------+-----------------------------------------------+
|``{playlist_owner}``,                    | User name of playlist's owner if passed a     |
|``{playlist_user}``,                     | a playlist uri, otherwise "No Playlist Owner" |
|``{playlist_username}``                  |                                               |
+-----------------------------------------+-----------------------------------------------+
|``{user}``, ``{username}``               | Spotify username of logged-in user            |
+-----------------------------------------+-----------------------------------------------+
|``{feat_artists}``,                      | Featuring artists join by commas (see Prefix  |
|``{featuring_artists}``                  | String section below)                         |
+-----------------------------------------+-----------------------------------------------+
|``{track_uri}``, ``{uri}``               | Spotify track uri                             |
+-----------------------------------------+-----------------------------------------------+
|``{artist:n[lL]}``                       | Takes the first *n* digits of the artist name |
|                                         | and convert to lower (l) or upper (L) case    |
+-----------------------------------------+-----------------------------------------------+

Any substring in the format string that does not match a variable above will be passed through to the file/path name unchanged.

_Zero-Filled Padding_

Format variables that represent an index can be padded with zeros to a user-specified length.  For example, ``{idx:3}`` will produce the following output: 001, 002, 003, etc.  If no number is provided, no zero-filled padding will occur (e.g. 8, 9, 10, 11, ...). The variables that accept this option include ``{idx}``, ``{track_num}``, ``{disc_num}``, ``{smart_track_num}`` and their aliases.
