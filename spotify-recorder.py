#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os, platform, sys, signal, select, psutil
#sys.path.insert(1, "./lib") # You can put the absolute path
from colorama import init, Fore, AnsiToWin32
from lib.recorder import SportifyRecorder
from lib.utils import *
from dotenv import load_dotenv
import argparse
import pkg_resources
import schedule
#import tty
#import termios

global codecs_choices, codecs_args_choices, format_choices
global playlist_create_choices, playlist_create_type_choices, playlist_create_path_type_choices
global tags_choices, tags_action_choices, tags_cover_size_choices, tags_defaults
codecs_choices = ["flac", "aac", "opus", "mp3", "vorbis", "ac3", "pcm"]
codecs_args_choices = codecs_choices
format_choices = codecs_choices

recording_format_list = ["PCM:8", "PCM:16", "PCM:24", "PCM:32", "IEEE_FLOAT"]

playlist_create_choices = {"type", "path-type", "path", "target-directory", "source-directory"}
playlist_create_type_choices = {"m3u", "wpl"}
playlist_create_path_type_choices = {"absolute", "relative"}
playlist_create_defaults = {"type":"m3u", "path-type":"relative", "target-directory":"."}

tags_choices = {"action", "comment", "cover", "cover-size", "grouping"}
tags_action_choices = {"set", "get", "update"}
tags_cover_size_choices = {"large","medium","small"}
tags_defaults = {"action":"set", "cover":"embed", "cover-size":"large"}

if sys.version_info >= (3, 0): import configparser as ConfigParser
else: import ConfigParser

