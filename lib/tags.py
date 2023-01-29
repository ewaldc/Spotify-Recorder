# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from colorama import Fore, Style
from mutagen import mp3, id3, flac, aiff, oggvorbis, oggopus, aac
from lib.encode import encoder_default_args
from stat import ST_SIZE
from lib.utils import *
from datetime import datetime
import os, sys, traceback
import base64

global cover_size_list
cover_size_choices = ['large', 'medium',  'small']

def get_metadata_tags(recorder, audio_file, ext):
    def get_codec(audio):
        for mime in audio.mime:
            if "codecs=" in mime: return mime.split("codecs=")[1]
        return None

    def fix_metadata_tags(audio, track):
        _pattern = os.path.splitext(audio_file.split(os.sep)[-1])[0]
        _tracks = recorder.web.search_tracks(_pattern)
        print("Attempting to repair metadata")
        _codec = get_codec(audio)
        if _codec and _tracks['tracks'] and _tracks['tracks']['items']: set_metadata_tags(recorder, audio_file, 1, _tracks['tracks']['items'][0], _codec, ext)
        else: print(Fore.RED + "Failed to determine codec, repair failed" + Fore.RESET)

    def get_id3_tags(audio):
        track["name"] = audio['TIT2'].text[0]
        track["artist"][0]["name"] = audio['TPE1'].text[0]
        return track

    def get_vorbis_comments(audio):
        try:
            track["name"] = audio.tags["TITLE"][0]
            track['track_number'] = audio.tags["TRACKNUMBER"][0]
            track["artists"][0]["name"] =  audio.tags["ARTIST"][0]
            album['name'] = audio.tags["ALBUM"][0]
            album['release_date'] = audio.tags["DATE"][0]
            album["artists"][0]["name"] = audio.tags["ALBUMARTIST"][0]
        except:
            print(Fore.YELLOW + "\nKey metadata missing for audio file: " + Fore.CYAN + audio_file + Fore.RESET)
            #fix_metadata_tags(audio, track)
        return track

    track = {'name':'', 'uri':'', 'disc_number':'1', 'track_number':'1', 'artists':[{'name':''}], 
        'album':{'name':'', 'total_tracks':'1', 'release_date':'', 'release_date_precision':'year', 'artists':[{'name':''}]}
    }
    album = track['album']
    try:
        match ext:
            case "flac":
                audio = flac.FLAC(audio_file)
                return set_vorbis_comments(audio)
            case "aiff":
                audio = aiff.AIFF(audio_file)
                set_id3_tags(audio)
            case "ogg":
                audio = oggvorbis.OggVorbis(audio_file)
                return set_vorbis_comments(audio)
            case "opus":
                audio = oggopus.OggOpus(audio_file)
                return get_vorbis_comments(audio)
            case "aac":
                audio = aac.AAC(audio_file)
                set_id3_tags_raw(audio, audio_file)
            case "m4a":
                if sys.version_info >= (3, 0):
                    from mutagen import mp4
                    audio = mp4.MP4(audio_file)
                    set_mp4_tags(audio)
                else:
                    from mutagen import m4a, mp4
                    audio = m4a.M4A(audio_file)
                    set_m4a_tags(audio)
                    audio = mp4.MP4(audio_file)
            case "mp3":
                audio = mp3.MP3(audio_file, ID3=id3.ID3)
                return get_id3_tags(audio)
    except Exception as e:
        print(Fore.RED + "\nCorrupt metadata for aufio file: " + Fore.CYAN + audio_file + Fore.RESET)
        print(str(e))
        #traceback.print_exc()
        return track

