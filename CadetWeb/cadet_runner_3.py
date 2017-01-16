#!/usr/bin/env python2.7

import numpy as np
from numpy import random
import h5py
import os
import os.path
import subprocess
import json
import argparse
import types
import plot_sensitivity
import utils
import itertools
import glob
import os
from threading import Timer
import time
import settings
import sys
import urllib2
import urllib

current_path = __file__
parent_path, current_file_name = os.path.split(current_path)
plugins = os.path.join(parent_path, 'plugins')
cadet_path = os.path.join(os.sep, 'home', 'heymann', 'CADET3', 'bin', 'cadet-cli')
library_path = os.path.join(os.sep, 'home', 'heymann', 'CADET3', 'lib')

print cadet_path
print library_path

env = dict(os.environ)
env['LD_LIBRARY_PATH'] = library_path

storage_path = os.path.join(parent_path, 'sims')

def set_value(node, nameH5, dtype, value):
    "merge the values from parms into node of the hdf5 file"
    data = np.array(value, dtype=dtype)
    if node.get(nameH5, None) is not None:
        del node[nameH5]
    node.create_dataset(nameH5, data=data, maxshape=tuple(None for i in range(data.ndim)), fillvalue=[0])

def set_value_enum(node, nameH5, value):
    "merge the values from parms into node of the hdf5 file"
    dtype = 'S' + str(len(value)+1)
    data = np.array(value, dtype=dtype)
    if node.get(nameH5, None) is not None:
        del node[nameH5]
    node.create_dataset(nameH5, data=data)

def run_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--json", help="Enter path to JSON file")
    parser.add_argument("-p", "--sim", help="Enter the path to the h5 file")
    parser.add_argument("-J", "--job", help="Enter the Job ID")
    parser.add_argument('-F', "--url_fail", help="Enter the feailure URL")
    parser.add_argument('-P', "--url_pass", help="Enter the pass url")
    args = parser.parse_args()
    return args

def create_simulation_file(directory_path, data):
    "create a simulation in the given directory using the given data"
    file_path = os.path.join(directory_path, 'sim3.h5')

    #only create the file if it does not already exist
    if not os.path.isfile(file_path):

        h5 = h5py.File(file_path, 'w')

        create_input(h5, data)
        create_web(h5, data)

        h5.close()

    return file_path

def create_input(h5, data):
    "handle the input node"
    input = h5.create_group("input")

    create_model(input, data)
    create_return(input, data)
    create_sensitivity(input, data)
    create_solver(input, data)
    

def create_model(input,data):
    model = input.create_group("model")

    set_value(model, 'NUNITS', 'i4', 2)
    create_connections(model, data)
    create_inlet(model, data)
    create_column(model, data)


def create_connections(model, data):
    connection = model.create_group('connections')
    set_value(connection, 'NSWITCHES', 'i4', 1)

    switch = connection.create_group('switch_000')
    set_value(switch, 'CONNECTIONS', 'i4', [0, 1, -1, -1])
    set_value(switch, 'SECTION', 'i4', 0)


def create_inlet(model, data):
    "handle the inlet node"
    unit = model.create_group("unit_000")

    set_value_enum(unit, 'INLET_TYPE', 'PIECEWISE_CUBIC_POLY')
    set_value(unit, 'NCOMP', 'i4', getNumberOfComponents(data))
    set_value_enum(unit, 'UNIT_TYPE', 'INLET')
    
    step_names = get_step_names(data)
    
    for section_number in range(int(data['NSEC'])):
        section_name = 'sec_%.03d' % section_number
        section = unit.create_group(section_name)
        
        #floats formatted sectionName_component_(Cubic, Quadratic, Constant, Linear)
        constant, linear, quadratic, cubic = get_inlet_data(step_names[section_number], data)
        set_value(section, 'CONST_COEFF', 'f8', constant)
        set_value(section, 'LIN_COEFF', 'f8', linear)
        set_value(section, 'QUAD_COEFF', 'f8', quadratic)
        set_value(section, 'CUBE_COEFF', 'f8', cubic)
    

