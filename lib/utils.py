# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

from colorama import Fore, Style
from datetime import datetime, timedelta
from lib.encode import encoder_default_format
import mutagen
import os, sys, errno
import re, math
import unicodedata

#  since there is no class, use global var
util_globals = {'args': None}

def init_util_globals(args):
    util_globals['args'] = args

def get_args():
    return util_globals['args']

def enc_str(_str):
    encoding = "ascii" if get_args().ascii else "utf-8"
    return _str.encode(encoding)

def path_exists(path):
    return os.path.exists(enc_str(path))

def get_alternative_file(file, trackinfo, ext):
    return os.path.abspath(os.path.join(os.path.dirname(file), get_track_artist(trackinfo) + ' - ' + to_ascii(escape_filename_part(trackinfo["name"] + '.' + ext))))

def get_track_artist(track):
    return to_ascii(escape_filename_part(track['artists'][0]['name']))
    return os.path.exists(enc_str(path))

def print_str(_str):
    """print without newline"""
    if not get_args().has_log:
        if sys.version_info >= (3, 0): print(_str, end = '', flush = True)
        else:
            sys.stdout.write(_str)
            sys.stdout.flush()

def norm_path(path):
    """normalize path"""
    return os.path.normpath(os.path.realpath(path))

def sanitize_playlist_name(name):
    """replace unwanted path characters"""
    return re.sub(r"[\\/]", "-", name) if name is not None else None

# borrowed from AndersTornkvist's fork
def escape_filename_part(part):
    """escape possible offending characters"""
    part = re.sub(r"\s*/\s*", r' & ', part)
    part = re.sub(r"""\s*[\\/:"*?<>|]+\s*""", r' ', part)
    part = part.strip()
    part = re.sub(r"(^\.+\s*|(?<=\.)\.+|\s*\.+$)", r'', part)
    return part

def to_ascii(_str, on_error='ignore'):
    """convert unicode to ascii if necessary"""
    # python 3 renamed unicode to str
    args = get_args()
    if sys.version_info >= (3, 0):
        if isinstance(_str, bytes) and not args.ascii:
            return str(_str, "utf-8")
        elif isinstance(_str, str) and args.ascii:
            return _str.encode("ascii", on_error).decode("utf-8")
#        elif isinstance(_str, str): return _str.encode("utf-8")
        else: return _str
    else:
        if isinstance(_str, str) and not args.ascii:
            return unicode(_str, "utf-8")
        elif isinstance(_str, unicode) and args.ascii:
            return _str.encode("ascii", on_error).decode("utf-8")
#        elif isinstance(_str, str): return _str.encode("utf-8")
        else: return _str

def to_normalized_ascii(_str):
    if sys.version_info < (3, 0):
        if not isinstance(_str, unicode): _str = unicode(_str, "utf-8")
    return unicodedata.normalize('NFKD', _str).encode('ASCII', 'ignore')

def rm_file(file_name):
    try: os.remove(enc_str(file_name))
    except OSError as e:
        # don't need to print a warning if the file doesn't exist
        if e.errno != errno.ENOENT:
            print(Fore.YELLOW + "Warning: error while trying to remove file " + file_name + Fore.RESET)
            print(str(e))

def default_settings_dir():
    return norm_path(os.path.join(os.path.expanduser("~"), ".spotify-recorder"))

def settings_dir():
    args = get_args()
    return norm_path(args.settings) if args.settings is not None \
        else default_settings_dir()

def base_dir():
    args = get_args()
    return norm_path(args.directory) if args.directory is not None else os.getcwd()
        
def is_unavailable(country, track):
    if 'is_playable' in track: return not track['is_playable']
    return False if not track['available_markets'] else country not in track['available_markets']

