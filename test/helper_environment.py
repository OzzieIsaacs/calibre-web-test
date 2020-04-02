# -*- coding: utf-8 -*-
import platform
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH
import re
import os
import sys
import pkg_resources

class Environment():
    def __init__(self):
        self.initial = None
        dep=list()
        self.result=list()
        uname = platform.uname()
        self.result.append(('Platform','{0.system} {0.release} {0.version} {0.processor} {0.machine}'.format(uname)))
        self.result.append(('Python', sys.version))

        dists = [str(d).split(" ") for d in pkg_resources.working_set]
        with open(os.path.join(CALIBRE_WEB_PATH,'requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].strip('>'))
        with open(os.path.join(CALIBRE_WEB_PATH,'optional-requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].split('>', 1)[0])
        for element in dists:
            if element[0] in dep:
                self.result.append((element[0],element[1],'basic'))


    def init_Environment(self, initial):
        self.initial = initial
        dep = list()
        self.result = list()
        uname = platform.uname()
        self.result.append(('Platform', '{0.system} {0.release} {0.version} {0.processor} {0.machine}'.format(uname),'Basic'))
        p = process_open([initial, "-V"], (0))
        p.wait()
        lines = ''.join(p.stdout.readlines())
        pVersion = re.findall("(\d+\.\d+\.\d+)", lines)[0]
        self.result.append(('Python', pVersion,'Basic'))

        p = process_open([initial, "-m", "pip", "freeze"], (0))
        p.wait()
        dists = [str(d).strip().split("==") for d in p.stdout.readlines()]
        with open(os.path.join(CALIBRE_WEB_PATH, 'requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].strip('>'))
        with open(os.path.join(CALIBRE_WEB_PATH, 'optional-requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].split('>', 1)[0])
        for element in dists:
            if element[0] in dep:
                self.result.append((element[0],element[1],'basic'))

    def add_Environemnt(self, test, extension):
        if self.initial:
            try:
                p = process_open([self.initial, "-m", "pip", "freeze"], (0))
                p.wait()
                dists = [str(d).strip().split("==") for d in p.stdout.readlines()]
                for element in dists:
                    if element[0] in extension:
                        self.result.append((element[0],element[1],test))
            except:
                pass
        else:
            for testdep in extension:
                self.result.append((extension, '', testdep))

    def get_Environment(self):
        return self.result


environment = Environment()