# create a keyvalue class
class keylist(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        if not getattr(namespace, self.dest): setattr(namespace, self.dest, [])  # Initialize at first occurance of argument
        _value_choices = globals().get(self.dest + '_choices')
        for value in values[0].split(','): 
            _value = value.lstrip()
            if _value_choices is None or _value in _value_choices: getattr(namespace, self.dest).append(_value) # assign into dictionary
            else: raise argparse.ArgumentTypeError('Value "' + _value + '" must be in ' + str(_value_choices))

class keyvalue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        if getattr(namespace, self.dest) is None: setattr(namespace, self.dest, dict())
        _key_choices = globals().get(self.dest + '_choices')
        for value in values: 
            if not '=' in value: return
            key, value = value.split('=',1) # split it into key and value
            key = key.lower()
            if _key_choices is None or key in _key_choices:
                _value_choices = globals().get(self.dest + "_" + key.replace('-', "_") + '_choices')
                if _value_choices is None or value in _value_choices:
                    getattr(namespace, self.dest)[key] = value #'='  #.join(data)     # assign into dictionary
                else: raise argparse.ArgumentTypeError('Value "' + value + '" must be in ' + str(_value_choices))
            else: raise argparse.ArgumentTypeError('Key "' + key + '" must be in ' + str(_key_choices))

class keyvaluelist(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, dict())
        _key_choices = globals().get(self.dest + '_choices')
        for value in values[0].split(','): 
            if not '=' in value: return
            value = value.lstrip()
            key, value = value.split('=',1) # split it into key and value
            key = key.lower()
            if _key_choices is None or key in _key_choices:
                _value_choices = globals().get(self.dest + "_" + key.replace('-', "_") + '_choices')
                if _value_choices is None or value in _value_choices:
                    getattr(namespace, self.dest)[key] = value #'='  #.join(data)     # assign into dictionary
                else: raise argparse.ArgumentTypeError('Value "' + value + '" must be in ' + str(_value_choices))
            else: raise argparse.ArgumentTypeError('Key "' + key + '" must be in ' + str(_key_choices))

def load_config(defaults):
    if not load_dotenv(): # load .env file in current directory
        print(Fore.RED + "Could not locate .env file with Spotify API credentials or .env is empty" + Fore.RESET)
        sys.exit(2)

    _settings_dir = settings_dir()
    if not os.path.exists(_settings_dir):
        print(Fore.GREEN + "First time initialization - creating settings directory at: " + Fore.CYAN + _settings_dir + Fore.RESET)
        os.makedirs(_settings_dir)

    config_file = os.path.join(_settings_dir, "config.ini")
    if os.path.exists(config_file):
        try:
            config = ConfigParser.ConfigParser()
            config.read(config_file)
            if not config.has_section("main"): return defaults
            config_items = dict(config.items("main"))
            to_array_options = ["replace"]

            # coerce boolean and none types
            config_items_new = {}
            for _key in config_items:
                item = config_items[_key]

                u_key = _key.replace("-", "_")
                if item == 'True': item = True
                elif item == 'False': item = False
                elif item == 'None': item = None
                else: item = item.strip("'\"")

                # certain options need to be in array (nargs=+)
                if u_key in to_array_options: item = [item]
                config_items_new[u_key] = item

            # overwrite any existing defaults
            defaults.update(config_items_new)
        except ConfigParser.Error as e:
            print("\nError parsing config file: " + config_file)
            print(str(e))
    return defaults

def patch_bug_in_mutagen():
    from mutagen.mp4 import MP4Tags, MP4Cover
    from mutagen.mp4._atom import Atoms, Atom, AtomError
    import struct

    def _key2name(key):
        if sys.version_info >= (3, 0): return key.encode("latin-1")
        else: return key

    def __fixed_render_cover(self, key, value):
        atom_data = []
        for cover in value:
            try: imageformat = cover.imageformat
            except AttributeError:
                imageformat = MP4Cover.FORMAT_JPEG
            atom_data.append(Atom.render(b"data", struct.pack(">2I", imageformat, 0) + bytes(cover)))
        return Atom.render(_key2name(key), b"".join(atom_data))

    print(Fore.RED + "Monkey-patching MP4/Python 3.x bug in Mutagen" + Fore.RESET)
    MP4Tags.__fixed_render_cover = __fixed_render_cover
    MP4Tags._MP4Tags__atoms[b"covr"] = (MP4Tags._MP4Tags__parse_cover, MP4Tags.__fixed_render_cover)

def partial_check_type(v):
    valid_choices = {'none', 'weak', 'strict'}
    if v in valid_choices: return v

    # allow user to override the "wiggle-room" for a weak check
    import re
    try: return re.match("^weak:[0-9]+$", v).group(0)
    except:
        raise argparse.ArgumentTypeError("String '" + v + "' does not match none, weak, weak:<%>, strict")

def main(prog_args=sys.argv[1:]):
    # in case we changed the location of the settings directory where the
    # config file lives, we need to parse this argument before we parse
    # the rest of the arguments (which can overwrite the options in the
    # config file)
    settings_parser = argparse.ArgumentParser(add_help=False)
    settings_parser.add_argument('-S', '--settings',
        help='Path to settings, config and temp files directory [Default=~/.spotify-recorder]')
    args, remaining_argv = settings_parser.parse_known_args(prog_args)
    init_util_globals(args)
  
    defaults = load_config({})   # load config file, overwriting any defaults

    parser = argparse.ArgumentParser(
        prog='spotify-recorder',
        description='Records Spotify URIs to encoded audio with ID3 tags and album covers',
        parents=[settings_parser],
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''Example usage:
    record a single track/file (PCM IEEE float with "wav" format/extension in current directory): spotify-recorder spotify:track:52xaypL0Kjzk0ngwv3oBPR
    record a single track/file (FLAC encoded with "flac" format/extension in current directory): spotify-recorder -e "flac" spotify:track:52xaypL0Kjzk0ngwv3oBPR
    record a single track/file (OPUS encoded with "opus" format/extension in current directory): spotify-recorder -e "opus"  spotify:track:52xaypL0Kjzk0ngwv3oBPR
    record entire playlist: spotify-recorder spotify:user:username:playlist:4vkGNcsS8lRXj4q945NIA4
    record entire album: spotify-recorder spotify:user:username:album:29tvPtFTZwxZZMIA34BjYm
    record a list of URIs contained in a file: spotify-recorder list_of_uris.txt
    ''')
    encoding_group = parser.add_mutually_exclusive_group(required=False)

    # set defaults
    parser.set_defaults(**defaults)

    try: prog_version = pkg_resources.require("spotify-recorder")[0].version
    except (pkg_resources.DistributionNotFound) as err: prog_version = "1.0"
    parser.add_argument('--ascii', action='store_true', default=False,
        help='Convert the file name and the metadata tags to ASCII encoding [Default=utf-8]')
    parser.add_argument('--all-artists', action='store_true',
        help='Store all artists, rather than just the main artist, in the track\'s metadata tag')
    parser.add_argument('--artist-album-type',
        help='Only load albums of specified types when passing a Spotify '
             'artist URI [Default=album,single,ep,compilation,appears_on]')
    parser.add_argument('--artist-album-market',
        help='Only load albums with the specified ISO2 country code when '
             'passing a Spotify artist URI. You may get duplicate albums if not set. [Default=any]')
    parser.add_argument('--ascii-path-only', action='store_true',
        help='Convert the file name (but not the metadata tags) to ASCII encoding [Default=utf-8]')
    parser.add_argument('-d', '--directory',
        help='Base directory where recorded files are saved [Default=cwd]')
    parser.add_argument('-e','--encode', nargs=1, action=keylist, default=['pcm'], dest="codecs", 
        help='String containing one or a comma separated list of audio encoders to be used for post-processing the recorded tracks.'
             '-e|--encode option can be used multiple times as is "-e flac -e aac"'
              'Valid/supported codecs: flac, aac, opus, mp3, vorbis, ac3, pcm.')
    parser.add_argument('--codec-args', nargs=1, action = keyvalue,
        help='String in assignment form "<codec>=<codec-options>". Repeat --codec-args option for each codec as required.'
             'Example: --codec-args "flac=-af aformat=s16:48000" , --codec-args "opus=-vbr off"') #, type=encoderArg
    #parser.add_argument('--codec_args', nargs='+', action = keyvalue, help='List of audio encoder arguments to be used for ffmpeg') #, type=encoderArg
    parser.add_argument('--format', nargs=1, action = keyvalue, dest="encoder_format",
        help='String in assignment form "<codec>=<format>". Repeat --format option for each codec as required.'
             'Example: --format "aac=m4a" , --format "opus=wbem"')
    parser.add_argument('--fail-log',
        help="Logs the list of track URIs that failed to record")
    parser.add_argument('-f', '--filename', dest="filename", default="{artist} - {track_name}.{ext}",
        help='Save songs using a formatted path/filename specification (see README). Default: "{artist} - {track_name}.{ext}"')
    parser.add_argument('--filename-replace', nargs="+", required=False,
        help='pattern to replace the output filename separated by "/". '
             'The following example replaces all spaces with "_" and all "-" '
             'with ".":    spotify-recorder --replace " /_" "\-/." uri')
    parser.add_argument('--filename-windows-safe', action='store_true',
        help='Make filename safe for Windows file system (eleimate invalid characters, truncate filename to 255 characters)')
    parser.add_argument('--format-case', choices=['upper', 'lower', 'capitalize'],
        help='Convert all words of the file name to upper-case, lower-case, or capitalized')
    parser.add_argument('-g', '--genres', choices=['artist', 'album'],
        help='Attempt to retrieve genre information from Spotify\'s Web API [Default=skip]')
    encoding_group.add_argument('--id3-v23', action='store_true',
        help='Store ID3 tags using version v2.3 [Default=v2.4]')
    parser.add_argument('-u', '--user', dest="user", default="", help='Spotify username, if not supplied use username from API or token cache')
    #parser.add_argument('-p', '--password', help='Spotify password [Default=ask interactively]')
    #parser.add_argument('-l', '--last', action='store_true', help='Use last login credentials')
    parser.add_argument('-L', '--log',
        help='Log in a log-friendly format to a file (use - to log to stdout)')
    parser.add_argument('--normalize', action='store_true',
        help='Normalize volume levels of tracks')
    parser.add_argument('-na', '--normalized-ascii', action='store_true',
        help='Convert the file name to normalized ASCII with unicodedata.normalize (NFKD)')
    parser.add_argument('--partial-check', metavar="{none,weak,weak:<%>,strict}", type=partial_check_type, default="weak",
        help='Check for and overwrite partially recorded files. "weak" will '
            'err on the side of not re-recording the file if it is unsure (up to 5%% deviation), '
            'whereas "strict" will re-record the file.  You can fine-tune the amount of deviation in %% of reference audio playback length'
            'for the "weak" check using "weak:<%%s>" [Default=weak]')
    parser.add_argument('--play-token-resume', metavar="RESUME_AFTER",
        help='If the \'play token\' is lost to a different device using '
            'the same Spotify account, the script will wait a speficied '
            'amount of time before restarting. This argument takes the same '
            'values as --resume-after [Default=abort]')
    parser.add_argument('--playlist', action='store_true', default=None,
        help='Record the named playlist. In this case no uri specifier is needed or if provided, it will be ignored')
    
    parser.add_argument('--playlist-create', nargs='+', action = keyvalue, #(parser, dest="playlist_create", option_strings=playlist_create_options), 
        help='Create a m3u/wpl playlist file using a series of options'
            'type="m3u"|"wpl": type of playlist (default: "m3u")'
            'path-type="relative"|"absolute": path type (default: "relative")'
            'path="<path-name-formatted>": path prefix (see README for path name formatting) to use for relative playlists (Default=absolute or relative path from current directory based on path-type)'
            'target-directory="<directory>": path (with {ext} replaced by codec extention) to use storing the generated playlist (Default=current directory)'
            'source-directory="<directory>": creates the playlist from files in this directory (default: current directory) matching the container extension (see README for path name formatting)')

    parser.add_argument('--tags', nargs='+', action = keyvalue, #(parser, dest="playlist_create", option_strings=playlist_create_options), 
        help='Set, check or update tags/metadata on encoded audio files'
            'action="set|check|update: set, check or update metadata on existing or recorder and encoded files [default="set"]'
            'comment=<comment>: set comment metadata tag for all songs. Can include same tags as --format'
            'cover="<file name>|embed": save album cover image to file name (e.g "cover.jpg") [default="embed"]'
            'cover-size="small|medium|large": size of covert art [default="large" (640x640)]'
            'grouping=<formatted text>: set grouping metadata tag to all songs. Can include same tags as --format.')

    #parser.add_argument('--playlist-sync', action='store_true', help='Sync playlist songs (rename and remove old songs)')
    parser.add_argument('--remove-from-playlist', action='store_true',
        help='[WARNING: SPOTIFY IS NOT PROPROGATING PLAYLIST CHANGES TO '
             'THEIR SERVERS] Delete tracks from playlist after successful recording [Default=no]')
    parser.add_argument('--recording-format', default="IEEE_FLOAT", choices=recording_format_list,
        help='Raw (lossless) recording format to use. '
        'Select from: "PCM:8", "PCM:16", "PCM:24", "PCM:32", "IEEE_FLOAT". '
        'The default format is IEEE_FLOAT with WAV container format')
    parser.add_argument('--recording', choices=["keep", "skip"],
        help='"keep": Keep raw temporary (lossless) PCM/WAV files from recordings.'
        '"skip": Skip all recording and encodeing operations e.g. to just create a playlist')
    parser.add_argument('--search', 
        help='Search given folder name (see README for folder name formatting) recursively for encoded recording '
              'and create a symlink to this file (given permissions) if found to avoid duplication')
    parser.add_argument('--strip-colors', action='store_true',
        help='Strip coloring from terminal output [Default=colors]')
    parser.add_argument('--stereo-mode', choices=['j', 's', 'f', 'd', 'm', 'l', 'r'],
        help='Advanced stereo settings for Lame MP3 encoder only')
    parser.add_argument('--stop-after',
        help='Stops script after a certain amount of time has passed (e.g. 1h30m).'
             'Alternatively, accepts a specific time in 24hr format to stop after (e.g 03:30, 16:15)')
    parser.add_argument('-V', '--version', action='version', version=prog_version)
    parser.add_argument('-y', '--overwrite', action='store_true', help='Overwrite existing output files [Default=skip]')

    parser.add_argument('uri', nargs="*",
        help='Zero or more Spotify URI(s) (either URI, a file of URIs or a search query)')
    parser.set_defaults(**defaults)
    #args, unknownargs = parser.parse_known_args(remaining_argv)
    args = parser.parse_args(remaining_argv)

    init_util_globals(args)

    # kind of a hack to get colorama stripping to work when outputting
    # to a file instead of stdout.  Taken from initialise.py in colorama
    def wrap_stream(stream, convert, strip, autoreset, wrap):
        if wrap:
            wrapper = AnsiToWin32(stream, convert=convert, strip=strip, autoreset=autoreset)
            if wrapper.should_wrap(): stream = wrapper.stream
        return stream

    args.has_log = args.log is not None
    if args.has_log:
        if args.log == "-": init(strip=True)
        else:
            encoding = "ascii" if args.ascii else "utf-8"
            log_file = codecs.open(enc_str(args.log), 'a', encoding)
            sys.stdout = wrap_stream(log_file, None, True, False, True)
    else: init(strip=True if args.strip_colors else None)
    if args.ascii_path_only is True: args.ascii = True

    # Set defaults 
    def set_defaults(argument, choices, defaults):
        for choice in choices:
            if not argument.get(choice):
                argument[choice]  = defaults.get(choice, "") 

    if args.playlist_create: set_defaults(args.playlist_create, playlist_create_choices, playlist_create_defaults)
    if args.tags is None: args.tags = dict()
    set_defaults(args.tags, tags_choices, tags_defaults)
    '''
        for choice in playlist_create_choices:
            if not args.playlist_create.get(choice):
                args.playlist_create[choice]  = playlist_create_defaults.get(choice, "") 
    '''
    # unless explicitly told not to, we are going to encode for utf-8 by default
    if not args.ascii and sys.version_info < (3, 0):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    # small sanity check on user option
    if args.user is not None and args.user == "USER":
        print(Fore.RED + "Please pass your username as --user " +
              "<YOUR_USER_NAME> instead of --user USER " + "<YOUR_USER_NAME>..." + Fore.RESET)
        sys.exit(1)
    
    print(Fore.GREEN + "Spotify Recorder - version " + prog_version + Fore.RESET)     # print version
    '''
    # give warning for broken feature
    if args.remove_from_playlist:
        print(Fore.RED + "--REMOVE-FROM-PLAYLIST WARNING:")
        print("SPOTIFY IS NOT PROPROGATING PLAYLIST CHANGES TO THEIR SERVERS.")
        print("YOU WILL NOT SEE ANY CHANGES TO YOUR PLAYLIST ON THE OFFICIAL SPOTIFY DESKTOP OR WEB APP." + Fore.RESET)

    if args.wav:
        args.output_type = "wav"
    elif args.pcm:
        args.output_type = "pcm"
    elif args.flac:
        args.output_type = "flac"
        if args.comp == "10":
            args.comp = "8"
    elif args.vorbis:
        args.output_type = "ogg"
        if args.vbr == "0":
            args.vbr = "9"
    elif args.opus:
        args.output_type = "opus"
        if args.vbr == "0":
            args.vbr = "320"
    elif args.aac:
        args.output_type = "aac"
        if args.vbr == "0":
            args.vbr = "500"
    elif args.mp4:
        args.output_type = "m4a"
        if args.vbr == "0":
            args.vbr = "5"
    elif args.alac:
        args.output_type = "alac.m4a"
    else:
        args.output_type = "mp3"

    # check that encoder tool is available
    encoders = {
        "flac": ("flac", "flac"),
        "aiff": ("sox", "sox"),
        "aac": ("aac", "-cutoff 18000"),
        "ogg": ("oggenc", "vorbis-tools"),
        "opus": ("opusenc", "opus-tools"),
        "mp3": ("lame", "lame"),
        "m4a": ("fdkaac", "fdk-aac-encoder"),
        "alac.m4a": ("avconv", "libav-tools"),
    }

    encoders2 = {
        "flac": ("flac", "flac"),
        "aiff": ("sox", "sox"),
        "aac": ("faac", "faac"),
        "ogg": ("oggenc", "vorbis-tools"),
        "opus": ("opusenc", "opus-tools"),
        "mp3": ("lame", "lame"),
        "m4a": ("fdkaac", "fdk-aac-encoder"),
        "alac.m4a": ("avconv", "libav-tools"),
    }
    if args.output_type in encoders.keys():
        encoder = encoders[args.output_type][0]
        if which(encoder) is None:
            print(Fore.RED + "Missing dependency '" + encoder +
                  "'.  Please install and add to path..." + Fore.RESET)
            # assumes OS X or Ubuntu/Debian
            command_help = ("brew install " if sys.platform == "darwin"
                            else "sudo apt-get install ")
            print("...try " + Fore.YELLOW + command_help +
                  encoders[args.output_type][1] + Fore.RESET)
            sys.exit(1)

    def encoding_output_str():
        if args.output_type == "wav": return "WAV, Stereo 16bit 44100Hz"
        elif args.output_type == "pcm": return "Raw Headerless PCM, Stereo 16bit 44100Hz"
        else:
            if args.output_type == "flac": return "FLAC, Compression Level: " + args.comp
            elif args.output_type == "aiff":
                return "AIFF"
            elif args.output_type == "alac.m4a":
                return "Apple Lossless (ALAC)"
            elif args.output_type == "ogg":
                codec = "Ogg Vorbis"
            elif args.output_type == "opus":
                codec = "Opus"
            elif args.output_type == "mp3":
                codec = "MP3"
            elif args.output_type == "m4a":
                codec = "MPEG4 AAC"
            elif args.output_type == "aac":
                codec = "AAC"
            else:
                codec = "Unknown"

            if args.cbr:
                return codec + ", CBR " + args.bitrate + " kbps"
            else:
                return codec + ", VBR " + args.vbr

    print(Fore.YELLOW + "  Encoding output:\t" + Fore.RESET + encoding_output_str())
    print(Fore.YELLOW + "  Spotify bitrate:\t" + Fore.RESET + args.quality + " kbps")

    # check that --stop-after and --resume-after options are valid
    if args.stop_after is not None and parse_time_str(args.stop_after) is None:
        print(Fore.RED + "--stop-after option is not valid" + Fore.RESET)
        sys.exit(1)
    if args.resume_after is not None and parse_time_str(args.resume_after) is None:
        print(Fore.RED + "--resume-after option is not valid" + Fore.RESET)
        sys.exit(1)
    if args.play_token_resume is not None and parse_time_str(args.play_token_resume) is None:
        print(Fore.RED + "--play_token_resume option is not valid" + Fore.RESET)
        sys.exit(1)
    '''
    def unicode_support_str():
        if args.ascii_path_only: return "Unicode tags, ASCII file path"
        elif args.ascii: return "ASCII only"
        else: return "Yes"

    print(Fore.YELLOW + "  Unicode support:\t\t" + Fore.RESET + unicode_support_str())
    print(Fore.YELLOW + "  Output directory:\t\t" + Fore.RESET + base_dir())
    print(Fore.YELLOW + "  Settings directory:\t\t" + Fore.RESET + settings_dir())
    print(Fore.YELLOW + "  Filename Format String:\t" + Fore.RESET + args.filename)
    print(Fore.YELLOW + "  Overwrite files:\t\t" + Fore.RESET + ("Yes" if args.overwrite else "No"))

    # increase priority
    p = psutil.Process(os.getpid())
    if sys.platform.startswith("win"): p.nice(psutil.REALTIME_PRIORITY_CLASS) #HIGH_PRIORITY_CLASS
    else: os.nice(-20)
    print(Fore.YELLOW + "  Process priority:\t\t" + Fore.RESET + str(p.nice()))

    # patch a bug when Python 3/MP4
    #if sys.version_info >= (3, 0) : #and (args.output_type == "m4a" or args.output_type == "alac.m4a")
    #    patch_bug_in_mutagen()
        
    recorder = SportifyRecorder(args)
    recorder.run() # Start Recording thread

    # try to listen for terminal resize events
    # (needs to be called on main thread)
    if not args.has_log:
        recorder.progress.handle_resize()
        if platform.system() == 'Linux': signal.signal(signal.SIGWINCH, recorder.progress.handle_resize)

    def hasStdinData():
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def abort(set_logged_in=False):
        recorder.abort_rip()
        if set_logged_in:
            recorder.recorder_continue.set()
        #recorder.join()
        sys.exit(1)

    # check if we were passed a file name or search, or skip check if passed a playlist
    def check_uri_args():
        if args.playlist: return
        if len(args.uri) == 1 and path_exists(args.uri[0]):
            encoding = "ascii" if args.ascii else "utf-8"
            args.uri = [line.strip() for line in
                codecs.open(enc_str(args.uri[0]), 'r', encoding)
                if not line.strip().startswith("#") and len(line.strip()) > 0]
        elif len(args.uri) == 1 and not args.uri[0].startswith("spotify:"):
            args.uri = [list(recorder.search_query(args.uri[0]))]

    # login and uri_parse on main thread to catch any KeyboardInterrupt
    '''
    try:
        if not recorder.login():
            print(Fore.RED + "Encountered issue while logging into Spotify, aborting..." + Fore.RESET)
            abort(set_logged_in=True)
        else:
            check_uri_args()
            recorder.recorder_continue.set()

    except (KeyboardInterrupt, Exception) as e:
        if not isinstance(e, KeyboardInterrupt):
            print(str(e))
        print("\n" + Fore.RED + "Aborting..." + Fore.RESET)
        abort(set_logged_in=True)

    # wait for ripping thread to finish
    #if not args.has_log: stdin_settings = termios.tcgetattr(sys.stdin)
    try:
        #if not args.has_log: tty.setcbreak(sys.stdin.fileno())
        while recorder.isA_aive():
            schedule.run_pending()

            # check if the escape button was pressed
            if not args.has_log and hasStdinData():
                c = sys.stdin.read(1)
                if c == '\x1b':
                    skip()
            recorder.join(0.1)
    except (KeyboardInterrupt, Exception) as e:
        if not isinstance(e, KeyboardInterrupt):
            print(str(e))
        print("\n" + Fore.RED + "Aborting..." + Fore.RESET)
        abort()
    finally:
        if not args.has_log:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, stdin_settings)
    '''

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "Keyboard interrupt, aborting..." + Fore.RESET)
        try: sys.exit(0)
        except SystemExit: os._exit(0)