def set_metadata_tags(recorder, audio_file, idx, track, codec, ext):
    def tag_to_ascii(_str):
        return _str if args.ascii_path_only else to_ascii(_str, on_error)
    
    def release_year(album):
        return album["release_date"] if (album["release_date_precision"] == "year") \
        else album["release_date"].split("-")[0]

    args = recorder.args
    # log completed file
    print(Fore.GREEN + Style.BRIGHT + os.path.basename(audio_file) + Style.NORMAL + "\t[ " +
          format_size(os.stat(enc_str(audio_file))[ST_SIZE]) + " ]" + Fore.RESET)

    #if ext == "wav": print(Fore.YELLOW + "Skipping metadata tagging for PCM (WAV) encoding..."); return

    # try to get genres from Spotify's Web API
    genres = None
    if args.genres is not None: genres = recorder.web.get_genres(args.genres, track)

    # use mutagen to update id3v2 tags and vorbis comments
    try:
        audio = None
        on_error = 'replace' if args.ascii_path_only else 'ignore'
        album = track['album']
        artists = track['artists']
        item = album['name']
        album_name = tag_to_ascii(album['name'])
        artists = tag_to_ascii(", ".join(artist['name'] for artist in artists) \
            if args.all_artists else artists[0]['name'])
        album_artist = tag_to_ascii(album['artists'][0]['name'])
        track_name = tag_to_ascii(track['name'])
        disc_number = track['disc_number']
        track_number = track['track_number']
        total_tracks = album['total_tracks']

        # the comment tag can be formatted
        comment = tag_to_ascii(format_track_string(recorder, args.tags["comment"], idx, track, ext)) if args.tags["comment"] else ""
            
        grouping = tag_to_ascii(format_track_string(recorder, args.tags["grouping"], idx, track, ext)) if args.tags["grouping"] else ""
        if genres is not None and genres and args.ascii_path_only:
            genres = [tag_to_ascii(genre) for genre in genres] if args.ascii_path_only else genres

        # cover art image
        image = recorder.web.get_coverart(track, cover_size_choices.index(args.tags["cover-size"]))

        def idx_of_total_str(_idx, _total):
            if _total > 0: return "%d/%d" % (_idx, _total)
            else: return "%d" % (_idx)

        def save_cover_image(embed_image_func):
            if image is not None:
                def write_image(file_name):
                    cover_path = os.path.dirname(audio_file)
                    cover_file = os.path.join(cover_path, file_name)
                    if not path_exists(cover_file):
                        with open(enc_str(cover_file), "wb") as f: f.write(image)
                _cover = args.tags["cover"]
                if _cover == 'embed': embed_image_func(image)
                else: write_image(_cover)


        def add_id3_tags(tags):
            def embed_image(data):
                tags.add(id3.APIC(encoding=3, mime='image/jpeg', type=3, desc='Front Cover', data=data))

            save_cover_image(embed_image)
            if album is not None: tags.add(id3.TALB(text=[album_name], encoding=3))
            tags.add(id3.TIT2(text=[track_name], encoding=3))
            tags.add(id3.TPE1(text=[artists], encoding=3))
            if album_artist is not None: tags.add(id3.TPE2(text=[album_artist], encoding=3))
            tags.add(id3.TDRC(text=[album['release_date']], encoding=3))
            tags.add(id3.TPOS(text=[disc_number], encoding=3))
            tags.add(id3.TRCK(text=[idx_of_total_str(track_number, total_tracks)], encoding=3))
            if comment: tags.add(id3.COMM(text=[comment], encoding=3))
            if grouping: tags.add(id3.TIT1(text=[grouping], encoding=3))
            if genres is not None and genres:
                tcon_tag = id3.TCON(encoding=3)
                tcon_tag.genres = genres
                tags.add(tcon_tag)

        def set_id3_tags(audio):
            # add ID3 tag if it doesn't exist
            try: audio.add_tags()
            except: pass
            add_id3_tags(audio.tags)
            if args.id3_v23:
                audio.tags.update_to_v23()
                audio.save(v2_version=3, v23_sep='/')
                audio.tags.version = (2, 3, 0)
            else:
                audio.save()

        # aac is not well supported
        def set_id3_tags_raw(audio, audio_file):
            try:
                id3_dict = id3.ID3(audio_file)
            except id3.ID3NoHeaderError:
                id3_dict = id3.ID3()
            add_id3_tags(id3_dict)
            if args.id3_v23:
                id3_dict.update_to_v23()
                id3_dict.save(audio_file, v2_version=3, v23_sep='/')
                id3_dict.version = (2, 3, 0)
            else:
                id3_dict.save(audio_file)
            audio.tags = id3_dict

        def set_vorbis_comments(audio):
            # add Vorbis comment block if it doesn't exist
            if audio.tags is None: audio.add_tags()

            def embed_image(data):
                pic = flac.Picture()
                pic.type = 3
                pic.mime = "image/jpeg"
                pic.desc = "Front Cover"
                pic.data = data

                if ext == "flac":
                    audio.clear_pictures()
                    audio.add_picture(pic)
                else:
                    data = base64.b64encode(pic.write())
                    audio["METADATA_BLOCK_PICTURE"] = [data.decode("ascii")]

            save_cover_image(embed_image)

            if album is not None: audio.tags["ALBUM"] = album_name
            audio.tags["TITLE"] = track_name
            audio.tags["ARTIST"] = artists
            if album_artist is not None: audio.tags["ALBUMARTIST"] = album_artist
            audio.tags["DATE"] = album['release_date']
            #audio.tags["YEAR"] = release_year(album)
            #audio.tags["DISCNUMBER"] = str(disc_number)
            #audio.tags["DISCTOTAL"] = str(num_discs)
            audio.tags["TRACKNUMBER"] = str(track_number)
            #audio.tags["TRACKTOTAL"] = str(total_tracks)
            if comment: audio.tags["COMMENT"] = comment
            if grouping: audio.tags["GROUPING"] = grouping
            if genres is not None and genres: audio.tags["GENRE"] = ", ".join(genres)

            audio.save()

        # only called by Python 3
        def set_mp4_tags(audio):
            # add MP4 tags if it doesn't exist
            if audio.tags is None: audio.add_tags()

            def embed_image(data):
                audio.tags["covr"] = [bytes(mp4.MP4Cover(data, imageformat='MP4Cover.FORMAT_JPEG'))]

            save_cover_image(embed_image)

            if album is not None: audio.tags["\xa9alb"] = album_name
            audio["\xa9nam"] = track_name
            audio.tags["\xa9ART"] = artists
            if album_artist is not None: audio.tags["aART"] = album_artist
            audio.tags["\xa9day"] = release_year(album)
            audio.tags["disk"] = [(disc_number, 1)]
            audio.tags["trkn"] = [(track_number, total_tracks)]
            if "comment": audio.tags["\xa9cmt"] = comment
            if grouping: audio.tags["\xa9grp"] = grouping
            if genres is not None and genres: audio.tags["\xa9gen"] = ", ".join(genres)
            audio.save()

        def set_m4a_tags(audio):
            # add M4A tags if it doesn't exist
            audio.add_tags()

            def embed_image(data):
                audio.tags[str("covr")] = m4a.M4ACover(data)

            save_cover_image(embed_image)

            if album is not None: audio.tags[b"\xa9alb"] = album.name
            audio[b"\xa9nam"] = track_name
            audio.tags[b"\xa9ART"] = artists
            if album_artist is not None: audio.tags[str("aART")] = album_artist
            audio.tags[b"\xa9day"] = release_year(album)
            audio.tags["disk"] = [(disc_number, "1")]
            audio.tags["trkn"] = [(track_number, total_tracks)]
            if comment: audio.tags[b"\xa9cmt"] = comment
            if grouping: audio.tags[b"\xa9grp"] = grouping
            if genres is not None and genres: audio.tags[b"\xa9gen"] = ", ".join(genres)
            audio.save()

        match ext:
            case "flac":
                audio = flac.FLAC(audio_file)
                set_vorbis_comments(audio)
            case "aiff":
                audio = aiff.AIFF(audio_file)
                set_id3_tags(audio)
            case "ogg":
                audio = oggvorbis.OggVorbis(audio_file)
                set_vorbis_comments(audio)
            case "opus":
                audio = oggopus.OggOpus(audio_file)
                set_vorbis_comments(audio)
            case "aac":
                audio = aac.AAC(audio_file)
                set_id3_tags_raw(audio, audio_file)
            case "m4a":
                if sys.version_info >= (3, 0):
                    from mutagen import mp4
                    audio = mp4.MP4(audio_file)
                    set_mp4_tags(audio)
                else:
                    from mutagen import m4a, mp4
                    audio = m4a.M4A(audio_file)
                    set_m4a_tags(audio)
                    audio = mp4.MP4(audio_file)
            case "mp3":
                audio = mp3.MP3(audio_file, ID3=id3.ID3)
                set_id3_tags(audio)
            case "wav":
                audio = mutagen.wave.WAVE(audio_file)
                set_id3_tags(audio)

        def bit_rate_str(bit_rate):
            brs = "%d kb/s" % bit_rate
            try: encoder_args = args.codec_args[codec]
            except: encoder_args = encoder_default_args[codec]
            if "-q:"  in encoder_args: brs = "~" + brs
            return brs

        def mode_str(mode):
            modes = ["Stereo", "Joint Stereo", "Dual Channel", "Mono"]
            if mode < len(modes): return modes[mode]
            else: return ""

        def channel_str(num):
            channels = ["", "Mono", "Stereo"]
            if num < len(channels): return channels[num]
            else: return ""

        # log id3 tags
        print("-" * 79)
        print(Fore.YELLOW + "Setting artist: " + artists + Fore.RESET)
        if album is not None:
            print(Fore.YELLOW + "Setting album: " + album_name + Fore.RESET)
        if album_artist is not None:
            print(Fore.YELLOW + "Setting album artist: " + album_artist + Fore.RESET)
        print(Fore.YELLOW + "Setting title: " + track_name + Fore.RESET)
        print(Fore.YELLOW + "Setting track info: (" +
              str(track_number) + ", " + str(total_tracks) + ")" + Fore.RESET)
        print(Fore.YELLOW + "Setting disc info: " + str(disc_number) + Fore.RESET)
        print(Fore.YELLOW + "Setting release year: " + release_year(album) + Fore.RESET)
        if genres is not None and genres: print(Fore.YELLOW + "Setting genres: " + " / ".join(genres) + Fore.RESET)
        if image is not None: print(Fore.YELLOW + "Adding cover image" + Fore.RESET)
        if comment: print(Fore.YELLOW + "Adding comment: " + comment + Fore.RESET)
        if grouping: print(Fore.YELLOW + "Adding grouping: " + grouping + Fore.RESET)
        match ext:
            case "flac":
                bit_rate = ((audio.info.bits_per_sample * audio.info.sample_rate) * audio.info.channels)
                print("Time: " + format_time(audio.info.length) + "\tFree Lossless Audio Codec" +
                        "\t[ " + bit_rate_str(bit_rate / 1000) + " @ " + str(audio.info.sample_rate) +
                        " Hz - " + channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                print(Fore.YELLOW + "Writing Vorbis comments - " + audio.tags.vendor + Fore.RESET)
                print("-" * 79)

            case "aiff":
                print("Time: " + format_time(audio.info.length) + "\tAudio Interchange File Format" +
                    "\t[ " + bit_rate_str(audio.info.bitrate / 1000) + " @ " + str(audio.info.sample_rate) +
                    " Hz - " + channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                id3_version = "v%d.%d" % (audio.tags.version[0], audio.tags.version[1])
                print("ID3 " + id3_version + ": " + str(len(audio.tags.values())) + " frames")
                print(Fore.YELLOW + "Writing ID3 version " + id3_version + Fore.RESET)
                print("-" * 79)

            case "ogg":
                print("Time: " + format_time(audio.info.length) + "\tOgg Vorbis Codec" +
                    "\t[ " + bit_rate_str(audio.info.bitrate / 1000) + " @ " +
                    str(audio.info.sample_rate) +
                    " Hz - " + channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                print(Fore.YELLOW + "Writing Vorbis comments - " + audio.tags.vendor + Fore.RESET)
                print("-" * 79)
            
            case "opus":
                print("Time: " + format_time(audio.info.length) + "\tOpus Codec" +
                    "\t[ " + channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                print(Fore.YELLOW + "Writing Vorbis comments - " + audio.tags.vendor + Fore.RESET)
                print("-" * 79)
            
            case "mp3":
                print("Time: " + format_time(audio.info.length) + "\tMPEG" + str(audio.info.version) +
                    ", Layer " + ("I" * audio.info.layer) + "\t[ " + bit_rate_str(audio.info.bitrate / 1000) +
                    " @ " + str(audio.info.sample_rate) + " Hz - " + mode_str(audio.info.mode) + " ]")
                print("-" * 79)
                id3_version = "v%d.%d" % (audio.tags.version[0], audio.tags.version[1])
                print("ID3 " + id3_version + ": " + str(len(audio.tags.values())) + " frames")
                print(Fore.YELLOW + "Writing ID3 version " + id3_version + Fore.RESET)
                print("-" * 79)
            
            case "aac":
                print("Time: " + format_time(audio.info.length) + "\tAdvanced Audio Coding" +
                    "\t[ " + bit_rate_str(audio.info.bitrate / 1000) +
                    " @ " + str(audio.info.sample_rate) + " Hz - " +
                    channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                id3_version = "v%d.%d" % (audio.tags.version[0], audio.tags.version[1])
                print("ID3 " + id3_version + ": " + str(len(audio.tags.values())) + " frames")
                print(Fore.YELLOW + "Writing ID3 version " + id3_version + Fore.RESET)
                print("-" * 79)

            case "m4a":
                bit_rate = ((audio.info.bits_per_sample * audio.info.sample_rate) *
                            audio.info.channels)
                print("Time: " + format_time(audio.info.length) + "\tMPEG-4 Part 14 Audio" +
                    "\t[ " + bit_rate_str(bit_rate / 1000) +
                    " @ " + str(audio.info.sample_rate) + " Hz - " +
                    channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                print(Fore.YELLOW + "Writing Apple iTunes metadata - " + str(audio.info.codec) + Fore.RESET)
                print("-" * 79)

        '''
            case "alac.m4a":
                bit_rate = ((audio.info.bits_per_sample * audio.info.sample_rate) * audio.info.channels)
                print("Time: " + format_time(audio.info.length) + "\tApple Lossless" +
                    "\t[ " + bit_rate_str(bit_rate / 1000) + " @ " + str(audio.info.sample_rate) +
                    " Hz - " + channel_str(audio.info.channels) + " ]")
                print("-" * 79)
                print(Fore.YELLOW + "Writing Apple iTunes metadata - " + Fore.RESET)
                print("-" * 79)
        '''
    except id3.error:
        print(Fore.YELLOW + "Warning: exception while saving id3 tag: " + str(id3.error) + Fore.RESET)
    except Exception as e: print(Fore.YELLOW + "Warning: exception while saving tag: " + type(e) + Fore.RESET)

