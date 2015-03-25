from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators import gzip
from django.core.exceptions import ObjectDoesNotExist

import models

import json
import hashlib
import subprocess
import os
import itertools
import urllib
import csv
import h5py
import plot_sensitivity
import cadet_runner
import utils
import numpy as np

#These are the default values for CADET that are put into the forms as a default
default_value = {}
default_value['NCOMP'] ='4'
default_value['NSEC'] = '4'
default_value['GS_TYPE'] = '1'
default_value['MAX_KRYLOV'] = '0'
default_value['MAX_RESTARTS'] = '0'
default_value['SCHUR_SAFETY'] = '1E-8'
default_value['ABSTOL'] = '1E-10'
default_value["INIT_STEP_SIZE"] = '1E-11'
default_value['MAX_STEPS'] = "100000"
default_value['RELTOL'] = "1E-12"
default_value['NCOL'] = '16'
default_value['NPAR'] = '4'
default_value['PAR_DISC_VECTOR_1'] = '0'
default_value['PAR_DISC_VECTOR_2'] = '0.5'
default_value['PAR_DISC_VECTOR_3'] = '1'
default_value['BOUNDARY_MODEL'] = '0'
default_value['WENO_EPS'] = '1E-12'
default_value['WENO_ORDER'] = '3'
default_value['NTHREADS'] = '4'

current_path = __file__
simulation_path, current_file_name = os.path.split(current_path)
parent_path, _ = simulation_path.rsplit('/', 1)

storage_path = os.path.join(parent_path, 'sims')

cadet_runner_path = os.path.join(parent_path, 'cadet_runner.py')

cadet_plugin_path = '..'

def get_json(post):
    temp = {}
    json_dict = get_json_dict(post)
    json_table = get_json_table_dict(post)

    if json_table:
        #clean out json_dict of sensitivities
        for key in json_dict.keys():
            if key.startswith( ('tol', 'dist', 'choice'),):
                del json_dict[key]

    temp.update(json_dict)
    temp.update(json_table)
    temp.update(post.dict())

    #remove fields that should not be persisted
    for name in ('json', 'table', 'csrfmiddlewaretoken'):
        try:
            del temp[name]
        except KeyError:
            pass

    return temp

def get_json_dict(post):
    temp = {}
    json_form_data = post.get('json', None)
    if json_form_data is not None:
        temp.update(json.loads(json_form_data.replace("'", '"')))
    return temp

def get_json_table_dict(post):
    temp = {}
    json_form_data = post.get('table', None)
    if json_form_data:
        temp.update(json.loads(json_form_data.replace("'", '"')))
    return temp

def get_json_string(data):
    return json.dumps(data).replace('"', "'")

def generate_column_table(list_of_names, data):
    html = ['<div class="row"><div class="col-md-12"><table class="table"><thead><tr><th>#</th>']
    for name in list_of_names:
        html.append('<th>%s</th>' % name)

    html.append('</tr></thead><tbody>')

    vals = ( ('FILM_DIFFUSION', 'Film Diffusion'),
             ("INIT_C", 'Initial Mobile Concentration'),
             ('INIT_Q', 'Initial Bound Concentration'),
             ("PAR_DIFFUSION", 'Particle Diffusion'),
             ('PAR_SURFDIFFUSION', 'Particle Surface Diffusion'), )

    for attribute, title in vals:
        html.append('<tr><td>%s</td>' % title)
        for name in list_of_names:
            value = data.get('%s:%s' % (name, attribute), '0')
            html.append('<td><input type="text" class="required" name="%s:%s" value="%s"></td>' % (name, attribute, value))
        html.append('</tr>')
    html.append('</tbody></table></div></div>')

    html = '\n'.join(html)
    return html

def generate_step_settings(step, list_of_names, data):
    html = ['<table class="table wide"><thead><tr><th>#</th>']
    for name in list_of_names:
        html.append('<th>%s</th>' % name)

    html.append('</tr></thead><tbody>')

    vals = ( ('CONST_COEFF', 'Constant'),
             ('LIN_COEFF', "Linear"),
             ('QUAD_COEFF', 'Quadratic'),
             ('CUBE_COEFF', "Cubic"), )

    for attribute, title in vals:
        html.append('<tr><td>%s</td>' % title)
        for name in list_of_names:
            value = data.get("%s:%s:%s" % (step, name, attribute), '0')
            html.append('<td><input type="text" class="required" name="%s:%s:%s" value="%s"></td>' % (step, name, attribute, value))
        html.append('</tr>')
    html.append('</tbody></table>')

    html = '\n'.join(html)
    return html
