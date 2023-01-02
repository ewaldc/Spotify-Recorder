# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from colorama import Fore
from lib.utils import *
import os, time
#import spotify
import codecs
import shutil


class PostActions(object):
    tracks_to_remove = []
    fail_log_file = None
    success_tracks = []
    failure_tracks = []

    def __init__(self, args, recorder):
        self.args = args
        self.recorder = recorder

        # create a log file for recording failures
        if args.fail_log is not None:
            _base_dir = base_dir()
            if not path_exists(_base_dir):
                os.makedirs(enc_str(_base_dir))

            encoding = "ascii" if args.ascii else "utf-8"
            self.fail_log_file = codecs.open(
                enc_str(os.path.join(_base_dir, args.fail_log)),
                'w', encoding)

    def log_success(self, track):
        self.success_tracks.append(track)

    def log_failure(self, track):
        self.failure_tracks.append(track)
        if self.fail_log_file is not None:
            self.fail_log_file.write(track.link.uri + "\n")

    def end_failure_log(self):
        if self.fail_log_file is not None:
            file_name = self.fail_log_file.name
            self.fail_log_file.flush()
            os.fsync(self.fail_log_file.fileno())
            self.fail_log_file.close()
            self.fail_log_file = None

            if os.path.getsize(enc_str(file_name)) == 0:
                rm_file(file_name)

    def print_summary(self):
        if len(self.success_tracks) + len(self.failure_tracks) <= 1: return

        def print_with_bullet(_str):
            if self.args.ascii: print(" * " + _str)
            else: print(" • " + _str)

        def log_tracks(tracks):
            for track in tracks:
                if (len(track["artists"]) > 0 and track["artists"][0]["name"] is not None and track["name"] is not None):
                    print_with_bullet(track["artists"][0]["name"] + " - " + track["name"])
                else: print_with_bullet(track["uri"])
            print("")

        if len(self.success_tracks) > 0:
            print(Fore.GREEN + "\nSuccess Summary (" + str(len(self.success_tracks)) + ")\n" + ("-" * 79) + Fore.RESET)
            log_tracks(self.success_tracks)
        if len(self.failure_tracks) > 0:
            print(Fore.RED + "\nFailure Summary (" + str(len(self.failure_tracks)) + ")\n" + ("-" * 79) + Fore.RESET)
            log_tracks(self.failure_tracks)

    def get_chart_name(self, chart):
        country_mapping = {
            "global": "Global",
            "us": "United States",
            "gb": "United Kingdom",
            "ad": "Andorra",
            "ar": "Argentina",
            "at": "Austria",
            "au": "Australia",
            "be": "Belgium",
            "bg": "Bulgaria",
            "bo": "Bolivia",
            "br": "Brazil",
            "ca": "Canada",
            "ch": "Switzerland",
            "cl": "Chile",
            "co": "Colombia",
            "cr": "Costa Rica",
            "cy": "Cyprus",
            "cz": "Czech Republic",
            "de": "Germany",
            "dk": "Denmark",
            "do": "Dominican Republic",
            "ec": "Ecuador",
            "ee": "Estonia",
            "es": "Spain",
            "fi": "Finland",
            "fr": "France",
            "gr": "Greece",
            "gt": "Guatemala",
            "hk": "Hong Kong",
            "hn": "Honduras",
            "hu": "Hungary",
            "id": "Indonesia",
            "ie": "Ireland",
            "is": "Iceland",
            "it": "Italy",
            "lt": "Lithuania",
            "lu": "Luxembourg",
            "lv": "Latvia",
            "mt": "Malta",
            "mx": "Mexico",
            "my": "Malaysia",
            "ni": "Nicaragua",
            "nl": "Netherlands",
            "no": "Norway",
            "nz": "New Zealand",
            "pa": "Panama",
            "pe": "Peru",
            "ph": "Philippines",
            "pl": "Poland",
            "pt": "Portugal",
            "py": "Paraguay",
            "se": "Sweden",
            "sg": "Singapore",
            "sk": "Slovakia",
            "sv": "El Salvador",
            "tr": "Turkey",
            "tw": "Taiwan",
            "uy": "Uruguay"
        }
        return (chart["time_window"].title() + " " +
                country_mapping.get(chart["region"], "") + " " +
                ("Top" if chart["metrics"] == "regional" else "Viral") + " " +
                ("200" if chart["metrics"] == "regional" else "50"))

    def get_playlist_name(self):
        recorder = self.recorder
        if recorder.current_playlist is not None:
            return recorder.current_playlist["name"]
        elif recorder.current_album is not None:
            return (recorder.current_album["artist"]["name"] + " - " + recorder.current_album["name"])
        elif recorder.current_chart is not None:
            return self.get_chart_name(recorder.current_chart)
        else: return None

    def get_playlist_path(self, name, ext):
        ext = "." + ext

        if self.args.playlist_directory is not None:
            playlist_dir = self.args.playlist_directory

            # check to see if we were passed in a playlist filename
            if playlist_dir.endswith(ext):
                playlist_file = playlist_dir
                playlist_dir = os.path.dirname(playlist_dir)
            else: playlist_file = to_ascii(os.path.join(playlist_dir, name + ext))

            # ensure path exists
            if not os.path.exists(playlist_dir): os.makedirs(playlist_dir)
            return playlist_file
        else: return to_ascii(os.path.join(base_dir(), name + ext))

    def get_playlist_file_path(self, _file, playlist_relative_path):
        _base_dir = base_dir()
        if "absolute" in self.args.playlist_create: return _file #os.path.join(_base_dir, _file)
        else:
            _basename = os.path.basename(_file)
            if self.args.playlist_relative_path: return os.path.join(playlist_relative_path, _basename)
            try: return os.path.relpath(_file, _base_dir) # Will fail for file on different mount points/drives
            except (Exception) as e: 
                return os.path.splitdrive(_file)[1]  # Split off drive name

    def create_playlist_m3u(self, tracks, ext):
        args = self.args
        recorder = self.recorder

        name = self.get_playlist_name()
        if name is not None and args.playlist_create.startswith("m3u"):
            name = sanitize_playlist_name(to_ascii(name)) + "_" + ext
            playlist_path = self.get_playlist_path(name, "m3u")

            print(Fore.GREEN + "Creating playlist m3u file " + playlist_path + Fore.RESET)

            encoding = "ascii" if args.ascii else "utf-8"
            with codecs.open(enc_str(playlist_path), 'w', encoding) as playlist:
                for idx, track in enumerate(tracks):
                    _file = recorder.format_track_path(idx, track, ext)
                    playlist_relative_path = format_track_string(recorder, self.args.playlist_relative_path.strip(), idx, track, ext) \
                        if self.args.playlist_relative_path else None
                    if path_exists(_file): playlist.write(self.get_playlist_file_path(_file, playlist_relative_path) + "\n")

    def create_playlist_wpl(self, tracks, ext):
        args = self.args
        recorder = self.recorder

        name = self.get_playlist_name()
        if name is not None and args.playlist_create.startswith("wpl"):
            name = sanitize_playlist_name(to_ascii(name))
            playlist_path = self.get_playlist_path(name, "wpl")
            print(Fore.GREEN + "Creating playlist wpl file " + playlist_path + Fore.RESET)

            encoding = "ascii" if args.ascii else "utf-8"
            with codecs.open(enc_str(playlist_path), 'w', encoding) as playlist:
                # to get an accurate track count
                track_paths = []
                for idx, track in enumerate(tracks):
                    _file = recorder.format_track_path(idx, track)
                    if path_exists(_file): track_paths.append(_file)

                playlist.write('<?wpl version="1.0"?>\n')
                playlist.write('<smil>\n')
                playlist.write('\t<head>\n')
                playlist.write('\t\t<meta name="Generator content="Microsoft Windows Media Player -- 12.0.7601.18526"/>\n')
                playlist.write('\t\t<meta name="ItemCount" content="' + str(len(track_paths)) + '"/>\n')
                playlist.write('\t\t<author>' + recorder.session.user.display_name + '</author>\n')
                playlist.write('\t\t<title>' + name + '</title>\n')
                playlist.write('\t</head>\n')
                playlist.write('\t<body>\n')
                playlist.write('\t\t<seq>\n')
                for _file in track_paths:
                    _file.replace("&", "&amp;")
                    _file.replace("'", "&apos;")
                    playlist.write('\t\t\t<media src="' + self.get_playlist_file_path(_file) + "\"/>\n")
                playlist.write('\t\t</seq>\n')
                playlist.write('\t</body>\n')
                playlist.write('</smil>\n')

    def queue_remove_from_playlist(self, idx):
        recorder = self.recorder
        if self.args.remove_from_playlist:
            if recorder.current_playlist:
                if recorder.current_playlist.owner.canonical_name == recorder.session.user.canonical_name:
                    self.tracks_to_remove.append(idx)
                else:
                    print(Fore.RED + "This track will not be removed from playlist " + recorder.current_playlist.name + " since " +
                          recorder.session.user.canonical_name + " is not the playlist owner..." + Fore.RESET)
            else: print(Fore.RED + "No playlist specified to remove this track from. Did you use '-r' without a playlist link?" + Fore.RESET)

    '''
    def clean_up_partial(self):
        recorder = self.recorder

        if recorder.audio_file is not None and path_exists(recorder.audio_file):
            print(Fore.YELLOW + "Deleting partially recorded file" + Fore.RESET)
            rm_file(recorder.audio_file)

            # check for any extra pcm or wav files
            def delete_extra_file(ext):
                audio_file = change_file_extension(recorder.audio_file, ext)
                if path_exists(audio_file): rm_file(audio_file)
            if self.args.plus_wav: delete_extra_file("wav")
            if self.args.plus_pcm: delete_extra_file("pcm")
    '''

    def remove_tracks_from_playlist(self):
        recorder = self.recorder
        if self.args.remove_from_playlist and recorder.current_playlist and len(self.tracks_to_remove) > 0:
            print(Fore.YELLOW + "Removing successfully recorded tracks from playlist " +
                  recorder.current_playlist.name + "..." + Fore.RESET)
            recorder.current_playlist.remove_tracks(self.tracks_to_remove)
            while recorder.current_playlist.has_pending_changes: time.sleep(0.1)

    def remove_offline_cache(self):
        recorder = self.recorder
        if self.args.remove_offline_cache:
            if self.args.settings is not None: storage_path = norm_path(self.args.settings)
            else: storage_path = default_settings_dir()

            storage_path = os.path.join(storage_path, "Storage")
            if path_exists(storage_path): shutil.rmtree(enc_str(storage_path))
