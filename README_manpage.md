# Spotify-Recorder Manual Page
spotify-recorder is a command line tool only that takes many [command-line options].  

```
spotify-recorder [-h] [-S SETTINGS] [--ascii] [--all-artists] [--artist-album-type ARTIST_ALBUM_TYPE]
                 [--artist-album-market ARTIST_ALBUM_MARKET] [--ascii-path-only] [-d DIRECTORY] [--debug]
                 [-e CODECS] [--codec-args CODEC_ARGS] [--format ENCODER_FORMAT] [--fail-log FAIL_LOG] [-f FILENAME]
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
  --debug               Add diagnostic messages (Spotify API, device/audio issues)
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
| Command                                       | Description                                                               |
|-----------------------------------------------|---------------------------------------------------------------------------|
| *spotify-recorder spotify:track:52xaypL0Kjzk0ngwv3oBPR*     | record a single track using user from API keys. Once raw recording complete, encode the audio file using the default codec (PCM, 32 bit IEEE float) as well as the default PCM format/container (.wav). The output file will be located in the current directory and named ``<artist name> - <track name>.wav`` with proper metadata tags set.  The temporary, raw recording can be found at ``%USERPROFILE%\AppData\Local\Temp`` and will be named: ``<artist name> - <track name>.wav``. From there you can encode it using e.g. ffmpeg |
| *spotify-recorder -e "flac" spotify:track:52xaypL0Kjzk0ngwv3oBPR*     | record a single track using user from API keys. Once raw recording has completed, the raw recording with be encoded using the "FLAC" codec and (default) ".flac" extension. The output file will be located in the current directory and named and named ``<artist name> - <track name>.flac``. |
| *spotify-recorder spotify:playlist:4vkGNcsS8lRXj4q945NIA4*     | record entire playlist from playlist URI. |
| *spotify-recorder --playlist myplaylist*   | record entire named playlist. |
| *spotify-recorder -e "opus" --playlist "myplaylist" --playlist-create "type:m3u" "path:./{artist:1l}/" --search "M:/{ext}" --filename "M:/{ext}/{artist} - {track_name}.{ext}"*|record entire named playlist ``myplaylist``, encode raw recordings to the OPUS format, create a M3U playlist named ``playlist_myplaylist_opus.m3u``, use a relative directory with the first letter of the artist as prefix, saving the OPUS audio file in drive ``"M:"`` in for example directory ``/opus/myplaylist/a/Adele - Chasing Pavements.opus``. Search ``M:/opus`` for an existing encoded Opus file, and if founds, use a symlink or copy of that file instead.  The search function is useful to avoid re-recording and re-encoding e.g. when several playlists contain the same tracks.|
|*spotify-recorder --update-metadata spotify:track:52xaypL0Kjzk0ngwv3oBPR*|update metadata on audion files that have been previously encoded in addition to record the track or album from the URI|
|*spotify-recorder -e "opus" -e "aac" --codec-args", "flac=-af aformat=s16:48000" --filename "M:/{ext}/{playlist}/{artist:1l}/{artist} - {track_name}.{ext}"*|record entire named playlist "myplaylist", encode the raw recordings to AAC and FLAC formats, pass ``-af aformat=s16:48000`` to ``ffmpeg`` to fine-tune theh FLAC encoding.|

# Formatting rules for filename, directories and path prefixes

The format string dictates how ``Spotify-Recorder`` will organize your recorded files.  This is controlled through the ``-f | --filename`` option.  The string should include the format of the file name and optionally a directory structure.   If you do not include a format string, the default format will be used: ``{album_artist}/{album}/{artist} - {track_name}.{ext}``.

Additionally, you can now use a substring function.  The typical use case is to classify e.g. all artists in folders using the first digit of the artist name, converted to lower or upper case: ``{artist:1l}/{artist} - {track_name}.{ext}``
Your format string can include the following variables names, which are case-sensitive and wrapped in curly braces, if you want your file/path name to be overwritten with Spotify metadata.

| Names and aliases                      | Description                                                               |
|----------------------------------------|---------------------------------------------------------------------------|
| ``{track_artist}``, ``{artist}``       | The track's artist                                                        |
| ``{track_artists}``, ``{artists}``     | Similar to ``{track_artist}`` but will join multiple artists with a comma (e.g. "artist 1, artist 2")                   |
| ``{album_artist}``                     | When passing an album, the album's artist (e.g. "Various Artists"). If no album artist exists, the track artist is used instead |
| ``{album}``                            | Album name                                    |
| ``{album_track_count}``                | Number of tracks in album                     |
| ``{track_name}``, ``{track}``          | Track name                                    |
| ``{year}``                             | Release year of the album                     |
| ``{ext}``, ``{extension}``             | Filename extension (i.e. "mp3", "ogg", "flac", ...)|
| ``{track_num}``, ``{track_idx}``, ``{track_index}``| The track number of the disc      |
| ``{idx}``, ``{index}``                 | Playlist index                                |
| ``{disc_num}``, ``{disc_idx}``, ``{disc_index}``| The disc number of the album                  |
| ``{playlist}``, ``{playlist_name}``    | Name of playlist if passed a playlist uri, otherwise "No Playlist" |
| ``{playlist_owner}``, ``{playlist_user}``, ``{playlist_username}``| User name of playlist's owner if passed a playlist uri, otherwise "No Playlist Owner" |
| ``{user}``, ``{username}``             | Spotify username of logged-in user                                             |
| ``{feat_artists}``, ``{featuring_artists}``| Featuring artists join by commas (see Prefix String section below)         |
| ``{track_uri}``, ``{uri}``             | Spotify track uri                             |
| ``{artist:n[lL]}``                     | Takes the first *n* digits of the artist name and convert to lower (l) or upper (L) case|

Any substring in the format string that does not match a variable above will be passed through to the file/path name unchanged.

_Zero-Filled Padding_

Format variables that represent an index can be padded with zeros to a user-specified length.  For example, ``{idx:3}`` will produce the following output: 001, 002, 003, etc.  If no number is provided, no zero-filled padding will occur (e.g. 8, 9, 10, 11, ...). The variables that accept this option include ``{idx}``, ``{track_num}``, ``{disc_num}``, ``{smart_track_num}`` and their aliases.