def parse_time_str(time_str):
    # if we are passed a time (e.g. 14:20)
    if re.match(r"^\d{2}:\d{2}$", time_str):
        t = datetime.strptime(time_str, "%H:%M")
        calc_time = datetime.now().replace(hour=t.hour, minute=t.minute)
        if datetime.now() > calc_time: calc_time += timedelta(days=1)
        return calc_time

    # if we are passed hour/minute offset (e.g. 1h20m)
    match = re.match(r"^((\d+h)?(\d+m))|(\d+h)$", time_str)
    if match is not None:
        calc_time = datetime.now()
        groups = match.groups()

        hours = groups[1] if groups[1] is not None else groups[3]
        if hours is not None:
            calc_time = calc_time + timedelta(hours=int(hours[:-1]))

        minutes = groups[2]
        if minutes is not None:
            calc_time = calc_time + timedelta(minutes=int(minutes[:-1]))

        return calc_time
    return None

def change_file_extension(file_name, ext):
    return os.path.splitext(file_name)[0] + "." + ext

def get_ext(args, codec):
    return args.encoder_format[codec] if args.encoder_format and args.encoder_format[codec] else encoder_default_format[codec]

def get_track_name(track):
    name = track["name"].split("- ")
    length = len(name)
    track_name = name[0].strip()
    if length > 1:
        track_name += " ("
        for idx in range(1, length):
            track_name += name[idx].strip()
            if idx < length - 1: track_name += ", "
        track_name += ")"
    return to_ascii(escape_filename_part(track_name))

def get_track_artist(track):
    return to_ascii(escape_filename_part(track['artists'][0]['name']))

def format_track_string(recorder, format_string, idx, track, ext):
    args = get_args()
    idx_str = str(idx + 1)
    artists = track['artists']
    track_name = get_track_name(track)
    track_num = str(track['track_number'])
    track_uri = track['uri']
    disc_num = str(track['disc_number'])
    track_artist = get_track_artist(track)
    track_artists = to_ascii(escape_filename_part(", ".join([artist['name'] for artist in artists])))
    if len(artists) > 1:
        featuring_artists = to_ascii(escape_filename_part(", ".join([artist['name'] for artist in artists[1:]])))
    else: featuring_artists = ""

    album = track['album']
    album_name = to_ascii(escape_filename_part(album['name']))
    album_artist = to_ascii(escape_filename_part(album['artists'][0]['name']))
    album_track_count = str(album['total_tracks'])

    if recorder.playlist_name is not None:
        playlist_name = to_ascii(sanitize_playlist_name(recorder.playlist_name))
        playlist_owner = to_ascii(recorder.playlist_owner)
    else:
        playlist_name = "No Playlist"
        playlist_owner = "No Playlist Owner"

    release_date = escape_filename_part(album['release_date'])
    release_date_precision = to_ascii(escape_filename_part(album['release_date_precision']))
    year = release_date if (release_date_precision == 'year') else release_date.split('-')[0]

    #extension = args.output_type
    user = recorder.user['display_name']

    tags = {
        "track_artist": track_artist,
        "track_artists": track_artists,
        "album_artist": album_artist,
        "album_track_count": album_track_count,
        "artist": track_artist,
        "artists": track_artists,
        "album": album_name,
        "track_name": track_name,
        "track": track_name,
        "year": year,
        "ext": ext,
        "extension": ext,
        "idx": idx_str,
        "index": idx_str,
        "track_num": track_num,
        "track_idx": track_num,
        "track_index": track_num,
        "disc_num": disc_num,
        "disc_idx": disc_num,
        "disc_index": disc_num,
        "playlist": playlist_name,
        "playlist_name": playlist_name,
        "playlist_owner": playlist_owner,
        "playlist_user": playlist_owner,
        "playlist_username": playlist_owner,
        "user": user,
        "username": user,
        "feat_artists": featuring_artists,
        "featuring_artists": featuring_artists,
        "uri": track_uri,
        #"custom": args.custom_format
    }
    fill_tags = {"idx", "index", "track_num", "track_idx", "track_index", "disc_num", "disc_idx", "disc_index"}
    prefix_tags = {"feat_artists", "featuring_artists"}
    paren_tags = {"track_name", "track"}
    substr_tags = {"artist"}
    for tag in tags.keys():
        format_string = format_string.replace("{" + tag + "}", to_ascii(tags[tag]))
        if tag in substr_tags:
            match = re.search(r"\{" + tag + r":\d+[lL]\}", format_string)
            if match:
                tokens = format_string[match.start():match.end()].strip("{}").split(":")
                token = tokens[1]
                digits = int(token[:-1]) if token[-1].isalpha() else int(token)
                tag_filled = tags[tag][0:digits]
                if token[-1].isalpha(): tag_filled = tag_filled.lower() if token[-1].islower() else tag_filled.upper()
                else: tag_filled = tags[tag][0:digits]
                format_string = format_string[:match.start()] + tag_filled + format_string[match.end():]
        if tag in fill_tags:
            match = re.search(r"\{" + tag + r":\d+\}", format_string)
            if match:
                tokens = format_string[match.start():match.end()].strip("{}").split(":")
                tag_filled = tags[tag].zfill(int(tokens[1]))
                format_string = format_string[:match.start()] + tag_filled + format_string[match.end():]
        if tag in prefix_tags:
            # don't print prefix if there are no values
            if len(tags[tag]) > 0:
                match = re.search(r"\{" + tag + r":[^\}]+\}", format_string)
                if match:
                    tokens = format_string[match.start():match.end()].strip("{}").split(":")
                    format_string = format_string[:match.start()] + tokens[1] + \
                        " " + tags[tag] + format_string[match.end():]
            else:
                match = re.search(r"\s*\{" + tag + r":[^\}]+\}", format_string)
                if match: format_string = format_string[:match.start()] + format_string[match.end():]
        if tag in paren_tags:
            match = re.search(r"\{" + tag + r":paren\}", format_string)
            if match:
                match_tag = re.search(r"(.*)\s+-\s+([^-]+)", tags[tag])
                if match_tag:
                    format_string = format_string[:match.start()] + match_tag.group(1) + " (" + \
                        match_tag.group(2) + ")" + format_string[match.end():]
                else: format_string = format_string[:match.start()] + tags[tag] + format_string[match.end():]

    if args.format_case is not None:
        if args.format_case == "upper": format_string = format_string.upper()
        elif args.format_case == "lower": format_string = format_string.lower()
        elif args.format_case == "capitalize":
            format_string = ' '.join(word[0].upper() + word[1:] for word in format_string.split())
    return to_ascii(format_string)

