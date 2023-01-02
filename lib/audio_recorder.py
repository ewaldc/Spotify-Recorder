#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""Test Import / Export and recording.

recording-test.py loads a WAV file, plays it, recording at the same time until
the end of the track, and then exports the recording as a WAV with "-out"
appended to the file name.

To run the test without input prompts, set valid values for
PATH and INFILE.

User supplied variables
-------
    PATH: Path to the folder containing the input test file. Also used for exporting the result.
    INFILE: Name of the input WAV file.

With a little modification, can be suitable for rinse and repeat with different
input files.

Make sure Audacity is running and that mod-script-pipe is enabled
before running this script.
"""
import pipeclient
from colorama import Fore, Style
import os
import sys
import time
import json

class AudioRecorder(object):

    def send_command(self, command):
        # Send a command to Audacity
        print("Send: >>> "+command)
        self.to_pipe.write(command + self.EOL)
        self.to_pipe.flush()


    def get_response(self):
        # Get response from Audacity
        line = self.from_pipe.readline()
        result = ""
        while True:
            result += line
            line = self.from_pipe.readline()
            # print(f"Line read: [{line}]")
            if line == '\n': return result


    def do_command(self, command):
        # Do the command. Return the response."""
        self.send_command(command)
        time.sleep(0.1) # may be required on slow machines
        response = self.get_response()
        print("Rcvd: <<< " + response)
        return response

    def __init__(self, args, recorder):
        self.args = args
        self.recorder = recorder

        print(Fore.GREEN + 'Initializing Audio Recorder (Audacity)' + Fore.RESET)
        self.client = pipeclient.PipeClient()