def index(request):
    context = {}
    return render(request, 'simulation/index.html', context)

@login_required
def single_start(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    if 'path' in request.GET and 'chunk_size' in request.GET:
        path = request.GET['path']
        chunk_size =int(request.GET['chunk_size'])

        relative_parts = [''.join(i for i in seq if i is not None) for seq in utils.grouper(path, chunk_size)]
        relative_path = os.path.join(*relative_parts)

        json_data = open(os.path.join(storage_path, relative_path, 'setup.json'), 'rb').read()

        json_data = json.loads(json_data)
        json_data = utils.encode_to_ascii(json_data)
        data.update(json_data)

    isotherms = utils.get_plugin_names('isotherm')
    isotherms = [(isotherm, 'selected' if isotherm == data.get('ADSORPTION_TYPE', None) else '') for isotherm in isotherms]
    data['isotherms'] = isotherms
    data['json'] = get_json_string(data)
    return render(request, 'simulation/single_start.html', data)

@login_required
def component_and_step_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    components = int(data.get('NCOMP', ''))
    steps = int(data.get('NSEC', ''))


    comps = [(i, data.get('component%s' % i, '')) for i in range(2, int(data.get('NCOMP', ''))+1)]
    steps = [(i, data.get('step%s' % i, '')) for i in range(1, int(data.get('NSEC', ''))+1)]

    data['json'] = get_json_string(data)
    data['comps'] = comps
    data['steps'] = steps
    data['back'] = reverse('simulation:single_start', None, None)
    data['back_text'] = 'The Beginning'
    return render(request, 'simulation/component_and_step_setup.html', data)

@login_required
def isotherm_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    isotherm_name = data.get('ADSORPTION_TYPE')
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]

    data['json'] = get_json_string(data)
    data['isotherm'] =  utils.call_plugin_by_name(isotherm_name, 'isotherm', 'run', list_of_names, data)
    data['back'] = reverse('simulation:component_and_step_setup', None, None)
    data['back_text'] = 'Component and Step Setup'
    return render(request, 'simulation/isotherm_setup.html', data)

@login_required
def column_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    isotherm_name = data.get('ADSORPTION_TYPE')
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
    if 'CADET_ISOTHERM' not in data:
        data['CADET_ISOTHERM'] = utils.call_plugin_by_name(isotherm_name, 'isotherm', 'process_form', list_of_names, post)

    data['json'] = get_json_string(data)
    data['column_table'] = generate_column_table(list_of_names, data)
    data['back'] = reverse('simulation:isotherm_setup', None, None)
    data['back_text'] = 'Isotherm Setup'
    return render(request, 'simulation/column_setup.html', data)

@login_required
def loading_setup(request):

    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
    list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    data['json'] = get_json_string(data)
    values = [generate_step_settings(step, list_of_names, data) for step in list_of_steps]
    data['steps'] = zip(list_of_steps, values)

    #This flattens out the array and django needs that to render properly
    continuous = [(idx, first, second) for idx, (first, second) in enumerate(zip(list_of_steps[:-1], list_of_steps[1:]))]
    continuous = [(idx, first, second, 'checked' if data.get('continuous_%s' % idx, '') == '1' else '', '' if data.get('continuous_%s' % idx, '') == '1' else 'checked') for (idx, first, second) in continuous]

    data['continuous'] = continuous
    step_times = ['Start:' + step for step in list_of_steps] + ['End:' + list_of_steps[-1]]
    data['step_times'] = [(name.replace(':', ' '), name, data.get(name, '0')) for name in step_times]
    data['back'] = reverse('simulation:column_setup', None, None)
    data['back_text'] = 'Column Setup'

    return render(request, 'simulation/loading_setup.html', data)