def create_column(model, data):
    unit = model.create_group("unit_001")

    isotherm = data['CADET_ISOTHERM']['ISOTHERM']
    open('/tmp/cadet', 'w').writelines(['ISOTHERM', str(type(isotherm)), str(isotherm)])
    if isotherm == 'MOBILE_PHASE_MODULATORS':
        isotherm = 'MOBILE_PHASE_MODULATOR'

    set_value_enum(unit, 'ADSORPTION_MODEL', isotherm)
    set_value(unit, 'COL_DISPERSION', 'f8', float(data['COL_DISPERSION']))
    set_value(unit, 'COL_LENGTH', 'f8', float(data['COL_LENGTH']))
    set_value(unit, 'COL_POROSITY', 'f8', float(data['COL_POROSITY']))
    set_value(unit, 'FILM_DIFFUSION', 'f8', get_film_diffusion(data))
    set_value(unit, 'INIT_C', 'f8', get_init_c_diffusion(data))
    set_value(unit, 'INIT_Q', 'f8', get_init_q_diffusion(data))
    set_value(unit, 'NCOMP', 'i4', getNumberOfComponents(data))
    set_value(unit, 'PAR_DIFFUSION', 'f8', get_particle_diffusion(data))
    set_value(unit, 'PAR_POROSITY', 'f8', float(data['PAR_POROSITY']))
    set_value(unit, 'PAR_RADIUS', 'f8', float(data['PAR_RADIUS']))
    set_value(unit, 'PAR_SURFDIFFUSION', 'f8', get_surface_diffusion(data))
    set_value_enum(unit, 'UNIT_TYPE', data['CHROMATOGRAPHY_TYPE'])
    set_value(unit, 'VELOCITY', 'f8', float(data['VELOCITY']))
    
    create_adsorption(unit, data)
    create_discretization(unit, data)
  

def create_adsorption(unit, data):
    "handle the adsorption node"
    adsorption = unit.create_group("adsorption")

    for key,value in data['CADET_ISOTHERM'].items():
        if key == 'ISOTHERM':
            continue
        func = int if key.startswith('IS_') else float
        dtype = 'i4' if key.startswith('IS_') else 'f8'
        try:
            #handles string case
            set_value(adsorption, key, dtype, func(value))
        except TypeError:
            #handles list case
            set_value(adsorption, key, dtype, map(func, value))


def create_discretization(unit, data):
    "handle discretization node"
    discretization = unit.create_group("discretization")

    set_value(discretization, 'GS_TYPE', 'i4', int(data['GS_TYPE']))
    set_value(discretization, 'MAX_KRYLOV', 'i4', int(data['MAX_KRYLOV']))
    set_value(discretization, 'MAX_RESTARTS', 'i4', int(data['MAX_RESTARTS']))
    set_value(discretization, 'NBOUND', 'i4', np.ones(getNumberOfComponents(data)))
    set_value(discretization, 'NCOL', 'i4', int(data['NCOL']))
    set_value(discretization, 'NPAR', 'i4', int(data['NPAR']))
    set_value_enum(discretization, 'PAR_DISC_TYPE', data['PAR_DISC_TYPE'])
    set_value(discretization, 'PAR_DISC_VECTOR', 'f8', [float(data['PAR_DISC_VECTOR_1']), float(data['PAR_DISC_VECTOR_2']), float(data['PAR_DISC_VECTOR_3'])])
    set_value_enum(discretization, 'RECONSTRUCTION', data['RECONSTRUCTION'])
    set_value(discretization, 'SCHUR_SAFETY', 'f8', float(data['SCHUR_SAFETY']))
    set_value(discretization, 'USE_ANALYTIC_JACOBIAN', 'i4', int(data['USE_ANALYTIC_JACOBIAN']))
    
    weno(discretization, data)


def weno(discretization, data):
    "handle the weno node"
    weno = discretization.create_group("weno")

    set_value(weno, 'BOUNDARY_MODEL', 'i4', int(data['BOUNDARY_MODEL']))
    set_value(weno, 'WENO_EPS', 'f8', float(data['WENO_EPS']))
    set_value(weno, 'WENO_ORDER', 'i4', int(data['WENO_ORDER']))
   

