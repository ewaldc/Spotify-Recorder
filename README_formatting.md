# Spotify-Recorder formatting rules for filenames, directories and path prefixes

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