@login_required
def simulation_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    data['json'] = get_json_string(data)
    data['rate_models'] = nice_names(['GENERAL_RATE_MODEL',], data, 'CHROMATOGRAPHY_TYPE')
    data['discretizations'] = nice_names(['EQUIDISTANT_PAR', 'EQUIVOLUME_PAR', 'USER_DEFINED_PAR'], data, 'PAR_DISC_TYPE')
    data['reconstructions'] = nice_names(['WENO'], data, 'RECONSTRUCTION')
    data['log_levels'] = nice_names(['ERROR', 'WARNING', 'INFO', 'DEBUG1', 'DEBUG2', 'TRACE1', 'TRACE2'], data, 'LOG_LEVEL')
    data['radios'] = fix_radio([ ('Print Config', 'PRINT_CONFIG','0'),
                        ('Print Parameter List', 'PRINT_PARAMLIST','0'),
                        ('Print Progress', 'PRINT_PROGRESS','0'),
                        ('Print Statistics', 'PRINT_STATISTICS','1'),
                        ('Print Timing', 'PRINT_TIMING','1'),
                        ('Use Analytical Jacobian', 'USE_ANALYTIC_JACOBIAN','1'),
                        ('Write at User Times', 'WRITE_AT_USER_TIMES','0'),
                        ('Write All Sensitivities', 'WRITE_SENS_ALL','0'),
                        ('Write Sensitivity at Column Outlet', 'WRITE_SENS_COLUMN_OUTLET','0'),
                        ('Write Solution All', 'WRITE_SOLUTION_ALL','0'),
                        ('Write Solution Column Inlet', 'WRITE_SOLUTION_COLUMN_INLET','1'),
                        ('Write Solution Column Outlet', 'WRITE_SOLUTION_COLUMN_OUTLET','1'),
                        ('Write Solution Times', 'WRITE_SOLUTION_TIMES','1')], data)
    data['back'] = reverse('simulation:loading_setup', None, None)
    data['back_text'] = 'Loading Setup'

    return render(request, 'simulation/simulation_setup.html', data)

@login_required
def graph_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    data['json'] = get_json_string(data)
    data['graph_single'] = [(name, 'checked' if data.get('graph_single:%s' % name, '')  == '1' else '', '' if data.get('graph_single:%s' % name, '')  == '1' else 'checked') for name in sorted(utils.get_plugin_names('graphing/single'))]
    data['graph_group'] = [(name, 'checked' if data.get('graph_group:%s' % name, '') == '1' else '', '' if data.get('graph_group:%s' % name, '') == '1' else 'checked') for name in sorted(utils.get_plugin_names('graphing/group'))]
    data['job_type'] = data['job_type']
    data['back'] = reverse('simulation:simulation_setup', None, None)
    data['back_text'] = 'Simulation Setup'
    return render(request, 'simulation/graph_setup.html', data)