def create_return(input, data):
    ret = input.create_group("return")
    set_value(ret, 'WRITE_SENS_LAST', 'i4', 0)
    set_value(ret, 'WRITE_SOLUTION_LAST', 'i4', 0)
    set_value(ret, 'WRITE_SOLUTION_TIMES', 'i4', 1)
    set_value(ret, 'SPLIT_COMPONENTS_DATA', 'i4', 1)

    unit = ret.create_group('unit_001')
    
    #Inlet
    set_value(unit, 'WRITE_SENSDOT_COLUMN_INLET', 'i4', 1)
    set_value(unit, 'WRITE_SENS_COLUMN_INLET', 'i4', 1)
    set_value(unit, 'WRITE_SOLDOT_COLUMN_INLET', 'i4', 1)
    set_value(unit, 'WRITE_SOLUTION_COLUMN_INLET', 'i4', 1)
    
    #Oulet
    set_value(unit, 'WRITE_SENSDOT_COLUMN_OUTLET', 'i4', 1)
    set_value(unit, 'WRITE_SENS_COLUMN_OUTLET', 'i4', 1)
    set_value(unit, 'WRITE_SOLDOT_COLUMN_OUTLET', 'i4', 1)
    set_value(unit, 'WRITE_SOLUTION_COLUMN_OUTLET', 'i4', 1)


    #TODO: Need to just have radio for column, flux and particle (need to look at dimensions for the gui)
    #Maybe just remove particle, flux and column, need to think about that one, it creates so much data there is no way
    #for the website to work with it
    

def create_sensitivity(input, data):
    "process the sensitivity node"
    sensitivity = input.create_group("sensitivity")

    sens = data.get('sensitivities')

    set_value(sensitivity, 'NSENS', 'i4', len(sens))
    set_value_enum(sensitivity, 'SENS_METHOD', 'ad1')
    for idx,sen in enumerate(sens):
        group = sensitivity.create_group("param_%03d" % idx)

        set_value(group, 'SENS_ABSTOL', 'f8', float(sen['SENS_ABSTOL']))
        
        #TODO: this will NOT work for any multistate setup
        set_value(group, 'SENS_BOUNDPHASE', 'i4', -1 if int(sen['SENS_COMP']) == -1 else 0)

        set_value(group, 'SENS_COMP', 'i4', int(sen['SENS_COMP']))
        set_value(group, 'SENS_FACTOR', 'f8', 1.0)
        set_value_enum(group, 'SENS_NAME', sen['SENS_NAME'])
        set_Value(group, 'SENS_REACTION', 'i4', -1)
        set_value(group, 'SENS_SECTION', 'i4', int(sen['SENS_SECTION']))
        
        #TODO: need to figure out how to do this one also
        #This should work for now, needs to be redone entirely later
        if sen['SENS_NAME'] in ('CONST_COEFF', 'LIN_COEFF', 'QUAD_COEFF', 'CUBE_COEFF'):
            set_value(group, 'SENS_UNIT', 'i4', 0)
        else:
            set_value(group, 'SENS_UNIT', 'i4', 1)

        set_value(group, 'SENS_FD_DELTA', 'f8', float(sen['SENS_FD_DELTA']))

def create_solver(input, data):
    "process the solver node"
    solver = input.create_group("solver")
    
    
    set_value(solver, 'NTHREADS', 'i4', int(data['NTHREADS']))
    
    #probably use the csv module to make this more generic
    #for now since we only accept numbers and they must be separated by commas this will work
    #the sequence is sorted after parsing just in case
    
    times = data['USER_SOLUTION_TIMES']
    if times:
        times = times.split(',')
        times = map(str.strip, times)
        times = map(float, times)
        times.sort()
    else:
        section_times = get_section_times(data)
        times = np.linspace(section_times[0], section_times[-1], 1000, endpoint=True)
    
    set_value(solver, 'USER_SOLUTION_TIMES', 'f8', times)
    
    create_section_times(solver, data)
    time_integrator(solver, data)