# returns path of executable
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(enc_str(fpath), os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program): return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file): return exe_file

    return None

KB_BYTES = 1024
'''Number of bytes per KB (2^10)'''
MB_BYTES = 1048576
'''Number of bytes per MB (2^20)'''
GB_BYTES = 1073741824
'''Number of bytes per GB (2^30)'''
KB_UNIT = "KB"
'''Kilobytes abbreviation'''
MB_UNIT = "MB"
'''Megabytes abbreviation'''
GB_UNIT = "GB"
'''Gigabytes abbreviation'''

def format_size(size, short=False):
    """Format ``size`` (number of bytes) into string format doing KB, MB, or GB
    conversion where necessary.

    When ``short`` is False (the default) the format is smallest unit of
    bytes and largest gigabytes; '234 GB'.
    The short version is 2-4 characters long and of the form

        256b
        64k
        1.1G
    """
    if not short:
        unit = "Bytes"
        if size >= GB_BYTES:
            size = float(size) / float(GB_BYTES)
            unit = GB_UNIT
        elif size >= MB_BYTES:
            size = float(size) / float(MB_BYTES)
            unit = MB_UNIT
        elif size >= KB_BYTES:
            size = float(size) / float(KB_BYTES)
            unit = KB_UNIT
        return "%.2f %s" % (size, unit)
    else:
        suffixes = u' kMGTPEH'
        if size == 0: num_scale = 0
        else: num_scale = int(math.floor(math.log(size) / math.log(1000)))
        if num_scale > 7: suffix = '?'
        else: suffix = suffixes[num_scale]
        num_scale = int(math.pow(1000, num_scale))
        value = size / num_scale
        str_value = str(value)
        if len(str_value) >= 3 and str_value[2] == '.':
            str_value = str_value[:2]
        else:
            str_value = str_value[:3]
        return "{0:>3s}{1}".format(str_value, suffix)

