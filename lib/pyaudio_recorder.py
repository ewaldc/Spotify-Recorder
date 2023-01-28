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
        #super().__init__()
        self.recorder = recorder
        try: wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI) # Get default WASAPI info
        except OSError: sys.stdout.write(Fore.RED + 'WASAPI is not available on the system. Exiting... \n' + Fore.RESET); exit(1)
        # Get default WASAPI speakers
        #self.stream = None
        device = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not device["isLoopbackDevice"]:
            def search_device(name, device_list):
                for device in device_list:
                    if name in device['name']: return device
                return None
            device = search_device(device["name"], pa.get_loopback_device_info_generator())
            if device is None: sys.stdout.write(Fore.RED + 'No loopback output device found. Exiting... \n' + Fore.RESET); sys.exit(11)

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