def create_web(h5, data):
    "handle the web node"
    web = h5.create_group("web")

    set_value_enum(web, 'MODEL_NAME', data['model_name'])
    set_value_enum(web, 'STUDY_NAME', data['study_name'])

    STEPS = web.create_group("STEPS")
    list_of_steps = [('STEP_%03d' % (i-1), data.get('step%s' % i)) for i in range(1, int(data.get('NSEC', ''))+1)]
    for step_id, step_name in list_of_steps:
        set_value_enum(STEPS, step_id, step_name)

    COMPONENTS = web.create_group("COMPONENTS")

    component_names = [data.get('component%s' % i) for i in range(1, int(data['numberOfComponents'])+1)]

    #add virtual names
    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        component_names = list(itertools.chain.from_iterable(zip(component_names, [i + ' Virtual' for i in component_names])))

    #add id
    list_of_names = [('COMP_%03d' % idx, name) for idx, name in enumerate(component_names)]

    for comp_id, comp_name in list_of_names:
        set_value_enum(COMPONENTS, comp_id, comp_name)

    GRAPHS = web.create_group("GRAPHS")
    SINGLE = GRAPHS.create_group("SINGLE")

    graphs = (key for key,value in data.items() if key.startswith('graph_single') and value == '1')
    for idx, graph_name in enumerate(graphs):
        _, graph_name = graph_name.split(':')
        set_value_enum(SINGLE, 'GRAPH_%03d' % idx, graph_name)

    GROUP = GRAPHS.create_group("GROUP")

    graphs = (key for key,value in data.items() if key.startswith('graph_group') and value == '1')
    for idx, graph_name in enumerate(graphs):
        _, graph_name = graph_name.split(':')
        set_value_enum(GROUP, 'GRAPH_%03d' % idx, graph_name)

    PERFORMANCE = web.create_group("PERFORMANCE")

    SINGLE = PERFORMANCE.create_group("SINGLE")

    perfs = (key for key,value in data.items() if key.startswith('perf_single') and value == '1')
    for idx, graph_name in enumerate(perfs):
        _, graph_name = graph_name.split(':')
        set_value_enum(SINGLE, 'PERF_%03d' % idx, graph_name)

    GROUP = PERFORMANCE.create_group("GROUP")

    perfs = (key for key,value in data.items() if key.startswith('perf_group') and value == '1')
    for idx, graph_name in enumerate(perfs):
        _, graph_name = graph_name.split(':')
        set_value_enum(GROUP, 'GRAPH_%03d' % idx, graph_name)
 

def create_section_times(solver, data):
    sections = solver.create_group("sections")

    set_value(sections, 'NSEC', 'i4', int(data['NSEC']))
    set_value(sections, 'SECTION_CONTINUITY', 'i4', get_section_continuity(data))
    set_value(sections, 'SECTION_TIMES', 'f8', get_section_times(data))
 
def time_integrator(solver, data):
    "implement the time integrator node"
    time_integrator = solver.create_group("time_integrator")

    set_value(time_integrator, 'ABSTOL', 'f8', float(data['ABSTOL']))
    set_value(time_integrator, 'ALGTOL', 'f8', float(data['ABSTOL']))
    set_value(time_integrator, 'INIT_STEP_SIZE', 'f8', float(data['INIT_STEP_SIZE']))
    set_value(time_integrator, 'MAX_STEPS', 'i4', int(data['MAX_STEPS']))
    set_value(time_integrator, 'RELTOL', 'f8', float(data['RELTOL']))
    

def get_components_in_order(data):
    "return the names of components in order"
    number_of_components = int(data['numberOfComponents'])
    return [data['component%d' % i] for i in xrange(1, number_of_components+1)]


def get_step_names(data):
    number_of_steps = int(data['NSEC'])
    return [data['step%d' % i] for i in xrange(1, number_of_steps+1)]
    

def get_suffix_data(suffix, components, data):
    "return all the data that shares a common suffix with the component name"
    return [data['%s:%s' % (component, suffix)] for component in components]