@login_required
def performance_parameters(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    data['json'] = get_json_string(data)
    data['perf_single'] = [(name, 'checked' if data.get('perf_single:%s' % name, '')  == '1' else '', '' if data.get('perf_single:%s' % name, '')  == '1' else 'checked') for name in sorted(utils.get_plugin_names('performance/single'))]
    data['perf_group'] = [(name, 'checked' if data.get('perf_group:%s' % name, '')  == '1' else '', '' if data.get('perf_group:%s' % name, '')  == '1' else 'checked') for name in sorted(utils.get_plugin_names('performance/group'))]
    data['job_type'] = data['job_type']
    data['back'] = reverse('simulation:graph_setup', None, None)
    data['back_text'] = 'Graph Setup'

    return render(request, 'simulation/performance_parameters.html', data)

@login_required
def sensitivity_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
    list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    sensitivities = []
    with open(os.path.join(parent_path,'sensitivity.csv'), 'rb') as csvfile:
        reader = csv.reader(csvfile)
        sensitivities = [row for row in reader]

    header = sensitivities[0]
    sensitivities = sensitivities[1:]

    isotherm_name = data.get('ADSORPTION_TYPE')
    sens = utils.call_plugin_by_name(isotherm_name, 'isotherm', 'sensitivity')
    sensitivities.extend(sens)

    ABS_TOL = float(data['ABSTOL'])

    entry = []
    for sensitivity in sensitivities:
        name, per_component, per_section, description = sensitivity
        if per_component == '1' and per_section == '1':
            seq = itertools.product(list_of_names, list_of_steps)
        elif per_component == '0' and per_section == '1':
            seq = itertools.product(itertools.repeat('', 1), list_of_steps)
        elif per_component == '1' and per_section == '0':
            seq = itertools.product(list_of_names, itertools.repeat('', 1))
        else:
            seq = [ ('',''), ]
        for component, section in seq:
            #value = 1.0
            if name and component and section:
                value = float(data['%s:%s:%s' % (section, component, name)])
            elif name and component:
                value = float(data['%s:%s' % (component, name)])
            else:
                value = 0

            try:
                default = ABS_TOL/value
            except ZeroDivisionError:
                default = 0
            form_name = ':'.join([i for i in name, component, section])
            entry.append( (
                'choice:%s' % (form_name),
                'checked' if data.get('choice:%s' % (form_name), '') == '1' else '',
                name,
                component,
                section,
                description,
                'tol:%s' % (form_name),
                data.get('tol:%s' % (form_name), '%.3g' % default),
                'dist:%s' % (form_name),
                data.get('dist:%s' % (form_name), '0.01'),
            )
            )

    data['json'] = get_json_string(data)
    data['sensitivities'] = utils.get_plugin_names('sensitivity')
    data['entry'] = entry
    data['back'] = reverse('simulation:performance_parameters', None, None)
    data['back_text'] = 'Performance Parameters Setup'
    return render(request, 'simulation/sensitivity_setup.html', data)

@login_required
def job_setup(request):
    post = request.POST

    data = get_json(post)
    table_data = get_json_table_dict(post)

    keep = set()
    sensitivities = []

    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
    list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    for key,value in data.items():
        if key.startswith('choice'):
            type, name = key.split(':', 1)
            keep.add(name)


    for name in keep:
        tol = data['dist:%s' % name]
        dist = data['dist:%s' % name]

        name, component, section = name.split(':')


        SENS_NAME = name

        try:
            SENS_COMP = list_of_names.index(component)
        except ValueError:
            SENS_COMP = -1

        try:
            SENS_SECTION = list_of_steps.index(section)
        except ValueError:
            SENS_SECTION = -1

        SENS_ABSTOL = float(tol)
        SENS_FD_DELTA = float(dist)

        sensitivity = {}
        sensitivity['SENS_NAME'] = SENS_NAME
        sensitivity['SENS_COMP'] = SENS_COMP
        sensitivity['SENS_SECTION'] = SENS_SECTION
        sensitivity['SENS_ABSTOL'] = SENS_ABSTOL
        sensitivity['SENS_FD_DELTA'] = SENS_FD_DELTA

        sensitivities.append(sensitivity)


    data['sensitivities'] = sensitivities
    try:
        del data['table']
    except KeyError:
        pass

    data['CADET_ISOTHERM'] = utils.call_plugin_by_name(data.get('ADSORPTION_TYPE'), 'isotherm', 'process_form', list_of_names, data)

    context = {'json':get_json_string(data),
               'back':reverse('simulation:sensitivity_setup', None, None),
            'back_text':'Sensitivity Setup'}
    return render(request, 'simulation/job_setup.html', context)

@login_required
def confirm_job(request):
    post = request.POST
    data = get_json(post)

    data['json'] = get_json_string(data)
    data['back'] = reverse('simulation:job_setup', None, None)
    data['back_text'] = 'Job Setup'
    return render(request, 'simulation/confirm_job.html', data)



@login_required
def generate_other_graphs(request):
    context = {}
    return render(request, 'simulation/generate_other_graphs.html', context)

@login_required
def run_job_get(request):
    path = request.GET['path']
    chunk_size =int(request.GET['chunk_size'])

    json_path, hdf5_path, graphs, json_data = utils.get_graph_data(path, chunk_size)

    query = request.GET.dict()
    query = urllib.urlencode(query)
    base = reverse('simulation:single_start', None, None)
    url_new = '%s?%s' % (base, query)

    data = {}
    data['graphs'] = graphs

    #FIXME: need to change the path so that this works. Needs to be path to /static/simulations/sims/...
    data['download_url'] = hdf5_path
    data['new_simulation'] = url_new
    data['path'] = path
    data['chunk_size'] = chunk_size
    data['json_url'] = reverse('simulation:get_data', None, None)
    return render(request, 'simulation/run_job.html', data)

@login_required
def run_job(request):
    post = request.POST
    data = get_json(post)

    json_data = get_json_string(data)
    check_sum = hashlib.sha256(json_data).hexdigest()

    group_size = 20

    relative_parts = [storage_path,] + [''.join(i for i in seq if i is not None) for seq in utils.grouper(check_sum, group_size)]
    relative_path = os.path.join(*relative_parts)

    try:
        os.makedirs(relative_path)
    except OSError:
        print "The simulation has already been run."

    path = os.path.join(relative_path, 'setup.json')

    json.dump(data, open(path, 'w'))
    out = open(os.path.join(relative_path, 'stdout'), 'w')
    err = open(os.path.join(relative_path, 'stderr'), 'w')
    simulation_path = cadet_runner.create_simulation_file(relative_path, data)

    write_job_to_db(data, json_data, check_sum)

    subprocess.Popen(['python', cadet_runner_path, '--json', path, '--sim', simulation_path,], stdout=out, stderr=err)

    query = {}
    query['path'] = check_sum
    query['chunk_size'] = group_size
    query = urllib.urlencode(query)
    base = reverse('simulation:run_job_get', None, None)
    return redirect('%s?%s' % (base, query))

def write_job_to_db(data, json_data, check_sum):
    #first check if we already have this entry

    #FIXME: ONLY FOR TESTING WIPES THE DB ENTRY EACH TIME
    try:
        job = models.Job.objects.get(uid=check_sum)
        job.delete()
        #[job.delete() for job in models.Job.objects.all()]
    except ObjectDoesNotExist:
        #create job type if it dies not exist
        pass

    try:
        job = models.Job.objects.get(uid=check_sum)
    except ObjectDoesNotExist:
        #create job type if it dies not exist
        try:
            job_type = models.Job_Type.objects.get(type=data['job_type'])
        except ObjectDoesNotExist:
            job_type = models.Job_Type.objects.create(type=data['job_type'])

        #create product type if it does not exist
        try:
            product = models.Products.objects.get(product=data['product'])
        except ObjectDoesNotExist:
            product = models.Products.objects.create(product=data['product'])


        #create model type if it dies not exist
        try:
            model = models.Models.objects.get(model=data['model_name'])
        except ObjectDoesNotExist:
             model = models.Models.objects.create(model=data['model_name'])


        list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
        list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

        #create job
        job = models.Job.objects.create(Product_ID = product,
            Job_Type_ID = job_type,
            Model_ID = model,
            study_name = data['study_name'],
            json = json_data,
            uid = check_sum)

        #create components
        comps = [models.Components.objects.create(Job_ID=job, Component=comp) for comp in list_of_names]
        #virtual component that has all column properties
        comps.insert(0, models.Components.objects.create(Job_ID=job, Component='Column'))


        #create steps
        steps = [models.Steps.objects.create(Job_ID=job, Step=step) for step in list_of_steps]
        #virtual step that contains all the Setup stuff and simulation settings
        steps.insert(0, models.Steps.objects.create(Job_ID=job, Step='Setup'))

        #create settings at each step
        #only writing parameters that could remotely make sense to search. This means the vector fields, sensitivities,
        # and similar things are not stored separately

        with open(os.path.join(parent_path,'parms.csv'), 'rb') as csvfile:
            reader = csv.reader(csvfile)
            #read the header and discard it
            reader.next()
            for name, units, type, per_component, per_section, sensitive, description  in reader:
                per_component = int(per_component)
                per_section = int(per_section)
                sensitive = int(sensitive)

                if type in ('int', 'string', 'double'):
                    if per_component and per_section:
                        db_add_comp_and_section(name, type, data, steps, comps, job)
                    elif per_component and not per_section:
                        db_add_comp(name, type, data, steps[0], comps, job)
                    elif per_section and not per_component:
                        pass #we don't have any of these but leave this here in case it happens later
                    else:
                        db_add_var(name, name, type, data, steps[0], comps[0], job)


                #create isotherm line if it dies not exist
                try:
                    models.Parameters.objects.get(name=name)
                except ObjectDoesNotExist:
                    models.Parameters.objects.create(name=name, units=units, description=description)


def db_add_comp_and_section(name, type, data, steps, comps, job):
    #skip the first component since it is the column
    #spip the first step since it is for setup
    for step in steps[1:]:
        for comp in comps[1:]:
            lookup = '%s:%s:%s' % (step.Step, comp.Component, name)
            db_add_var(lookup, name, type, data, step, comp, job)

def db_add_comp(name, type, data, step, comps, job):
    #skip the first component since it is the column
    for comp in comps[1:]:
        lookup = '%s:%s' % (comp.Component, name)
        db_add_var(lookup, name, type, data, step, comp, job)

def db_add_var(lookup, name, type, data, step, comp, job):
    try:
        model_args = {}
        model_args['Step_ID'] = step
        model_args['Parameter_ID'] = models.Parameters.objects.get(name=name)
        model_args['Component_ID'] = comp
        model_args['Job_ID'] = job


        if type == 'int':
            model_args['Data'] = int(data[lookup])
            models.Job_Int.objects.create(**model_args)

        elif type == 'string':
            model_args['Data'] = data[lookup]
            models.Job_String.objects.create(**model_args)

        elif type == 'double':
            model_args['Data'] = float(data[lookup])
            models.Job_Double.objects.create(**model_args)
        #print 'Found', lookup, lookup in data
    except KeyError:
        #print 'Missing', lookup, lookup in data
        pass

@login_required
def sync_db(request):
    with open(os.path.join(parent_path,'iso.csv'), 'rb') as csvfile:
        reader = csv.reader(csvfile)
        #read the header and discard it
        reader.next()
        for name, isotherm in reader:
            #create isotherm line if it dies not exist
            try:
                models.Isotherms.objects.get(Name = name, Isotherm=isotherm)
            except ObjectDoesNotExist:
                models.Isotherms.objects.create(Name = name, Isotherm=isotherm)


    with open(os.path.join(parent_path,'parms.csv'), 'rb') as csvfile:
        reader = csv.reader(csvfile)
        #read the header and discard it
        reader.next()
        for name, units, type, per_component, per_section, sensitive, description  in reader:
            #create isotherm line if it dies not exist
            try:
                models.Parameters.objects.get(name=name, units=units, description=description)
            except ObjectDoesNotExist:
                models.Parameters.objects.create(name=name, units=units, description=description)
    return render(request, 'simulation/sync_db.html', {})

@login_required
@gzip.gzip_page
def get_data(request):
    """This function has to call an external process because of scipy. DO NOT MERGE that code into here. It causes apache
    to deadlock and go into some kind of memory allocation loop. I tried many different options but none worked. Instead
    will pass the needed json to an external process and then read the result back."""
    json_data = {}
    path = request.GET['path']
    chunk_size =int(request.GET['chunk_size'])

    json_path, hdf5_path, graphs, data = utils.get_graph_data(path, chunk_size)

    h5 = h5py.File(hdf5_path, 'r')

    #check for success by seeing if we have output created
    try:
        h5['/output/solution/SOLUTION_TIMES']
        success = 1
    except KeyError:
        success = 0
    json_data['success'] = success

    #close the hdf5 file
    h5.close()

    if success:
        #if success get the step names and times
        section_times = cadet_runner.get_section_times(data)
        section_names = cadet_runner.get_step_names(data)
        times = zip(section_names, section_times[:-1])
        times.append( ('End', section_times[-1]), )
        json_data['times'] = times



        json_data['data'] = {}
        #run graphs
        for key,value in data.items():
            if key.startswith('graph_single') and value == '1':
                _, name = key.split(':')
                id, title, data_sets = utils.call_plugin_by_name(name, 'graphing/single', 'get_data', hdf5_path)
                if data_sets:
                    json_data['data'][id] = data_sets

            if key.startswith('graph_group') and value == '1':
                _, name = key.split(':')
                id, title, data_sets = utils.call_plugin_by_name(name, 'graphing/group', 'get_data', hdf5_path)
                if data_sets:
                    json_data['data'][id] = data_sets

        for sensitivity_number in range(len(data.get("sensitivities", []))):
            id, title, data_sets = plot_sensitivity.get_data(hdf5_path, sensitivity_number)
            if data_sets:
                json_data['data'][id] = data_sets

        if json_data['data']:
            #hand off to subprocess
            json_string = get_json_string(json_data)
            #open('/tmp/data.json', 'w').write(json_string)
            compress = os.path.join(parent_path, 'compress_series.py')
            p = subprocess.Popen(['python', compress], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate(input=json_string)
            #open('/tmp/data3.json', 'w').write(stdout)

            #get data back from subprocess and turn it into a dictionary again
            json_data = json.loads(stdout.replace("'", '"'))

            #process the dictionary into the interleaved format needed
            for id, data_sets in json_data['data'].items():
                for data_set in data_sets:
                    time = list(data_set['data'][0])
                    values = list(data_set['data'][1])
                    data_set['data'] = zip(time, values)

    return JsonResponse(json_data, safe=False)

@login_required
@gzip.gzip_page
def inlet_graph(request):
    post = request.POST
    data = get_json(post)

    section_times = cadet_runner.get_section_times(data)
    components = [data.get('component%s' % i) for i in range(1, int(data.get('NCOMP', ''))+1)]
    steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    json_data = []
    for component in components:
        temp = {}
        temp['label'] = component
        temp_data = []
        for idx, step in enumerate(steps):
            constant = float(data['%s:%s:CONST_COEFF' % (step, component)])
            linear = float(data['%s:%s:LIN_COEFF' % (step, component)])
            quadratic = float(data['%s:%s:QUAD_COEFF' % (step, component)])
            cubic = float(data['%s:%s:CUBE_COEFF' % (step, component)])
            start = section_times[idx]
            stop = section_times[idx+1]

            if cubic or quadratic:
                times = np.linspace(0, stop-start, endpoint=True)
                values = constant + linear*times + quadratic*times**2 + cubic*times**3
                times = times + start
                temp_data.extend(zip(times.tolist(), values.tolist()))

            else:
                times = np.array([0, stop-start])
                values = constant + linear*times
                times = times + start
                temp_data.extend(zip(times.tolist(), values.tolist()))
        temp['data'] = temp_data
        json_data.append(temp)

    return JsonResponse(json_data, safe=False)

def nice_names(seq, data, name):
    return [(i.replace('_', ' ').title(), i, 'selected' if data.get(name) == i else '') for i in seq]

def fix_radio(seq, data):
    temp = []
    for label, name, value in seq:
        value = data.get(name, value)
        if value == '1':
            yes = 'checked="checked"'
            no = ''
        else:
            yes = ''
            no = 'checked="checked"'
        temp.append( (label, name, yes, no))
    return temp

@login_required
def choose_attributes_to_modify(request):

    post = request.POST
    data = get_json_dict(post)

    context = {'json':get_json_string(data),
              'modifies': utils.get_plugin_names('modify')}
    return render(request, 'simulation/choose_attributes_to_modify.html', context)

@login_required
def choose_search_query(request):

    post = request.POST
    data = get_json_dict(post)

    context = {'json':get_json_string(data),
              'queries': utils.get_plugin_names('search')}

    return render(request, 'simulation/choose_search_query.html', context)

@login_required
def create_batch_simulation(request):

    context = {}
    return render(request, 'simulation/create_batch_simulation.html', context)

@login_required
def modify_attributes(request):

    post = request.POST
    data = get_json_dict(post)
    context = {'json':get_json_string(data)}
    choose_attributes = [(key,value) for (key,value) in data.items() if 'choose_attributes_' in key]
    context['choices'] = [key.replace('choose_attributes_', '') for (key, value) in choose_attributes if value == 'choose']
    context['linears'] = [key.replace('choose_attributes_', '') for (key, value) in choose_attributes if value == 'linear']
    context['randoms'] = [key.replace('choose_attributes_', '') for (key, value) in choose_attributes if value == 'random']
    return render(request, 'simulation/modify_attributes.html', context)

@login_required
def query_options(request):

    post = request.POST
    data = get_json_dict(post)
    context = {'json':get_json_string(data),
              'query': data['search_query'],
              'query_form':utils.call_plugin_by_name(data['search_query'], 'search', 'run')}

    return render(request, 'simulation/query_options.html', context)

@login_required
def query_results(request):

    post = request.POST
    data = get_json_dict(post)
    results = utils.call_plugin_by_name(data['search_query'], 'search', 'process_search', data)
    search_results = []
    for result in results[1:]:
        # (Job ID, Study Name, Model Name, Isotherm, [list of additional headers], rating
        #will have a search function here later that gathers up all the info we need from a jobid
        jobid = result[0]
        study_name = 'test'
        model_name = 'test2'
        isotherm = 'test3'
        additional = result[1:]
        rating = 3.5
        search_results.append([jobid, study_name, model_name, isotherm, additional, rating])
    headers = results[0][1:]
    context = {'json':get_json_string(data),
              'search_results':search_results,
              'headers':headers}
    return render(request, 'simulation/query_results.html', context)


