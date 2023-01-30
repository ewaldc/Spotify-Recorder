# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from colorama import Fore
from lib.utils import *
import spotipy
from spotipy.oauth2 import SpotifyOAuth
#import spotipy.client
#import spotipy.util as util
import os, time
import requests, json
import csv
import re

SPOFITY_WEB_API_SCOPE = ' '.join([
    'playlist-read-private',
    'playlist-read-collaborative',
    'playlist-modify-public',
    'playlist-modify-private',
    'user-follow-read',
    'user-library-read',
    'user-read-private',
    'user-read-email',
    'user-read-playback-state',
    'user-modify-playback-state',
    'user-read-currently-playing'
    #'user-library-modify',
    #'user-top-read',
    #'user-follow-modify',
])

class WebAPI(object):
    def __init__(self, args, recorder):
        def getEnvironmentVariable(name):
            try: _value = os.environ[name]
            except: 
                print(Fore.RED + name + " is missing from .env file" + Fore.RESET);
                sys.exit(3)
            return _value
        self.args = args
        self.recorder = recorder
        self.cache = {
            "artist_albums": {},
            "album_artists": {},
            "genres": {},
            "charts": {},
            "coverart": {},
            "tracks": {}
		}
        self.client_id = getEnvironmentVariable("SPOTIPY_CLIENT_ID")
        self.client_secret = getEnvironmentVariable("SPOTIPY_CLIENT_SECRET")
        self.redirect_uri = getEnvironmentVariable("SPOTIPY_REDIRECT_URI")
        cache_location = os.path.join(recorder.cache_location, 'spotipy_token.cache')
        self.cache_handler = spotipy.cache_handler.CacheFileHandler(cache_location)
        self.use_token_cache = True
        self.login()
        self.valid_countries = self.spotify.available_markets()['markets']
        self.spotify.trace = False
        self.device_id = None
        system_name = os.environ['COMPUTERNAME']
        
        def is_none(device):
            if device is None or not device: 
                print(Fore.RED + "No Spotify device found for this system. Is Spotify Player running ?" + Fore.RESET)
                sys.exit(1)
        
        devices = self.spotify.devices()
        #devices = self.get_devices()
        is_none(devices)
        #for device in self.get_devices()["devices"]: #self.spotify.devices():
        if args.debug: print(Fore.MAGENTA + "Parsing the list of Spotify devices" + Fore.RESET)
        for device in devices["devices"]: #self.spotify.devices():
            if args.debug: print(Fore.MAGENTA + "Device name - type - id: " + device["name"] + \
                " - " + device["type"] + " - " + device["id"] + Fore.RESET)
            if device["name"] == system_name: 
                if args.debug: print(Fore.MAGENTA + "Device matches system name --> select this device" + Fore.RESET)
                self.device_id = device["id"]; break
        is_none(self.device_id)
        self.spotify.volume(100, device_id=self.device_id)

    def get_token(self):
        if int(time.time()) > self.token['expires_at']:
            self.token = self.auth_manager.refresh_access_token(self.token["refresh_token"])
        return self.token['access_token']

    def login(self, use_token_cache = True):
        if self.use_token_cache:
            self.auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=self.cache_handler, scope=SPOFITY_WEB_API_SCOPE)
            self.token = self.auth_manager.get_access_token(check_cache=True)
            if not self.auth_manager.validate_token(self.token): 
                self.token = self.auth_manager.refresh_access_token(self.token["refresh_token"])
        else:
            self.auth_manager = spotipy.oauth2.SpotifyOAuth(self.client_id, self.client_secret, self.redirect_uri, scope=SPOFITY_WEB_API_SCOPE, cache_handler=self.cache_handler)
            self.token = self.auth_manager.get_access_token(check_cache=False)
        #if request.args.get("code"):
           # Step 2. Being redirected from Spotify auth page
            #auth_manager.get_token(request.args.get("code"))
        
        # Step 3. Signed in, display data
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)
        
    def cache_result(self, name, key, result):
        self.cache[name][key] = result

    def get_cached_result(self, name, key):
        return self.cache[name].get(key)

    def request_json(self, url, msg):
        res = self.request_url(url, msg)
        return res.json() if res is not None else res

    def request_url(self, url, msg):
        #print(Fore.GREEN + "Attempting to retrieve " + msg + " from Spotify's Web API" + Fore.RESET)
        #print(Fore.CYAN + url + Fore.RESET)
        res = requests.get(url, headers = {'Content-Type':'application/json', \
              'Authorization': 'Bearer {}'.format(self.get_token())})
        if res.status_code == 200: return res
        else:
            print(Fore.RED + "URL returned non-200 HTTP code: " + str(res.status_code) + Fore.RESET)
            sys.exit(10)
        return None

    def api_url(self, url_path):
        return 'https://api.spotify.com/v1/' + url_path

    def charts_url(self, url_path):
        return 'https://spotifycharts.com/' + url_path

    def get_user(self, user):
        if user is None: return self.spotify.current_user()
        else: return self.spotify.user(user)

    def get_devices(self):
        return self.request_json(self.api_url('me/player/devices'), "devices")

    def is_playing(self):
        res = self.request_json(self.api_url('me/player'), "is_playing")
        return res["is_playing"]

    def get_track_info(self, id):
        # check for cached result
        cached_result = self.get_cached_result("tracks", id)
        if cached_result is not None: return cached_result
        track = self.spotify.track(id, self.recorder.country)

        self.cache_result("tracks", id, track)
        return track

    # Artist albums
    def get_artist_albums(self, id):
        args = self.args
        #album_type = ('&album_type=' + args.artist_album_type) if args.artist_album_type is not None else ""
        #market = ('&market=' + args.artist_album_market) if args.artist_album_market is not None else ""

        def get_albums_json(offset):
            #url = self.api_url('artists/' + id + '/albums/?=' + album_type + market + '&limit=50&offset=' + str(offset))
            url = self.api_url('artists/' + id + '/albums/?limit=50&offset=' + str(offset))
            return self.request_json(url, "albums")

        # check for cached result
        cached_result = self.get_cached_result("artist_albums", id)
        if cached_result is not None: return cached_result

        # extract artist id from uri
        #uri_tokens = uri.split(':'); if len(uri_tokens) != 3: return []

        # it is possible we won't get all the albums on the first request
        offset = 0
        album_ids = []
        total = None
        while total is None or offset < total:
            try: # rate limit if not first request
                if total is not None: time.sleep(1.0)
                albums = get_albums_json(offset)
                if albums is None: break

                # extract album URIs
                for album in albums['items']: album_ids.append(album['id']) 
                offset = len(album_ids)
                if total is None: total = albums['total']
            except KeyError as e: break
        if albums is not None: print(Fore.YELLOW + "Getting all (" + str(len(album_ids)) + 
            ") albums from artist \"" + albums['items'][0]["artists"][0]["name"] + "\"")
        self.cache_result("artist_albums", id, album_ids)
        return album_ids

    def get_playlist_by_name(self, name, user):
        offset = 0; count = 1
        while offset < count:
            url = self.api_url('users/' + user + '/playlists?limit=50&offset=' + str(offset))
            res = self.request_json(url, "user's playlists")
            if offset == 0: count = res['total']
            for playlist in res['items']:
                 if playlist['name'] == name:
                    print(Fore.GREEN + "Playlist with name " + name + " found: " + playlist["uri"] + Fore.RESET)
                    self.recorder.playlist = playlist
                    self.recorder.playlist_name = name
                    self.recorder.playlist_owner = playlist['owner']['display_name']
                    return playlist
            offset += 50
        print(Fore.RED + "Playlist with name " + name + " not found" + Fore.RESET)
        return None

    '''
    def get_saved_tracks(self):
        tracks = self.spotify.current_user_saved_tracks()
        count = tracks['total']
        tracks_ids = []
        for offset in range(0, count, 50):
            tracks = self.spotify.current_user_saved_tracks(limit=50,offset=offset)
            tracks_ids += [track['track']['id'] for track in tracks['items']]
        return tracks_ids
    '''
    def search_tracks(self, pattern):
        url = self.api_url('search?q=' + pattern + '&type=track&limit=1&offset=0')
        return self.request_json(url, "search track by track name and artist name")

    def get_album_tracks(self, id):
        url = self.api_url('albums/' + id)
        res = self.request_json(url, "album name, track count and tracks")
        self.recorder.album_name = res['name']
        count = res['total_tracks']
        print(Fore.YELLOW + "Album name: " + self.recorder.album_name + 
                ", released " + res['release_date'] + ", containing " + str(count) + " tracks(s)" + Fore.RESET)
        return [track['id'] for track in res['tracks']['items']]

    def get_playlist_tracks(self, id):
        def get_playlist_name_and_count_json(playlist_id):
            url = self.api_url('playlists/' + playlist_id + "?fields=name, owner.display_name, tracks.total")
            res = self.request_json(url, "playlist name and track count")
            self.recorder.playlist_name = res['name']
            self.recorder.playlist_owner = res['owner']["display_name"]
            count = res['tracks']['total']
            print(Fore.YELLOW + "Playlist name: " + self.recorder.playlist_name + 
                  " owned by " + self.recorder.playlist_owner + " with " + str(count) + " tracks(s)" + Fore.RESET)
            return count
        
        def get_playlist_tracks_json(playlist_id, offset):
            #url = self.api_url('playlists/' + playlist_id + '/tracks?fields=items(track(uri))&limit=100&offset=' + str(offset)) # Just get URI's
            url = self.api_url('playlists/' + playlist_id + '/tracks?limit=100&offset=' + str(offset))
            return self.request_json(url, "playlist")

        self.playlist_track_count = get_playlist_name_and_count_json(id)

        playlist_tracks = []
        print_str("Progress: ")
        for offset in range(0, self.playlist_track_count, 100):
            playlist = get_playlist_tracks_json(id, offset)
            print_str(str(offset) + " ")
            for track in playlist['items']:
                _track = track['track']
                _id = _track['id']
                playlist_tracks += [_id]
                self.cache_result("tracks", _id, _track)
        print(str(self.playlist_track_count) + " Done")
        return playlist_tracks
    
    def get_album_artists(self, uri):
        def get_album_json(album_id):
            url = self.api_url('albums/' + album_id)
            return self.request_json(url, "album")

        # check for cached result
        cached_result = self.get_cached_result("album_artists", uri)
        if cached_result is not None:
            return cached_result

        # extract album id from uri
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 3: return None

        album = get_album_json(uri_tokens[2])
        if album is None: return None

        result = [artist['name'] for artist in album['artists']]
        self.cache_result("album_artists", uri, result)
        return result

    # genre_type can be "artist" or "album"
    def get_genres(self, genre_type, track):
        def get_genre_json(id):
            url = self.api_url(genre_type + 's/' + id)
            return self.request_json(url, "genres")

        # extract album/artist id from track
        id = track['artists'][0]['id'] if genre_type == "artist" else track['album']['id']
        cached_result = self.get_cached_result("genres", id)    # check for cached result
        if cached_result is not None: return cached_result

        json_obj = get_genre_json(id)
        if json_obj is None: return None

        result = json_obj["genres"]
        self.cache_result("genres", id, result)
        return result

    # doesn't seem to be officially supported by Spotify
    def get_charts(self, uri):
        def get_chart_tracks(metrics, region, time_window, from_date):
            url = self.charts_url(metrics + "/" + region + "/" + time_window +
                "/" + from_date + "/download")

            res = self.request_url(url, region + " " + metrics + " charts")
            if res is not None:
                csv_items = [enc_str(to_ascii(r)) for r in res.text.split("\n")]
                reader = csv.DictReader(csv_items)
                return ["spotify:track:" + row["URL"].split("/")[-1] for row in reader]
            else: return []

        # check for cached result
        cached_result = self.get_cached_result("charts", uri)
        if cached_result is not None: return cached_result

        # spotify:charts:metric:region:time_window:date
        uri_tokens = uri.split(':')
        if len(uri_tokens) != 6: return None

        # some sanity checking
        valid_metrics = {"regional", "viral"}
        valid_windows = {"daily", "weekly"}

        def sanity_check(val, valid_set):
            if val not in valid_set:
                print(Fore.YELLOW + "Not a valid Spotify charts URI parameter: " + val + Fore.RESET)
                print("Valid parameter options are: [" + ", ".join(valid_set)) + "]"
                return False
            return True

        def sanity_check_date(val):
            if  re.match(r"^\d{4}-\d{2}-\d{2}$", val) is None and val != "latest":
                print(Fore.YELLOW + "Not a valid Spotify charts URI parameter: " + val + Fore.RESET)
                print("Valid parameter options are: ['latest', a date (e.g. 2016-01-21)]")
                return False
            return True

        check_results = sanity_check(uri_tokens[2], valid_metrics) and \
            sanity_check(uri_tokens[3], self.valid_countries) and \
            sanity_check(uri_tokens[4], valid_windows) and \
            sanity_check_date(uri_tokens[5])
        if not check_results:
            print("Generally, a charts URI follow the pattern spotify:charts:metric:region:time_window:date")
            return None

        tracks_obj = get_chart_tracks(uri_tokens[2], uri_tokens[3], uri_tokens[4], uri_tokens[5])
        charts_obj = {
            "metrics": uri_tokens[2],
            "region": uri_tokens[3],
            "time_window": uri_tokens[4],
            "from_date": uri_tokens[5],
            "tracks": tracks_obj
        }

        self.cache_result("charts", uri, charts_obj)
        return charts_obj

    def start_playback(self, device_id = None, context_uri = None, uris = None, offset = None, position_ms = None):
        try: 
            url = self.api_url('me/player/play?device_id=' + self.device_id)
            res = requests.put(url, headers = {'Content-Type':'application/json', 'Accept':'application/json',\
              'Authorization': 'Bearer {}'.format(self.get_token())}, data=json.dumps({'uris': uris}))
            time.sleep(1)   # Sleep 1 second, otherwise is_playing miht be False (needs 1 second play time)
            return True if self.is_playing() else False
        except:
            print(Fore.RED + "Start Playback: Spotify Player not available, aborting..." + Fore.RESET)
            sys.exit(4)
        
    def stop_playback(self, device_id=None):
        try: return self.spotify.pause_playback(device_id)
        except:
            print(Fore.RED + "Stop Playback: Spotify Player not available, aborting..." + Fore.RESET)
            sys.exit(5)

    def get_coverart(self, track, cover_size_idx):
        def get_track(track_id):
            url = self.api_url('tracks/' + track_id)
            return self.request_json(url, "track")
            #results = self.spotify.track(track_id)
            if results: return results['track']
                #return track['album']['images'][0]['url']
            else: return None

        def get_image_data(url):
            response = self.request_url(url, "cover art")
            if response: return response.content
            else: return None
            
        try:
            image = track['album']['images'][cover_size_idx]
        except KeyError:
            return None

        url = image["url"]
        # check for cached result
        cached_result = self.get_cached_result("coverart", url)
        if cached_result is not None: return cached_result

        image_data = get_image_data(url)
        self.cache_result("coverart", url, image_data)
        return image_data