def get_inlet_data(step_name, data):
    "return all the inlet data for a given step name and the correct order"
    "valid order values are Constant, Linear, Cubic and Quadratic"
    components = get_components_in_order(data)
    constant =  [data['%s:%s:%s' % (step_name, component, 'CONST_COEFF')] for component in components]
    linear =  [data['%s:%s:%s' % (step_name, component, 'LIN_COEFF')] for component in components]
    quadratic =  [data['%s:%s:%s' % (step_name, component, 'QUAD_COEFF')] for component in components]
    cubic =  [data['%s:%s:%s' % (step_name, component, 'CUBE_COEFF')] for component in components]

    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        constant = list(itertools.chain.from_iterable(zip(constant, [0 for i in components])))
        linear = list(itertools.chain.from_iterable(zip(linear, [0 for i in components])))
        quadratic = list(itertools.chain.from_iterable(zip(quadratic, [0 for i in components])))
        cubic = list(itertools.chain.from_iterable(zip(cubic, [0 for i in components])))


    return constant, linear, quadratic, cubic
    

def get_section_times(data):
    "return a vector of the section times in order"
    steps = get_step_names(data)
    times = np.zeros(len(steps)+1)
    for idx,step in enumerate(steps):
        times[idx] = float(data['Start:%s' % step])
    times[-1] = float(data['End:%s' % steps[-1]])
    return times
        

def get_section_continuity(data):
    "return the section continuity"
    number_of_steps = int(data['NSEC'])
    return [data['continuous_%d' % i] for i in xrange(0, number_of_steps - 1)]    


def get_film_diffusion(data):
    "return the vector of film diffusions"
    components = get_components_in_order(data)

    film_diffusion = map(float, get_suffix_data('FILM_DIFFUSION', components, data))
    
    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        film_diffusion = list(itertools.chain.from_iterable(zip(film_diffusion, film_diffusion)))
    return film_diffusion


def get_particle_diffusion(data):
    "return the vector of film diffusions"
    components = get_components_in_order(data)

    par_diffusion = map(float, get_suffix_data('PAR_DIFFUSION', components, data))
    
    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        par_diffusion = list(itertools.chain.from_iterable(zip(par_diffusion, par_diffusion)))
    return par_diffusion


def get_surface_diffusion(data):
    "return the vector of film diffusions"
    components = get_components_in_order(data)
    surface_diffusion = map(float, get_suffix_data('PAR_SURFDIFFUSION', components, data))
    
    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        surface_diffusion = list(itertools.chain.from_iterable(zip(surface_diffusion, surface_diffusion)))
    return surface_diffusion


def get_init_c_diffusion(data):
    "return the vector of film diffusions"
    components = get_components_in_order(data)
    init_c = map(float, get_suffix_data('INIT_C', components, data))

    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        init_c = list(itertools.chain.from_iterable(zip(init_c, [0 for i in components])))
    return init_c


def get_init_q_diffusion(data):
    "return the vector of film diffusions"
    components = get_components_in_order(data)
    init_q = map(float, get_suffix_data('INIT_Q', components, data))

    if data['CADET_ISOTHERM']['ISOTHERM'] == 'MULTI_COMPONENT_BILANGMUIR':
        init_q = list(itertools.chain.from_iterable(zip(init_q, [0 for i in components])))
    return init_q


def getNumberOfComponents(data):

    isotherm = data['CADET_ISOTHERM']['ISOTHERM']

    no_change_isotherms = set(['LINEAR', 'MULTI_COMPONENT_LANGMUIR', 'MOBILE_PHASE_MODULATORS', 'EXTERNAL_MOBILE_PHASE_MODULATORS', 'EXTERNAL_LANGMUIR',
                               'STERIC_MASS_ACTION', 'SELF_ASSOCIATION', 'EXTERNAL_STERIC_MASS_ACTION', 'MOBILE_PHASE_MODULATORS', 'EXTERNAL_MOBILE_PHASE_MODULATORS'])

    try:
        numberOfComponents = int(data['numberOfComponents'])
    except KeyError:
        #must be an older file and that still has the CADET virtual components
        numberOfComponents = int(data['NCOMP'])
        data['numberOfComponents'] = numberOfComponents

    if isotherm in no_change_isotherms:
        NCOMP = numberOfComponents
    elif isotherm == 'MULTI_COMPONENT_BILANGMUIR':
        NCOMP = numberOfComponents * 2
    return NCOMP


