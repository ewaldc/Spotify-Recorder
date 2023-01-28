# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from subprocess import Popen, PIPE
from colorama import Fore, Style
from lib.utils import *
from lib.tags import set_metadata_tags
from lib.progress import Progress
from lib.post_actions import PostActions
from lib.web import WebAPI
from lib.encode import encode
#from audio_recorder import AudioRecorder
from lib.pyaudio_recorder import AudioRecorder
import pyaudiowpatch as pyaudio
from lib.sync import Sync
from datetime import datetime
import os, sys, traceback, threading, re, glob, shutil
from pathlib import Path
import select
import tempfile

recording_format = {
    "PCM:8":pyaudio.paInt8, "PCM:16":pyaudio.paInt16, "PCM:24":pyaudio.paInt24, "PCM:32":pyaudio.paInt32, "IEEE_FLOAT":pyaudio.paFloat32
}

'''
def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper
'''

class SportifyRecorder(threading.Thread):
    progress = None
    sync = None
    post = None
    web = None
    dev_null = None
    abort = False

    def __init__(self, args):
        #threading.Thread.__init__(self)

        # initialize progress meter
        self.progress = Progress(args, self)
        self.args = args

        # settings directory
        default_dir = default_settings_dir()
        if args.settings is not None:
            settings_dir = norm_path(args.settings)
            self.settings_location = settings_dir
            self.cache_location = settings_dir
        else:
            self.settings_location = default_dir
            self.cache_location = default_dir

        self.post = PostActions(args, self)
        self.web = WebAPI(args, self)
        self.user = self.web.get_user(None)
        self.country = self.user["country"]
        self.audio_recorder = AudioRecorder(self, pyaudio.PyAudio(), recording_format[args.recording_format])
        
        proxy = os.environ.get('http_proxy')
        if proxy is not None: self.config.proxy = proxy

    def run(self):
        # Encoding and tagging thread function
        def encode_and_tag(encoder, ext, output_file, audio_file, track_info, idx):
            print(Fore.YELLOW + "Encoding " + Fore.CYAN + output_file + Fore.YELLOW + " (" + encoder + ")" + Fore.RESET)
            encode(args, encoder, audio_file.replace(os.sep, '/'), output_file)
            set_metadata_tags(self, output_file, idx, track_info, encoder, ext)

        args = self.args
        uris = args.uri        # list of spotify URIs
               
        # if uris is a playlist, substitute for list of tracks
        self.playlist = None
        self.playlist_name = None
        self.playlist_owner = None
        #if ":playlist:" in uris[0]: uris = self.web.get_playlist_tracks(self, uris[0])
        # check fo playlist by name option
        #if args.playlist: user_id = self.user['id'] if args.playlist_user is None else args.playlist_user
        if args.playlist: 
            user_id = self.user['id']
            self.playlist = self.web.get_playlist_by_name(uris[0], user_id)
            uris = [self.playlist['uri']]

        # calculate total size and time
        track_info_list = []
        threads = []
        self.show_total = True

        print("Assemble list of tracks to record (can take minutes for large playlists)")
        for uri in uris:
            tracks = self.get_tracks_from_uri(uri)
            for idx, track in enumerate(tracks):
                track_info = self.web.get_track_info(track)
                if is_unavailable(self.country, track_info):
                    name = track_info["artists"][0]["name"] + '-' + track_info["name"]
                    print(Fore.RED + 'Track is not available - skipping: ' + Fore.CYAN + name + Fore.RESET)
                    self.post.log_failure(track_info)
                    self.progress.skipped_tracks += 1
                    continue
                track_info_list.append(track_info)

                duration_ms = track_info['duration_ms']
                self.progress.calc_total(duration_ms)

        if self.progress.total_size > 0:
            print("Total Estimated Uncompressed Audio Size (PCM - " + args.recording_format + "): " + format_size(self.progress.total_size))
            print("Total Estimated Recording time (HH:MM:SS): " + format_time(self.progress.total_duration / 1000))

        # Create temporary directory
        #dir = tempfile.TemporaryDirectory(suffix=".wav")
        dir = tempfile.gettempdir()

        # reording loop
        for idx, track_info in enumerate(track_info_list):
            if self.abort: break
            track_duration_ms = track_info["duration_ms"]
            track_uri = track_info["uri"]
            
            #if args.playlist_sync and self.current_playlist:
            #     self.sync = Sync(args, self)
            #     self.sync.sync_playlist(self.current_playlist)

            try:
                self.progress.increment_track_idx()                #self.check_stop_time()
                record_track = True
                encode_track = True  
                track_name = get_track_name(track_info)
                artist_name = get_track_artist(track_info)
                if not track_name or not artist_name:
                    print(Fore.RED + 'Spotify track (' + track_uri +' ) is invalid, skipping' + Fore.RESET)
                    continue

                audio_file = os.path.join(dir, artist_name + " - " + track_name + ".wav")  #dir.name
                for encoder in args.encode:
                    # Wait for all of them to finish
                    ext = get_ext(self.args, encoder)
                    output_file = self.format_track_path(idx, track_info, ext)

                    # before we skip or can fail loading the track
                    if not args.overwrite and (path_exists(output_file) or path_exists(get_alternative_file(output_file, track_info, ext))):
                        if is_partial(output_file, track_duration_ms, alt_output_file): 
                            print(Fore.YELLOW + "\"" + encoder + "\" encoder: Partial encoding found - overwriting: " + Fore.CYAN + output_file + Fore.RESET)
                            os.remove(output_file)
                        else:
                            print(Fore.GREEN + "\"" + encoder + "\" encoder: Complete encoding found for " + Fore.CYAN + output_file + Fore.RESET)
                            if args.tags["action"] == "update": # update id3v2 with metadata and embed front cover image
                                set_metadata_tags(args, output_file, idx, track_info, self, encoder, ext)
                            continue # next encoder
                    if args.search:
                        search_dir = format_track_string(self, args.search.strip(), idx, track_info, ext)
                        pattern = search_dir + '/**/' + os.path.basename(output_file)
                        files = glob.glob(search_dir + '/**/' + os.path.basename(output_file), recursive=True)
                        if len(files) > 0:
                            try: # First try symbolic links
                                os.symlink(files[0].replace(os.sep, '/'), output_file, True)
                            except (Exception) as e: # With insufficient permission, just copy
                                shutil.copy2(files[0].replace(os.sep, '/'), output_file, follow_symlinks=True)
                            continue
                        
                    if record_track:
                        if not path_exists(audio_file) or is_partial(audio_file, track_duration_ms):
                            if args.recording == "skip":  continue  # We have a missing or incomplete file but can't record -> skip 
                            try: 
                                #os.remove(audio_file)
                                os.rename(audio_file, audio_file + ".old") 
                                print(Fore.YELLOW + 'Found incomplete raw recording from previous session - removing' + Fore.RESET)
                            except OSError: pass
                            sys.stdout.write(Fore.GREEN + '\nRecording Track "' + track_name + '" by "' +
                                artist_name + '" (' + track_uri + ') ... ' + Fore.RESET)
                            # Start recording
                            self.audio_recorder.start_recording(audio_file)
                            if self.web.start_playback(uris=[track_uri]):
                                self.audio_recorder.stop_recording(track_duration_ms / 1000.0)
                                self.post.log_success(track_info) 
                                print(Fore.GREEN + 'recording complete' + Fore.RESET)
                            else: # track can not be played
                                self.audio_recorder.stop_recording(0)
                                encode_track = False
                                self.post.log_failure(track_info)
                                print(Fore.RED + 'recording failed - track can not be played' + Fore.RESET)
                        else: print(Fore.GREEN + 'Found complete raw recording from previous session - reusing' + Fore.RESET)
                        record_track = False # No need to record more than once

                    if encode_track:
                        t = threading.Thread(target=encode_and_tag, args=(encoder, ext, output_file, audio_file, track_info, idx))
                        threads.append(t)
                        t.start()

                # Increment skipped tracks when no recording required for every single encoder
                if record_track:
                    msg = ' or missing raw recording with recording set to "skip"' if args.recording == "skip" else ''
                    print(Fore.YELLOW + 'Skipping ' + track_uri + ' - complete audio files found for all encoders' + msg + Fore.RESET)
                    self.progress.skipped_tracks += 1

                # update id3v2 with metadata and embed front cover image
                #set_metadata_tags(args, self.audio_file, idx, track, self)

                # make a note of the index and remove all the
                # tracks from the playlist when everything is done
                #self.post.queue_remove_from_playlist(idx)
                # finally log success

            except (Exception) as e:
                sys.stdout.write(Fore.YELLOW + "skipping to next track\n" + Fore.RESET)
                if isinstance(e, Exception): print(Fore.RED + "Error detected" + Fore.RESET)
                print(str(e))
                traceback.print_exc()
                self.post.log_failure(track_info)
                #self.session.player.play(False)
                #self.post.clean_up_partial()
                continue

            for t in threads: t.join() # Wait for last threads to complete
            threads = []
            if args.recording != "keep" and not record_track: os.remove(audio_file)

            # actually removing the tracks from playlist
            #self.post.remove_tracks_from_playlist()

        # logout, we are done
        self.audio_recorder.terminate()

        # Create playlists
        if args.playlist_create:
            for encoder in args.encode:
                self.post.create_playlist(track_info_list, get_ext(self.args, encoder))

        self.post.end_failure_log()
        self.post.print_summary()
        #self.logout()
        #self.finished.set()

    def get_tracks_from_uri(self, uri):
        if type(uri) in (tuple, list): return uri

        if uri.startswith("spotify:artist:"): 
            #nested_list = [self.web.get_album_tracks(id) for id in self.web.get_artist_albums(uri[15:])]
            #return [tid for id in nested_list for tid in id]  #unpacking list comprehension
            _tracks = []  #unpacking list comprehension
            for id in self.web.get_artist_albums(uri[15:]): _tracks += self.web.get_album_tracks(id)
            return _tracks
        elif uri.startswith("spotify:track:"): return [uri[14:]]
        elif uri.startswith("spotify:playlist:"): return self.web.get_playlist_tracks(uri[17:])
        elif uri.startswith("spotify:album:"):  return self.web.get_album_tracks(uri[14:])
        else: return [] # invalid URI

    def format_track_path(self, idx, track_info, ext):
        args = self.args
        audio_file = format_track_string(self, args.filename.strip(), idx, track_info, ext)

        # in case the file name is too long
        def truncate(_str, max_size):
            return _str[:max_size].strip() if len(_str) > max_size else _str

        def truncate_dir_path(dir_path):
            path_tokens = dir_path.split(os.sep)
            path_tokens = [truncate(token, 255) for token in path_tokens]
            return os.sep.join(path_tokens)

        def truncate_file_name(file_name):
            tokens = file_name.rsplit(os.extsep, 1)
            if len(tokens) > 1:
                tokens[0] = truncate(tokens[0], 255 - len(tokens[1]) - 1)
            else: tokens[0] = truncate(tokens[0], 255)
            return os.extsep.join(tokens)

        # ensure each component in path is no more than 255 chars long
        if args.filename_windows_safe:
            tokens = audio_file.rsplit(os.sep, 1)
            if len(tokens) > 1:
                audio_file = os.path.join(truncate_dir_path(tokens[0]), truncate_file_name(tokens[1]))
            else: audio_file = truncate_file_name(tokens[0])

        # replace filename
        if args.filename_replace is not None: audio_file = self.replace_filename(audio_file, args.filename_replace)

        # remove not allowed characters in filename (windows)
        if args.filename_windows_safe: audio_file = re.sub('[:"*?<>|]', '', audio_file)

        # prepend base_dir
        #audio_file = to_ascii(os.path.join(base_dir(), audio_file))
        audio_file = os.path.join(base_dir(), audio_file)

        if args.normalized_ascii: audio_file = to_normalized_ascii(audio_file)

        # create directory if it doesn't exist
        audio_path = os.path.dirname(audio_file)
        if not path_exists(audio_path): 
            try: os.makedirs(enc_str(audio_path))
            except: 
                print(Fore.RED + "Failed to create file - exiting: " + Fore.RESET + audio_file)
                sys.exit(5)

        return audio_file

    def replace_filename(self, filename, pattern_list):
        for pattern in pattern_list:
            repl = pattern.split('/')
            filename = re.sub(repl[0], repl[1], filename)
        return filename