# returns true if audio_file is a partial of track
def is_partial(audio_file, track_duration_ms, alt_audio_file = None):
    args = get_args()
    if args.partial_check == "none": return False
    
    def _is_partial(file):
        if args.partial_check == "strict":
            return track_duration_ms > audio_file_duration_ms
        # for 'weak' the setting is 2% wiggle-room
        wiggle_room = track_duration_ms * 0.05 if args.partial_check == "weak" \
            else float(args.partial_check.split(":")[1]) * track_duration_ms / 100
        _isPartial = (abs(track_duration_ms - audio_file_duration_ms) > wiggle_room) or audio_file_duration == 0
        if _isPartial and args.debug:
            print(Fore.MAGENTA + 'Duration deviation encountered above threshold for audio file: ' + Fore.CYAN + file + Fore.RESET)
        return _isPartial

    def get_audio_file_duration(audio_file):
        if (path_exists(audio_file)):
            try: 
                _file = mutagen.File(audio_file)
                if _file is not None and _file.info is not None:
                    return _file.info.length, _file.info.length * 1000
            except KeyboardInterrupt: raise
            except Exception as e:
                print(Fore.RED + 'Exception encountered (' + str(e) + ') - unable to get duration from (corrupt ?) audio file: ' + Fore.CYAN + audio_file + Fore.RESET)
        return 0, 0

    audio_file_duration, audio_file_duration_ms = get_audio_file_duration(audio_file)
    if audio_file_duration_ms == 0:
        if alt_audio_file:
            audio_file_duration, audio_file_duration_ms = get_audio_file_duration(alt_audio_file)
            if audio_file_duration_ms == 0: return True
            if args.debug:
                print(Fore.MAGENTA + 'Renaming legacy audio file: ' + Fore.CYAN + alt_audio_file + Fore.YELLOW + ' to: ' + Fore.CYAN + audio_file + Fore.RESET)
            os.rename(alt_audio_file, audio_file)
            return _is_partial(audio_file)
        return True
    return _is_partial(audio_file)

# borrowed from eyeD3
def format_time(seconds, total=None, short=False):
    """
    Format ``seconds`` (number of seconds) as a string representation.
    When ``short`` is False (the default) the format is:
        HH:MM:SS.
    Otherwise, the format is exacly 6 characters long and of the form:
        1w 3d
        2d 4h
        1h 5m
        1m 4s
        15s

    If ``total`` is not None it will also be formatted and
    appended to the result separated by ' / '.
    """

    def time_tuple(ts):
        if ts is None or ts < 0:
            ts = 0
        hours = ts / 3600
        mins = (ts % 3600) / 60
        secs = (ts % 3600) % 60
        tstr = '%02d:%02d' % (mins, secs)
        if int(hours):
            tstr = '%02d:%s' % (hours, tstr)
        return (int(hours), int(mins), int(secs), tstr)

    if not short:
        hours, mins, secs, curr_str = time_tuple(seconds)
        retval = curr_str
        if total:
            hours, mins, secs, total_str = time_tuple(total)
            retval += ' / %s' % total_str
        return retval
    else:
        units = [
            (u'y', 60 * 60 * 24 * 7 * 52),
            (u'w', 60 * 60 * 24 * 7),
            (u'd', 60 * 60 * 24),
            (u'h', 60 * 60),
            (u'm', 60),
            (u's', 1),
        ]

        seconds = int(seconds)
        if seconds < 60:
            return u'00m {0:02d}s'.format(seconds)
        for i in range(len(units) - 1):
            unit1, limit1 = units[i]
            unit2, limit2 = units[i + 1]
            if seconds >= limit1:
                return u'{0:02d}{1} {2:02d}{3}'.format(
                    seconds // limit1, unit1,
                    (seconds % limit1) // limit2, unit2)
        return u'  ~inf'