def compress_data(h5):
    #DO NOT MOVE THIS IMPORT OR IT WILL DEADLOCK WSGI
    #IT CAN'T BE OUTSIDE THIS FUNCTION
    #import compress_series
    #compress the data
    web = h5["web"]
    if web.get("compress", None) is not None:
        del web["compress"]
    compress = web.create_group("compress")

    #inlet
    #outlet
    #parameters

    number_of_components = h5['/input/model/unit_001/NCOMP'].value

    solution_times = h5['/output/solution/SOLUTION_TIMES'][:]

    ABSTOL = h5['/input/solver/time_integrator/ABSTOL'].value

    digits = int(np.floor(abs(max(np.log10(ABSTOL), -15)) - 2))

    for name in ('OUTLET', 'INLET'):
        data = [solution_times,]
        for idx in range(number_of_components):
            data.append(np.array(h5['/output/solution/unit_001/SOLUTION_COLUMN_%s_COMP_%03d' % (name, idx)]))
        data = np.transpose(np.vstack(data))
        #data = compress_series.compress(data)
        set_value(compress, name, 'f8', data)

    try:
        sens = h5['/output/sensitivity']
    except KeyError:
        sens = {}

    for name in sens.keys():
        data = [solution_times,]
        for idx in range(number_of_components):
            data.append(np.array(h5['/output/sensitivity/unit_001/%s/SENS_COLUMN_OUTLET_COMP_%03d' % (name, idx)]))
        data = np.transpose(np.vstack(data))
        #data = compress_series.compress(data)
        set_value(compress, name, 'f8', data)


def gen_bounds(lb, ub, base_value):
    if '%' in lb and '%' in ub:
        lb = float(lb.replace('%', ''))
        ub = float(ub.replace('%', ''))
        if lb < 0:
            lb = (100.0+lb)/100.0
            ub = (100.0+ub)/100.0
        else:
            lb = lb/100.0
            ub = ub/100.0
        lb = lb * base_value
        ub = ub * base_value
    else:
        ub = float(ub)
        lb = float(lb)
    return lb, ub


def generate_ranges(json_data):
    changed = [(key, value) for key,value in json_data.items() if key.startswith('choose_attributes')]

    ranges = {}

    for key,value in changed:
        base = key.replace('choose_attributes:', '')
        base_value = float(json_data[base])
        values = []
        if value == 'distribution':
            dist_type =  json_data['modify_dist_type:%s' % base]
            lb = json_data['modify_dist_lb:%s' % base]
            ub = json_data['modify_dist_ub:%s' % base]
            size = int(json_data['modify_dist_number:%s' % base])
            stdev = float(json_data.get('modify_dist_stdev:%s' % base, 1))
            lb, ub = gen_bounds(lb, ub, base_value)

            if dist_type == 'Random Uniform':
                values = random.uniform(lb, ub, size)
            elif dist_type == 'Linear':
                values = np.linspace(lb, ub, size, endpoint=True)
            elif dist_type == 'Truncated Random Normal':
                values = []
                while len(values) < size:
                    value = random.normal(base_value, stdev)
                    if lb < value < ub:
                        values.append(value)
            #print dist_type, base_value, values

        elif value == 'choose':
            values = map(float, json_data['modify_choice:%s' % base].split(','))
        if len(values):
            ranges[base] = list(values)
    json_data['batch_distribution'] = ranges.items()


def generate_permutations(json_data):
    keys, values = zip(*json_data['batch_distribution'])

    combos = []
    for value in itertools.product(*values):
        combos.append(value)
    return keys, combos


