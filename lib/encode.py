# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from colorama import Fore, Style
import os, subprocess, shlex, shutil

encoder_default_format = {
    "flac":"flac", "aac":"m4a", "opus":"opus", "mp3":"mp3", "vorbis":"ogg", "ac3":"ac3", "pcm":"wav"
}
encoder_default_args = {
    "flac": "-c:a flac -af aformat=s16:48000 -compression_level 5",
    "aac":  "-c:a aac -b:a 320k",
    "opus": "-c:a libopus -compression_level 10 -vbr on -b:a 96000",
    "mp3":  "-c:a libmp3lame -b:a 320k",
    "vorbis": "-c:a libvorbis -q:a 5",
    "ac3": "-c:a ac3 -b:a 320k",
    "pcm": "-c:a pcm_f32le -ar 48000"  #IEEE float
}

def encode(args, codec, input_file, output_file):
    def get_ext():
        return args.encoder_format[codec] if args.encoder_format and args.encoder_format[codec] else encoder_default_format[codec]

    try: encoder_args = args.codec_args[codec]
    except: encoder_args = encoder_default_args[codec]
#ffmpeg -report <report-opts> -i input output
#<report-opts> should, in your case, be: file=test.log:level=16
    _tmpfile = '_file.' + get_ext()
    command = shlex.split('ffmpeg -hide_banner -loglevel error -y -i "'+ input_file + '" ' + encoder_args + ' ' + _tmpfile)
    #subprocess.call(command)

    try:
        subprocess.run(command, shell=True, check=True, capture_output=True)
        shutil.move(_tmpfile, output_file)
    except subprocess.CalledProcessError as err:
        print(Fore.RED + "Ffmpeg error " + err.stderr.decode('utf8') + Fore.RESET)


