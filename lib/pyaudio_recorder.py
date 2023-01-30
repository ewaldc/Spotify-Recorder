#! /usr/bin/python3
# -*- coding: utf-8 -*-

import pyaudiowpatch as pyaudio
from colorama import Fore
from lib.utils import print_str
import time
from lib.PyWave import Wave
import sys, shutil #,threading #, platform

class AudioRecorder:
    def __init__(self, recorder, pa, format):
 
        def search_device(name, device_list):
            if _debug: print(Fore.MAGENTA + "Searching for a loopback device that matches the default output device" + Fore.RESET)
            for device in device_list:
                if _debug: print(Fore.MAGENTA + "Loopback device name - sample rate: " +  device["name"] + ' - ' + str(device['defaultSampleRate']) + Fore.RESET)
                if name in device['name']: return device
            return None
 
        #super().__init__()
        self.recorder = recorder
        _debug = recorder.args.debug
        try: 
            if _debug: print(Fore.MAGENTA + "Scanning for WASAPI enabled audio devices" + Fore.RESET)
            wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI) # Get default WASAPI info
            if _debug: print(Fore.MAGENTA + "Found " + str(wasapi_info["deviceCount"]) + ' WASAPI capable devices' + Fore.RESET)
        except OSError: sys.stdout.write(Fore.RED + 'WASAPI is not available on the system. Exiting... \n' + Fore.RESET); exit(1)
        #device_list = pa.get_device_info_generator_by_host_api(host_api_type = pyaudio.paWASAPI)
        # Get default WASAPI speakers
        if _debug: print(Fore.MAGENTA + "Searching for a loopback audio device" + Fore.RESET)
        device = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if device is None:
            sys.stdout.write(Fore.RED + 'No default output/playback device defined. Exiting... \n' + Fore.RESET); sys.exit(11)
        if _debug: print(Fore.MAGENTA + "Default audio output/playback device found: " + device["name"] + Fore.RESET)

        # Search for loopback device
        device = search_device(device["name"], pa.get_loopback_device_info_generator())
        if device is None: 
            sys.stdout.write(Fore.RED + 'No loopback input device found that matches default output. Exiting... \n' + Fore.RESET); sys.exit(12)
        if _debug: print(Fore.MAGENTA + "Selecting this device as Loopback device" + Fore.RESET)
        self.pa = pa
        self.device = device
        self.channels = device["maxInputChannels"]
        self.rate = int(device["defaultSampleRate"])
        self.format = format
        self.sample_size = pyaudio.get_sample_size(format)  #CHUNK
        self.size_unit = (self.rate / 1000.0) * self.sample_size * self.channels

    def get_bitrate(self):
        return self.size_unit

    def start_recording(self, audio_file):
        def callback(in_data, frame_count, time_info, status):  # Write frames and return PA flag
            #breakpoint()
            self.wave_file.write(in_data)
            return (in_data, pyaudio.paContinue)

        format = Wave.WAVE_FORMAT_IEEE_FLOAT if self.format == pyaudio.paFloat32 else Wave.WAVE_FORMAT_PCM
        
        self.wave_file = Wave(audio_file, mode = "w", channels = self.channels,
            frequency = self.rate, bits_per_sample = self.sample_size << 3, format = format)

        self.stream = self.pa.open(format = self.format, channels = self.channels, rate = self.rate, frames_per_buffer = self.sample_size,
            input = True, input_device_index=self.device["index"], stream_callback=callback)
        self.stream.start_stream()
    
    def stop_recording(self, duration):
        if duration >= 2.0:
            time.sleep(duration - 2.0) # Blocking execution while playing
            while self.recorder.web.is_playing(): time.sleep(0.2)
        self.stream.stop_stream()
        self.stream.close()
        self.wave_file.close()

    def terminate(self):
        self.pa.terminate()
        #sys.stdout.write('Recording complete\n')

    '''
    def callback(self, in_data, frame_count, time_info, status):
        # Write frames and return PA flag
        self.wave_file.writeframes(in_data)
        return (in_data, pyaudio.paContinue)

    def start_recording(self, duration_ms):
        self.stream =  self.pyaudio.open(format = FORMAT, channels = self.channels, rate = self.rate, 
            frames_per_buffer = self.sample_size, input=True, input_device_index = self.device_idx) #, stream_callback = self.callback) #as stream:
        stream.start_stream()
        frames = []
            #for i in range(0, int((self.rate * duration / CHUNK))): frames.append(stream.read(CHUNK))
            #stream.stop_stream(); stream.close()
                #time.sleep(duration_ms/1000.0 + 1)

    def stop_recording(self):
        self.stream.stop_stream()
        self.stream.close()
        #self.wave_file.flush()
        self.wave_file.close()

        #waveFile.writeframes(b''.join(frames))
        #waveFile.close()

    def close(self):
        self.wave_file.close()

    def wait_for_recording_complete(self, thread_handle):
        thread_handle.join()
        print(Fore.GREEN + 'Recording complete' + Fore.RESET)
    '''