def generate_simulations(parent_dir, json_data):
    keys, combos = generate_permutations(json_data)

    try:
        os.mkdir(os.path.join(parent_dir, 'batch'))
    except OSError:
        pass

    components = get_components_in_order(json_data)

    for idx, value in enumerate(combos):
        temp = json_data.copy()
        temp.update(dict(zip(keys, value)))

        for key,val in zip(keys, value):
            temp[key] = val

            try:
                comp, isotherm = key.split(':')
            except ValueError:
                comp, isotherm = (None, None)

            if isotherm in utils.isotherm_name_set:
                #this is part of an isotherm so we have to treat it specially

                temp['CADET_ISOTHERM'][isotherm][components.index(comp)] = val

        try:
            os.mkdir(os.path.join(parent_dir, 'batch', str(idx)))
        except OSError:
            pass
        directory_path = os.path.join(parent_dir, 'batch', str(idx))
        create_simulation_file(directory_path, temp)


def write_progress(parent_dir, current, total):
    with open(os.path.join(parent_dir,'progress'), 'w') as progress:
        progress.write('%s of %s simulations completed (%.1f%%)' % (current, total, float(current)/total*100.0))


def run_batch_simulations(parent_dir, json_path):
    dirs = glob.glob(os.path.join(parent_dir, 'batch', '*'))
    dir_count = len(dirs)
    write_progress(parent_dir, 0, dir_count)

    total = settings.cpu

    for idx, dir_name in enumerate(dirs):
        h5_path = os.path.join(dir_name, 'sim3.h5')
        out = open(os.path.join(dir_name, 'stdout'), 'w')
        err = open(os.path.join(dir_name, 'stderr'), 'w')

        proc = subprocess.Popen(['python', __file__, '--json', json_path, '--sim', h5_path,], stdout=out, stderr=err, env=env)

        proc.wait()
        write_progress(parent_dir, idx+1, dir_count+1)


def failure(parent_dir, isBatch, job, url, stdout=None, stderr=None):
    data = {}
    data['complete'] = 1
    data['ok'] = 0
    
    data['stdout'] = stdout
    data['stderr'] = stderr

    try:
        data['cadet_version'] = str(np.array(h5['/meta/CADET_VERSION']))
        data['cadet_git_version'] = str(np.array(h5['/meta/CADET_COMMIT']))
    except (KeyError,ValueError):
        data['cadet_version'] = 'NOT FOUND'
        data['cadet_git_version'] = 'NOT FOUND'
        
    json_cache = os.path.join(parent_dir, 'json_cache')
    open(json_cache, 'wb').write(json.dumps(data))

    if not isBatch:
        data = urllib.urlencode({'job_id':args.job})
        urllib2.urlopen(url, data)

    sys.exit()


def gen_json_cache_init(parent_dir):
    "generate initial json cache"
    data = {}
    data['complete'] = 0
    data['ok'] = 0

    json_cache = os.path.join(parent_dir, 'json_cache')
    open(json_cache, 'wb').write(json.dumps(data))


def gen_json_cache_complete(parent_dir, h5, hdf5_path):
    "generate a finished json_cache"
    data = {}

    data['complete'] = 1
    data['ok'] = 1
    data['stdout'] = str(np.array(h5['/web/STDOUT']))
    data['stderr'] = str(np.array(h5['/web/STDERR']))
    data['prefix'] = ''
    data['cadet_version'] = str(np.array(h5['/meta/CADET_VERSION']))
    data['cadet_git_version'] = str(np.array(h5['/meta/CADET_COMMIT']))
        
    data['data'] = {}

    for key,value in h5['/web/GRAPHS/SINGLE'].items():
        value = str(np.array(value))
        id, title, data_sets = utils.call_plugin_by_name(value, 'graphing/single', 'get_data', hdf5_path)
        if data_sets:
            data['data'][id] = data_sets

    for key,value in h5['/web/GRAPHS/GROUP'].items():
        value = str(np.array(value))
        id, title, data_sets = utils.call_plugin_by_name(value, 'graphing/group', 'get_data', hdf5_path)
        if data_sets:
            data['data'][id] = data_sets

    for sensitivity_number in range(int(np.array(h5['/input/sensitivity/NSENS']))):
        id, title, data_sets = plot_sensitivity.get_data(hdf5_path, sensitivity_number)
        if data_sets:
            data['data'][id] = data_sets

    if data['data']:
        #process the dictionary into the interleaved format needed
        for id, data_sets in data['data'].items():
            for data_set in data_sets:
                time = list(data_set['data'][0])
                values = list(data_set['data'][1])
                data_set['data'] = zip(time, values)


    json_cache = os.path.join(parent_dir, 'json_cache')
    open(json_cache, 'wb').write(json.dumps(data))


