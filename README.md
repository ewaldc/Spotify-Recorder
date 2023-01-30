# Spotify-Recorder

A replacement for ``spotify-ripper`` which is now  obsolete due to the sunset of the Spotify libraries (aka libspotify) for Windows/Linux.
Spotify-Recorder provides 5 main functions:
- Plays and records tracks, albums or playlists from Spotify using loopback audio devices
- Encodes the recorded audio in PCM (WAV) IEEE-FLOAT format by default and in multiple other formats (FLAC, AAC, OPUS, MP3, VORBIS, AC3) on request
- Generates filenames for the encode audio based on formatting rules, with ability to execute character replacements
- Sets metadata tags on the encoded audio files
- Generates relative or absolute playlists of existing or generated audio files e.g. for import on Android

# Limitations and defects
The code is for **educational purposes only**. Its use does not meat production quality and recording of audio streams violates the Spotify terms and conditions (ToS). In most countries though, it is legal to your record audio/video streams from owned subscriptions for personal use only. Reproducing this content as your own or distributing it, is illegal.
- Several known defects in this 1.0 release
- Not yet supported/tested on Linux.
- The code does not catch all exceptions (e.g. random/unexplained failures of Spotify API)

**Please note: Spotify’s highest quality setting is 320 kbps. Hence it’s not possible to produce true lossless quality. The benefit of encoding to a lossless format is primarily to not double encode the audio data and reduce the quality further.**

# Requirements
A Spotify developer account and premium account is required for overall operation.

# Simplified installation on Windows
1. Create or select a folder where you want to install Spotify-Recorder
2. Download [Spotify-Recorder](releases/spotify-recorder_1.0.zip) and unzip
3. Set up a [Spotify Developer account](https://developer.spotify.com/console/). ``http://example.com/`` is a potential redirect URL.
4. Save your Spotify API credentials in a file with name `.env`:
```
# Variables for Spotify Web API
SPOTIPY_CLIENT_ID="<client ID>"
SPOTIPY_CLIENT_SECRET="<client secret>"
SPOTIPY_REDIRECT_URI="<redirect URL>"
```
5. Install *Ffmpeg* to encode the raw recordings which are saved in PCM 32 bit IEEE float format (.wav container) by default.
6. Open a terminal (DOS, Powershell) in the Spotify-Recorder installation folder to perform a few installation checks
```
# Is ffmpeg in path and working?
ffmpeg -formats
# Is Spotify-Recorder properly installed and working?
.\spotify-recorder.exe -h
```
7. Configure your audio playback/recording devices
* Make sure you have a default playback device
* Set it to DVD or Studio quality: 2-channel, 16 or 24 bits, 48000 Hz sample rate
* Disable audio enhancements (recommended)

8. If you are running Anti-virus software, allow/enable microphone access

# Recording with Spotify-Recorder on Windows
1. Open the Spotify Windows Player application
2. Open a terminal window in your Spotify-Recorder directory
3. Run the Spotify-Recorder command as desired.  Spotify-Recorder will discover and control the Spotify Player via the API.  There is no need to start/stop/pause anything on the Spotify Player app, but it's OK to use the app to search music etc.
4. You can interrupt Spotify-Recorder using the keyboard (e.g. ``<ctrl>C``).  In that case, you may want to manually stop the current playing song on the Spotify Player app.


#  Advanced Installations
[Advanced installations](README_advanced.md) allow you to install from source, perform portable installations and build your own custom executable.

# Manual Page and Usage
spotify-recorder is a command line tool that takes many [command-line options](README_manpage.md).  

# Getting started - examples
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

The detailed formatting rules can be found [here](README_formatting.md)
