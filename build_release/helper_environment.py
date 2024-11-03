# -*- coding: utf-8 -*-
import platform
from subproc_wrapper import process_open
from config import FILEPATH as CALIBRE_WEB_PATH
from config import VENV_PYTHON
import re
import os
import sys
#import pkg_resources
#import importlib
import json

try:
    import importlib
    from importlib.metadata import version
    import_lib = True
    ImportNotFound = BaseException
except ImportError:
    import_lib = False
    version = None

if not import_lib:
    try:
        import pkg_resources
        from pkg_resources import DistributionNotFound as ImportNotFound
        pkgresources = True
    except ImportError as e:
        pkgresources = False

class Environment:
    def __init__(self):
        self.initial = None
        dep = list()
        self.result = list()
        uname = platform.uname()
        self.result.append(('Platform', '{0.system} {0.release} {0.version} {0.processor} {0.machine}'.format(uname)))
        self.result.append(('Python', sys.version))

        if import_lib:
            dists = importlib.metadata.packages_distributions()
        else:
            dists = [str(d).split(" ") for d in pkg_resources.working_set]
        with open(os.path.join(CALIBRE_WEB_PATH, 'requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].strip('>'))
        with open(os.path.join(CALIBRE_WEB_PATH, 'optional-requirements.txt'), 'r') as f:
            for line in f:
                if not line.startswith('#') and not line == '\n' and not line.startswith('git'):
                    dep.append(line.split('=', 1)[0].split('>', 1)[0])
        normalized_dep = [name.replace('_', '-').upper() for name in dep]
        for element in dists:
            if element[0].replace('_', '-').upper() in normalized_dep:
                self.result.append((element[0], element[1], 'Basic'))

    def init_environment(self, initial, sub_dependencies=None):
        if sub_dependencies is None:
            sub_dependencies = list()
        self.initial = initial
        dep = sub_dependencies
        self.result = list()
        uname = platform.uname()
        self.result.append(('Platform', '{0.system} {0.release} {0.version} {0.processor} {0.machine}'.format(uname),
                            'Basic'))
        p = process_open([initial, "-V"], [0])
        p.wait()
        lines = ''.join(p.stdout.readlines())
        pVersion = re.findall(r'(\d+\.\d+\.\d+)', lines)[0]
        self.result.append(('Python', pVersion, 'Basic'))

        p = process_open([initial, "-m", "pip", "freeze"], [0])
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
        normalized_dep = [name.replace('_', '-').upper() for name in dep]
        for element in dists:
            if element[0].replace('_', '-').upper() in normalized_dep:
                self.result.append((element[0], element[1], 'Basic'))

    def add_environment(self, test, extension):
        if self.initial:
            try:
                p = process_open([self.initial, "-m", "pip", "freeze"], [0])
                p.wait()
                dists = [str(d).strip().split("==") for d in p.stdout.readlines()]
                normalized_Ext = [name.replace('_', '-').upper() for name in extension]
                for element in dists:
                    if element[0].replace('_', '-').upper() in normalized_Ext:
                        self.result.append((element[0], element[1], test))
            except Exception:
                pass
        else:
            for testdep in extension:
                self.result.append((extension, '', testdep))

    def get_Environment(self):
        return self.result

    def save_environment(self, filename):
        output = dict()
        for line in self.result:
            output[line[0].lower()] = line[1]
        with open(filename, "w") as f:
            f.write(json.dumps(output))


environment = Environment()

def add_dependency(name, testclass_name):
    print("Adding dependencies")
    element_version = list()
    with open(os.path.join(CALIBRE_WEB_PATH, 'optional-requirements.txt'), 'r') as f:
        requirements = f.readlines()
    for element in name:
        if element.lower().startswith('local|'):
            # full_module_name = ".config_test." + element.split('|')[1]
            # The file gets executed upon import, as expected.
            # tmp = __import__('pkg', fromlist=['mod', 'mod2'])
            whl = importlib.__import__("config", fromlist=[element.split('|')[1]])
            element_version.append(whl.__dict__[element.split('|')[1]])
        for line in requirements:
            if element.lower().startswith('git|') \
                    and not line.startswith('#') \
                    and not line == '\n' \
                    and line.lower().startswith('git') \
                    and line.lower().endswith('#egg=' + element.lower().lstrip('git|')+'\n'):
                element_version.append(line.strip('\n'))
            elif not line.startswith('#') \
                    and not line == '\n' \
                    and not line.startswith('git') \
                    and not line.startswith('local') \
                    and line.upper().startswith(element.upper()):
                element_version.append(line.split('=', 1)[0].strip('>'))
                break

    for indx, element in enumerate(element_version):
        with process_open([VENV_PYTHON, "-m", "pip", "install", element], (0, 4)) as r:
            while r.poll() == None:
                out = r.stdout.readline()
                out != "" and print(out.strip("\n"))
        if element.lower().startswith('git'):
            element_version[indx] = element[element.rfind('#egg=')+5:]

    environment.add_environment(testclass_name, element_version)


def remove_dependency(names):
    for name in names:
        if name.startswith('git|'):
            name = name[4:]
        if name.startswith('local|'):
            name = name.split('|')[2]
        with process_open([VENV_PYTHON, "-m", "pip", "uninstall", "-y", name], (0, 5)) as q:
            if os.name == 'nt':
                while q.poll() == None:
                    out = q.stdout.readline()
                    out != "" and print(out.strip("\n"))
            else:
                q.wait()