if __name__ == '__main__':
    total = settings.cpu
    
    print "STARTING"

    args = run_args()
    json_data = open(args.json, 'rb').read()
    json_data = json.loads(json_data)
    json_data = utils.encode_to_ascii(json_data)

    isBatch = 'batch' in args.sim

    if args.sim:
        parent_dir = os.path.dirname(args.sim)
    else:
        parent_dir = os.path.dirname(args.json)
        file_path = create_simulation_file(parent_dir, json_data)
        args.sim = file_path

    start_processing = time.time()

    open(os.path.join(parent_dir, 'status'), 'w').write('working')
    
    if not isBatch:
        if json_data['job_type'] == 'batch':
            generate_simulations(parent_dir, json_data)
            run_batch_simulations(parent_dir, args.json)

    if not isBatch:
        write_progress(parent_dir, 0, 1)

    #run simulation
    start = time.time()
    #gen_json_cache_init(parent_dir)
    cadet_stdout = open(os.path.join(parent_dir, 'cadet_stdout'), 'w')
    cadet_stderr = open(os.path.join(parent_dir, 'cadet_stderr'), 'w')

    print [cadet_path, args.sim]
    proc = subprocess.Popen([cadet_path, args.sim], stdout=cadet_stdout, stderr=cadet_stderr, env=env)

    print "CADET RUNNING"

    def fail():
        proc.kill()
        return failure(parent_dir, isBatch, args.job, args.url_fail)

    timer = Timer(settings.cpu, fail)
    timer.start()

    proc.wait()
    timer.cancel()
    simulation_time = time.time() - start

    cadet_stdout.close()
    cadet_stderr.close()

    stdout = open(os.path.join(parent_dir, 'cadet_stdout'), 'r').read()
    stderr = open(os.path.join(parent_dir, 'cadet_stderr'), 'r').read()

    sys.stdout.write(stdout)
    sys.stderr.write(stderr)

    h5 = h5py.File(args.sim, 'a')
    web = h5["web"]
    set_value_enum(web, 'STDOUT', stdout)
    set_value_enum(web, 'STDERR', stderr)

    print "GENERATE GRAPHS"
    compress_data(h5)
    gen_json_cache_complete(parent_dir, h5, args.sim)

    try:
        compress_data(h5)
        gen_json_cache_complete(parent_dir, h5, args.sim)
    except KeyError:
        h5.close()
        failure(parent_dir, isBatch, args.job, args.url_fail, stdout, stderr)
    else:    

        print "FINISHED COMPRESSING DATA AND GENERATING JSON"

        h5.close()
        #run performance parameters
    
        #run graphs
        for key,value in json_data.items():
            if key.startswith('graph_single') and value == '1':
                _, name = key.split(':')
                print "GENERATING GRAPH", name
                utils.call_plugin_by_name(name, 'graphing/single', 'run', args.sim)

            if key.startswith('graph_group') and value == '1':
                _, name = key.split(':')
                utils.call_plugin_by_name(name, 'graphing/group', 'run', args.sim)

        for sensitivty_number in range(len(json_data.get("sensitivities", []))):
            plot_sensitivity.run(args.sim, sensitivty_number)

        if not isBatch:
            write_progress(parent_dir, 1, 1)

        processing_time = time.time() - start_processing

        h5 = h5py.File(args.sim, 'a')
        web = h5["web"]
        set_value(web, 'CADET_SIMULATION_TIME', 'f8', simulation_time)
        set_value(web, 'TOTAL_RUN_TIME', 'f8', processing_time)
        h5.close()

        if not isBatch:
            data = urllib.urlencode({'job_id':args.job})
            urllib2.urlopen(args.url_pass, data)

        open(os.path.join(parent_dir, 'status'), 'w').write('success')
