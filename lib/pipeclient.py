#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import errno
import argparse

if sys.version_info[0] < 3 and sys.version_info[1] < 7:
    sys.exit('PipeClient Error: Python 2.7 or later required')

# Platform specific constants
if sys.platform == 'win32':
    WRITE_NAME = '\\\\.\\pipe\\ToSrvPipe'
    READ_NAME = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    # Linux or Mac
    PIPE_BASE = '/tmp/audacity_script_pipe.'
    WRITE_NAME = PIPE_BASE + 'to.' + str(os.getuid())
    READ_NAME = PIPE_BASE + 'from.' + str(os.getuid())
    EOL = '\n'


class PipeClient():
    """Write / read client access to Audacity via named pipes.

    Normally there should be just one instance of this class. If
    more instances are created, they all share the same state.

    __init__ calls _write_thread_start() and _read_thread_start() on
    first instantiation.

    Parameters
    ----------
        None

    Attributes
    ----------
        reader_pipe_broken : event object
            Set if pipe reader fails. Audacity may have crashed
        reply_ready : event object
            flag cleared when command sent and set when response received
        timer : bool
            When true, time the command execution (default False)
        reply : string
            message received when Audacity completes the command

    See Also
    --------
    write : Write a command to _write_pipe.
    read : Read Audacity's reply from pipe.

    """

    reader_pipe_broken = threading.Event()
    reply_ready = threading.Event()

    _shared_state = {}

    def __new__(cls, enc='', *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._shared_state
        return self

    def __init__(self, enc=''):
        self.timer = False
        self._start_time = 0
        self._write_pipe = None
        self.reply = ''
        self.enc = enc
        if not self._write_pipe:
            self._write_thread_start()
        self._read_thread_start()

    def _write_thread_start(self):
        """Start _write_pipe thread"""
        # Pipe is opened in a new thread so that we don't
        # freeze if Audacity is not running.
        write_thread = threading.Thread(target=self._write_pipe_open)
        write_thread.daemon = True
        write_thread.start()
        # Allow a little time for connection to be made.
        time.sleep(0.1)
        if not self._write_pipe:
            sys.exit('PipeClientError: Write pipe cannot be opened.')

    def _write_pipe_open(self):
        """Open _write_pipe."""
        if self.enc: self._write_pipe = open(WRITE_NAME, 'w', newline='', encoding=self.enc)
        else: self._write_pipe = open(WRITE_NAME, 'w', newline='')

    def _read_thread_start(self):
        """Start read_pipe thread."""
        read_thread = threading.Thread(target=self._reader)
        read_thread.daemon = True
        read_thread.start()

    def write(self, command, timer=False):
        """Write a command to _write_pipe.

        Parameters
        ----------
            command : string
                The command to send to Audacity
            timer : bool, optional
                If true, time the execution of the command

        Example
        -------
            write("GetInfo: Type=Labels", timer=True):

        """
        self.timer = timer
        print('Sending command:', command)
        self._write_pipe.write(command + EOL)
        # Check that read pipe is alive
        if PipeClient.reader_pipe_broken.isSet():
            sys.exit('PipeClient: Read-pipe error.')
        try:
            self._write_pipe.flush()
            if self.timer:
                self._start_time = time.time()
            self.reply = ''
            PipeClient.reply_ready.clear()
        except IOError as err:
            if err.errno == errno.EPIPE:
                sys.exit('PipeClient: Write-pipe error.')
            else:
                raise

    def _reader(self):
        """Read FIFO in worker thread."""
        # Thread will wait at this read until it connects.
        # Connection should occur as soon as _write_pipe has connected.
        read_pipe = None
        if self.enc:
            read_pipe = open(READ_NAME, 'r', newline='', encoding=self.enc)
        else:
            read_pipe = open(READ_NAME, 'r', newline='')
        message = ''
        pipe_ok = True
        while pipe_ok:
            line = read_pipe.readline()
            # Stop timer as soon as we get first line of response.
            stop_time = time.time()
            while pipe_ok and line != '\n':
                message += line
                line = read_pipe.readline()
                if line == '':
                    # No data in read_pipe indicates that the pipe is broken
                    # (Audacity may have crashed).
                    PipeClient.reader_pipe_broken.set()
                    pipe_ok = False
            if self.timer:
                xtime = (stop_time - self._start_time) * 1000
                message += 'Execution time: {0:.2f}ms'.format(xtime)
            self.reply = message
            PipeClient.reply_ready.set()
            message = ''
        read_pipe.close()

    def read(self):
        """Read Audacity's reply from pipe.

        Returns
        -------
        string
            The reply from the last command sent to Audacity, or null string
            if reply not received. Null string usually indicates that Audacity
            is still processing the last command.

        """
        if not PipeClient.reply_ready.isSet():
            return ''
        return self.reply

