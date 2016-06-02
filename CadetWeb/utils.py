__author__ = 'kosh_000'

import itertools
import importlib
import glob
import os
import json
import plot_sensitivity
import types
import errno
import csv
import settings
from collections import OrderedDict

current_path = __file__
simulation_path, current_file_name = os.path.split(current_path)
parent_path, _ = simulation_path.rsplit('/', 1)
plugins = os.path.join(parent_path, 'CadetWeb', 'plugins')
storage_path = os.path.join(parent_path, 'CadetWeb', 'sims')

def encode_to_ascii(data):
    "encode all the data in this dictionary to ascii"
    temp = {}
    for key,value in data.items():
        if isinstance(value, types.StringTypes):
            temp[key.encode('ascii')] = value.encode('ascii')
        elif isinstance(value, types.ListType):
            temp[key.encode('ascii')] = encode_to_ascii_list(value)
        elif isinstance(value, types.DictType):
            temp[key.encode('ascii')] = encode_to_ascii(value)
        else:
            temp[key.encode('ascii')] = value
    return temp

def encode_to_ascii_list(data):
    "enocde all the data in a list to ascii"
    temp = []

    for key in data:
        if isinstance(key, types.StringTypes):
            temp.append(key.encode('ascii'))
        elif isinstance(key, types.ListType):
            temp.append(encode_to_ascii_list(key))
        elif isinstance(key, types.DictType):
            temp.append(encode_to_ascii(key))
        else:
            temp.append(key)
    return temp


