# -*- coding: utf-8 -*-

# from __future__ import division, print_function, unicode_literals
import subprocess
import os
import sys


def process_open(command, quotes=None, env=None, sout=subprocess.PIPE, s_err=subprocess.PIPE, cwd=None):
    # Linux py2.7 encode as list without quotes no empty element for parameters
    # linux py3.x no encode and as list without quotes no empty element for parameters
    # windows py2.7 encode as string with quotes empty element for parameters is okay
    # windows py 3.x no encode and as string with quotes empty element for parameters is okay
    # separate handling for windows and linux
    if quotes is None:
        quotes = []
    if os.name == 'nt':
        for key, element in enumerate(command):
            if key in quotes:
                command[key] = '"' + element + '"'
        exc_command = " ".join([x for x in command if x])
        if sys.version_info < (3, 0):
            exc_command = exc_command.encode(sys.getfilesystemencoding())
    else:
        if sys.version_info < (3, 0):
            exc_command = [x.encode(sys.getfilesystemencoding()) for x in command if x]
        else:
            exc_command = [x for x in command if x]

    return subprocess.Popen(exc_command,
                            shell=False,
                            stdout=sout,
                            stderr=s_err,
                            universal_newlines=True,
                            env=env,
                            cwd=cwd)