#new version from http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid
def check_pid(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True

def get_hdf5_path(path, chunk_size, rel_path):
    "return just the path to the hdf5 file"
    relative_parts = [''.join(i for i in seq if i is not None) for seq in grouper(path, chunk_size)]
    relative_path = os.path.join(*relative_parts)

    if rel_path:
        return os.path.join(storage_path, relative_path, 'batch', rel_path, 'sim.h5')
    else:
        return os.path.join(storage_path, relative_path, 'sim.h5')

def get_graph_data(path, chunk_size, rel_path):
    "return the path to the json_file, path to the hdf5 file, and the list of name,url pairs for images"
    graphs = []

    relative_parts = [''.join(i for i in seq if i is not None) for seq in grouper(path, chunk_size)]
    relative_path = os.path.join(*relative_parts)


    try:
        pid = int(open(os.path.join(storage_path, relative_path, 'pid'), 'r').read())
        alive = check_pid(pid)
    except IOError:
        alive = False

    try:
        if rel_path:
            complete = open(os.path.join(storage_path, relative_path, 'batch', rel_path, 'status')).read() == 'success'
        else:
            complete = open(os.path.join(storage_path, relative_path, 'status')).read() == 'success'
    except IOError:
        complete = False

    #try:
    #    failure = open(os.path.join(storage_path, relative_path, 'status')).read() == 'failure'
    #except IOError:
    #    failure = False

    json_path = os.path.join(storage_path, relative_path, 'setup.json')

    if rel_path:
        hdf5_path = os.path.join(storage_path, relative_path, 'batch', rel_path, 'sim.h5')
    else:
        hdf5_path = os.path.join(storage_path, relative_path, 'sim.h5')

    json_data = open(json_path, 'rb').read()

    json_data = json.loads(json_data)
    json_data = encode_to_ascii(json_data)

    for key,value in json_data.items():
        if key.startswith('graph_single') and value == '1':
            _, name = key.split(':')
            filename = get_attribute_by_name(name, 'graphing/single', 'file_name')
            filename_csv = get_attribute_by_name(name, 'graphing/single', 'file_name_csv')
            filename_xls = get_attribute_by_name(name, 'graphing/single', 'file_name_xls')
            path = os.path.join('/static/simulation/sims', relative_path, filename)
            path_download = os.path.join('/static/simulation/sims', relative_path, filename_csv)
            path_download_xls = os.path.join('/static/simulation/sims', relative_path, filename_xls)
            id = name.replace(' ', '_').replace(':', '_')
            graphs.append( (id, name, path, path_download, path_download_xls, filename_csv, filename_xls) )

        if key.startswith('graph_group') and value == '1':
            _, name = key.split(':')
            filename = get_attribute_by_name(name, 'graphing/group', 'file_name')
            filename_csv = get_attribute_by_name(name, 'graphing/single', 'file_name_csv')
            filename_xls = get_attribute_by_name(name, 'graphing/single', 'file_name_xls')
            path = os.path.join('/static/simulation/sims', relative_path, filename)
            path_download = os.path.join('/static/simulation/sims', relative_path, filename_csv)
            path_download_xls = os.path.join('/static/simulation/sims', relative_path, filename_xls)
            id = name.replace(' ', '_').replace(':', '_')
            graphs.append( (id, name, path, path_download, path_download_xls, filename_csv, filename_xls) )

    for sensitivity_number in range(len(json_data.get("sensitivities", []))):
        file_name, file_name_csv, file_name_xls, title = plot_sensitivity.get_picture_id(hdf5_path, sensitivity_number)
        path = os.path.join('/static/simulation/sims', relative_path, file_name)
        path_download = os.path.join('/static/simulation/sims', relative_path, file_name_csv)
        path_download_xls = os.path.join('/static/simulation/sims', relative_path, file_name_xls)
        id = title.replace(' ', '_').replace(':', '_')
        graphs.append( (id, title, path, path_download, path_download_xls, filename_csv, filename_xls))

    try:
        stdout = open(os.path.join(storage_path, relative_path, 'stdout')).read()
    except IOError:
        stdout = ''

    try:
        stderr = open(os.path.join(storage_path, relative_path, 'stderr')).read()
    except IOError:
        stderr = ''

    return json_path, hdf5_path, graphs, json_data, alive, complete, stdout, stderr

#from https://docs.python.org/2/library/itertools.html
def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

def load_plugin(path):
    module_name = os.path.relpath(path, simulation_path).replace('/', '.').replace('.py', '')
    return importlib.import_module(module_name)

def call_plugin_function(plugin_path, attribute_name, *args, **kwargs):
    return getattr(load_plugin(plugin_path), attribute_name)(*args, **kwargs)

def call_plugin_by_name(name, directory, attribute_name, *args, **kwargs):
    for path in get_files(os.path.join(plugins, directory, '*.py')):
        plugin_name = get_plugin_attribute(path, 'name')
        if plugin_name == name:
            return call_plugin_function(path, attribute_name, *args, **kwargs)

def call_plugin_by_id(name, attribute_name, *args, **kwargs):
    module = importlib.import_module(name)
    return getattr(module, attribute_name)(*args, **kwargs)

def call_plugins_by_name(directory, attribute_name, *args, **kwargs):
    temp = []
    for path in get_files(os.path.join(plugins, directory, '*.py')):
        temp.append( call_plugin_function(path, attribute_name, *args, **kwargs) )
    return temp

def get_attribute_by_name(name, directory, attribute_name):
    for path in get_files(os.path.join(plugins, directory, '*.py')):
        plugin_name = get_plugin_attribute(path, 'name')
        if plugin_name == name:
            return get_plugin_attribute(path, attribute_name)

def get_plugin_attribute(path, attribute_name):
    return getattr(load_plugin(path), attribute_name)

def get_files(path):
    return [path for path in glob.glob(path) if not path.endswith('__init__.py')]

def get_plugin_names(directory):
    return [get_plugin_attribute(path, 'name') for path in get_files(os.path.join(plugins, directory, '*.py'))]


#cache the isotherm and parameters csv file and also do some processing with them.
def get_parameters():
    with open(os.path.join(simulation_path,'parms.csv'), 'rb') as csvfile:
        temp = []
        reader = csv.reader(csvfile)
        #read the header and discard it
        reader.next()
        for name, units, type, per_component, per_section, sensitive, description, human_name, isotherm  in reader:
            if isotherm == '' or (isotherm and isotherm in settings.isotherms):
                per_component = int(per_component)
                per_section = int(per_section)
                sensitive = int(sensitive)
                temp.append( (name, units, type, per_component, per_section, sensitive, description, human_name), )
        return temp

def get_isotherms():
    with open(os.path.join(simulation_path,'iso.csv'), 'rb') as csvfile:
        reader = csv.reader(csvfile)
        #read the header and discard it
        reader.next()

        #decorate, sort, undecorate
        dsu = [(settings.isotherms.index(isotherm), name, isotherm) for name, isotherm in list(reader) if isotherm in settings.isotherms] 
        dsu.sort()
        return [(name, isotherm) for (sort, name, isotherm) in dsu]

def isotherm_setup_cache(isotherms, parameters):
    "make a dictionary that has a key of the isotherm name and then a list of all the isotherm values plus if it is per component"
    "also make a dictionary of sets to allow quickly check if an item is part of an isotherm"
    temp = OrderedDict()
    temp_set = OrderedDict()
    name_set = OrderedDict()

    for name, isotherm in isotherms:
        section = temp.get(isotherm, [])
        section_set = temp_set.get(isotherm, set())
        section_set.add(name)
        name_set[name] = None
        for par_name, units, type, per_component, per_section, sensitive, description, human_name in parameters:
            if name == par_name:
                section.append( (name, per_component), )
        temp[isotherm] = section
        temp_set[isotherm] = section_set
    return temp, temp_set, name_set


isotherms = get_isotherms()
parameters = get_parameters()
isotherm_settings, isotherm_set, isotherm_name_set = isotherm_setup_cache(isotherms, parameters)

#create a lookup table to map the CADET name to a more user friendly name
#the key is the CADET name and the value is a tuple of a name to display and the text for a tooltip

def generate_name_lookup(paraemters):
    "generate the dictionarys that maps CADET names to more human names"
    "The first dictionary is used in python to quickly look up human names and tooltips"
    "The second dictionary is used for django templates and the names are modified in a predictable way to make it easy to use in templates without conflicts"
    temp_python = OrderedDict()
    temp_django = OrderedDict()
    for par_name, units, type, per_component, per_section, sensitive, description, human_name in parameters:
        temp_python[par_name] = (human_name, description, units)
        temp_django[par_name+ '_human'] = human_name
        temp_django[par_name+ '_tip'] = description
        temp_django[par_name+ '_units'] = units
    return temp_python, temp_django


name_lookup_python, name_lookup_template = generate_name_lookup(parameters)