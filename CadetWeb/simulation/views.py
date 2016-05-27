from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators import gzip
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

import settings

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
import operator
import resource
from django.http import HttpResponse
from datetime import datetime, timedelta
import shutil
from collections import OrderedDict
import glob

class HttpResponseTemporaryRedirect(HttpResponse):
    status_code = 307

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = redirect_to



#These are the default values for CADET that are put into the forms as a default
default_value = {}
default_value['numberOfComponents'] ='1'
default_value['NSEC'] = '1'
default_value['GS_TYPE'] = '1'
default_value['MAX_KRYLOV'] = '0'
default_value['MAX_RESTARTS'] = '0'
default_value['SCHUR_SAFETY'] = '1E-8'
default_value['ABSTOL'] = '1E-8'
default_value["INIT_STEP_SIZE"] = '0.0'
default_value['MAX_STEPS'] = "0"
default_value['RELTOL'] = "0.0"
default_value['NCOL'] = '16'
default_value['NPAR'] = '4'
default_value['PAR_DISC_VECTOR_1'] = '0'
default_value['PAR_DISC_VECTOR_2'] = '0.5'
default_value['PAR_DISC_VECTOR_3'] = '1'
default_value['BOUNDARY_MODEL'] = '0'
default_value['WENO_EPS'] = '1E-12'
default_value['WENO_ORDER'] = '3'
default_value['NTHREADS'] = '4'
default_value['LOG_LEVEL'] = '4'
default_value['advanced_ui'] = 'normal'
default_value['graph_single:Chromatogram'] = '1'

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
            if key.startswith( ('tol:', 'dist:', 'choice:'),):
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

    vals = ( "INIT_C", 'INIT_Q', 'FILM_DIFFUSION', "PAR_DIFFUSION", 'PAR_SURFDIFFUSION' )

    for attribute in vals:
        human_name, tooltip, units = utils.name_lookup_python[attribute]
        html.append('<tr><td data-toggle="tooltip" data-placement="bottom" title="%s">%s (%s) </td>' % (tooltip, human_name, units) )
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

    vals = ( ( 'CONST_COEFF', ''),
             ('LIN_COEFF', ''),
             ('QUAD_COEFF', 'advanced'),
             ('CUBE_COEFF', 'advanced'), )

    for attribute, cssClass in vals:
        human_name, tooltip, units = utils.name_lookup_python[attribute]

        html.append('<tr class="%s"><td data-toggle="tooltip" data-placement="bottom" title="%s">%s </td>' % (cssClass, tooltip, human_name) )
        for name in list_of_names:
            value = data.get("%s:%s:%s" % (step, name, attribute), '0')
            html.append('<td><input type="text" class="required" name="%s:%s:%s" value="%s"></td>' % (step, name, attribute, value))
        html.append('</tr>')
    html.append('</tbody></table>')

    html = '\n'.join(html)
    return html


def index(request):
    context = {}

    context['search_examples'] = get_examples(5)
    context['search_history'] = get_most_recent_simulations(request.user.username, 5)

    return render(request, 'simulation/index.html', context)


#@login_required
def remove_old_simulations():
    jobs = models.Job.objects.filter(created__lte=datetime.now()-timedelta(days=settings.keep_time))
    
    removed = 0
    for job in jobs:
        if job.username not in settings.users_keep:
            delete_job(job.uid)
            removed = removed + 1

    # for root, dirs, files in os.walk(storage_path, topdown=False):
    #     print root, dirs, files
    #     # if a directory is empty there will be no sub-directories or files
    #     if len(dirs) is 0 and len(files) is 0 and len(root) > len(storage_path) and root.startswith(storage_path):
    #         shutil.rmtree(root)

    #data = {}
    #data['removed'] = removed

    #return render(request, 'simulation/remove_old.html', data)

def delete_job(uid):
    "delete this job from the system"
    #delete job from database
    models.Job.objects.filter(uid=uid).delete()

    #delete job from filesystem
    relative_parts = [''.join(i for i in seq if i is not None) for seq in utils.grouper(uid, settings.chunk_size)]
    relative_path = os.path.join(*relative_parts)
    path = os.path.join(storage_path, relative_path)
    shutil.rmtree(path)

    for idx in reversed(range(len(relative_parts))):
        try:
            os.rmdir(os.path.join(storage_path, *relative_parts[0:idx]))
        except:
            pass


def get_examples(limit):
    "return the the limit most recent 5 star simulations"
    "format is study name, model name, isotherm, results link, create link, create batch link"
    results = models.Job.objects.filter(username='cadet', job_notes__rating=5).select_related('job_notes').order_by('-created')[:limit]
    parameter = models.Parameters.objects.get(name='ADSORPTION_TYPE')

    temp = []
    for result in results:
        study_name= result.study_name
        model_name = result.Model_ID.model
        isotherm = models.Job_String.objects.get(Job_ID=result, Parameter_ID=parameter).Data.replace('_', ' ').title()
        results_link = reverse('simulation:run_job_get', None, None) + "?path=%s" % result.uid
        create_single = reverse('simulation:single_start', None, None) + "?path=%s" % result.uid
        create_batch = reverse('simulation:choose_attributes_to_modify', None, None) + "?path=%s" % result.uid
        created = result.created
        simulation_path = utils.get_hdf5_path(result.uid, settings.chunk_size, None)
        simulation_path = '/static/simulation/sims/' + simulation_path.replace(utils.storage_path, '')
        try:
            note = result.job_notes.notes
        except models.Job_Notes.DoesNotExist:
            note = ''
        temp.append([study_name, model_name, isotherm, results_link, create_single, create_batch, created, simulation_path, note])
    return temp

def get_most_recent_simulations(username, limit):
    "return a list of the most recent simulations run by the user in username"
    "format is study name, model name, isotherm, results link, create link, create batch link"
    print username, limit
    if username:
        results = models.Job.objects.filter(username=username).select_related('job_notes').order_by('-created')[:limit]
        parameter = models.Parameters.objects.get(name='ADSORPTION_TYPE')

        temp = []
        for result in results:
            study_name= result.study_name
            model_name = result.Model_ID.model
            isotherm = models.Job_String.objects.get(Job_ID=result, Parameter_ID=parameter).Data
            results_link = reverse('simulation:run_job_get', None, None) + "?path=%s" % result.uid
            create_single = reverse('simulation:single_start', None, None) + "?path=%s" % result.uid
            create_batch = reverse('simulation:choose_attributes_to_modify', None, None) + "?path=%s" % result.uid
            created = result.created
            simulation_path = utils.get_hdf5_path(result.uid, settings.chunk_size, None)
            simulation_path = '/static/simulation/sims/' + simulation_path.replace(utils.storage_path, '')
            try:
                note = result.job_notes.notes
            except models.Job_Notes.DoesNotExist:
                note = ''
            temp.append([study_name, model_name, isotherm, results_link, create_single, create_batch, created, simulation_path, note])
        return temp
    else:
        return []

@login_required
def single_start(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    
    if 'path' in request.GET:
        path = request.GET['path']

        relative_parts = [''.join(i for i in seq if i is not None) for seq in utils.grouper(path, settings.chunk_size)]
        relative_path = os.path.join(*relative_parts)

        json_data = open(os.path.join(storage_path, relative_path, 'setup.json'), 'rb').read()

        json_data = json.loads(json_data)
        json_data = utils.encode_to_ascii(json_data)
        data.update(json_data)


    isotherm = data.get('ADSORPTION_TYPE', None)
    numberOfComponents = data.get('numberOfComponents', None)

    if isotherm in ('EXTERNAL_STERIC_MASS_ACTION', 'STERIC_MASS_ACTION', 'SELF_ASSOCIATION') and numberOfComponents > 1:
        data['numberOfComponents'] = numberOfComponents - 1


    isotherms = utils.isotherm_set.keys()

    isotherms = [(isotherm.replace('_', ' ').title(), isotherm, 'selected' if isotherm == data.get('ADSORPTION_TYPE', None) else '') for isotherm in isotherms]
    data['json'] = get_json_string(data)
    data['isotherms'] = isotherms
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/single_start.html', data)

@login_required
def component_and_step_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    steps = int(data.get('NSEC', ''))

    start = 1
    isotherm = data['ADSORPTION_TYPE']
    comps = []

    if isotherm in ('EXTERNAL_STERIC_MASS_ACTION', 'STERIC_MASS_ACTION', 'SELF_ASSOCIATION'):
        start = 2
        comps = [(1, 'Salt', 'readonly')]


    comps = comps + [(i, data.get('component%s' % i, ''), '') for i in range(start, int(data.get('numberOfComponents', 0))+1+len(comps))]
    steps = [(i, data.get('step%s' % i, ''), '') for i in range(1, int(data.get('NSEC', ''))+1)]

    data['numberOfComponents'] = len(comps)
    data['json'] = get_json_string(data)
    data['comps'] = comps
    data['steps'] = steps
    data['back'] = reverse('simulation:single_start', None, None)
    data['back_text'] = 'The Beginning'
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/component_and_step_setup.html', data)

def draw_isotherm(data, isotherm):
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    html = ['<div class="row"><div class="col-md-12"><table class="table"><thead><tr><th>#</th>']
    for name in list_of_names:
        html.append('<th>%s</th>' % name)

    html.append('</tr></thead><tbody>')
    for (attribute, per_component) in utils.isotherm_settings[isotherm]:
        if per_component:
            human_name, tooltip, units = utils.name_lookup_python[attribute]
            html.append('<tr><td data-toggle="tooltip" data-placement="bottom" title="%s">%s</td>' % (tooltip, human_name))
            for name in list_of_names:
                value = data.get('%s:%s' % (name, attribute), '0')
                html.append('<td><input type="text" class="required" value="%s" name="%s:%s"></td>' % (value, name, attribute))
            html.append('</tr>')
    html.append('</tbody></table></div></div>')

    for (attribute, per_component) in utils.isotherm_settings[isotherm]:
        if not per_component:
            human_name, tooltip, units = utils.name_lookup_python[attribute]
            html.append('''<div class="row"><div class="col-md-12">
                <div class="form-group">
                  <div class="col-sm-2">
                    <label for="%s" class="control-label" data-toggle="tooltip" data-placement="bottom" title="%s">%s</label>
                  </div>
                  <div class="col-sm-10">
                    <input type="text" class="form-control required" id="%s" name="%s" aria-required="true" value="%s">
                  </div>
                </div>
                </div>
                </div>''' % (attribute, tooltip, human_name, attribute, attribute, data.get(attribute, '0')))

    checked_yes = 'checked' if data.get('IS_KINETIC', '') == '1' else ''
    checked_no = '' if data.get('IS_KINETIC', '') == '1' else 'checked'
    html.append('''<div class="row"><div class="col-md-12">
                <div class="form-group">
              <div class="col-sm-offset-2 col-sm-10">
              <div class="radio">
                <input type="radio" name="IS_KINETIC" id="radio1" value="1" %s><label for="radio1">Use Kinetic Binding Model</label>
                <input type="radio" name="IS_KINETIC" id="radio2" value="0" %s><label for="radio2">Use Isotherm Binding Model</label>
                </div>
              </div>
            </div>
            </div></div>''' % (checked_yes, checked_no))

    html = '\n'.join(html)
    return html

def get_suffix_data(suffix, components, data):
    "return all the data that shares a common suffix with the component name"
    return [data['%s:%s' % (component, suffix)] for component in components]

def process_isotherm(data, isotherm_name):
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    processed_dict = {}
    processed_dict['ISOTHERM'] = isotherm_name

    for (attribute, per_component) in utils.isotherm_settings[isotherm_name]:
        if per_component:
            processed_dict[attribute] = get_suffix_data(attribute, list_of_names, data)

    for (attribute, per_component) in utils.isotherm_settings[isotherm_name]:
        if not per_component:
            processed_dict[attribute] = data[attribute]

    processed_dict['IS_KINETIC'] = data['IS_KINETIC']
    return processed_dict

@login_required
def isotherm_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    
    isotherm_name = data.get('ADSORPTION_TYPE')

    data['json'] = get_json_string(data)
    #data['isotherm'] =  utils.call_plugin_by_name(isotherm_name, 'isotherm', 'run', list_of_names, data)
    data['isotherm'] = draw_isotherm(data, isotherm_name)
    data['back'] = reverse('simulation:column_setup', None, None)
    data['back_text'] = 'Column Setup'
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/isotherm_setup.html', data)

@login_required
def column_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    


    data['json'] = get_json_string(data)
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    data['column_table'] = generate_column_table(list_of_names, data)
    data['back'] = reverse('simulation:component_and_step_setup', None, None)
    data['back_text'] = 'Component and Step Setup'
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/column_setup.html', data)

@login_required
def loading_setup(request):

    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    
    
    isotherm_name = data.get('ADSORPTION_TYPE')
    
    data['CADET_ISOTHERM'] = process_isotherm(data, isotherm_name)
    
    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    #This will remove all whitespace
    list_of_step_ids = [''.join(step.split()) for step in list_of_steps]

    data['json'] = get_json_string(data)
    values = [generate_step_settings(step, list_of_names, data) for step in list_of_steps]
    data['steps'] = zip(list_of_step_ids, list_of_steps, values)

    #This flattens out the array and django needs that to render properly
    continuous = [(idx, first, second) for idx, (first, second) in enumerate(zip(list_of_steps[:-1], list_of_steps[1:]))]
    continuous = [(idx, first, second, 'checked' if data.get('continuous_%s' % idx, '') == '1' else '', '' if data.get('continuous_%s' % idx, '') == '1' else 'checked') for (idx, first, second) in continuous]

    data['continuous'] = continuous
    step_times = ['Start:' + step for step in list_of_steps] + ['End:' + list_of_steps[-1]]
    data['step_times'] = [(name.replace(':', ' '), name, data.get(name, '0')) for name in step_times]
    data['back'] = reverse('simulation:isotherm_setup', None, None)
    data['back_text'] = 'Isotherm Setup'
    data.update(utils.name_lookup_template)
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
    data['radios'] = fix_radio([ ('PRINT_CONFIG','0'),
                        ('PRINT_PARAMLIST','0'),
                        ('PRINT_PROGRESS','0'),
                        ('PRINT_STATISTICS','1'),
                        ('PRINT_TIMING','1'),
                        ('USE_ANALYTIC_JACOBIAN','1'),
                        ('WRITE_AT_USER_TIMES','0'),
                        ('WRITE_SENS_ALL','0'),
                        ('WRITE_SENS_COLUMN_OUTLET','1'),
                        ('WRITE_SOLUTION_ALL','0'),
                        ('WRITE_SOLUTION_COLUMN_INLET','1'),
                        ('WRITE_SOLUTION_COLUMN_OUTLET','1'),
                        ('WRITE_SOLUTION_TIMES','1')], data)
    data['back'] = reverse('simulation:loading_setup', None, None)
    data['back_text'] = 'Loading Setup'
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/simulation_setup.html', data)

@login_required
def graph_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    

    if data['job_type'] == 'batch':
        cadet_runner.generate_ranges(data)

        length = reduce(operator.mul, [len(b) for c,b in data['batch_distribution']], 1)
        if length > settings.batch_limit:
            query = {}
            query['batch_limit'] = length
            query = urllib.urlencode(query)
            base = reverse('simulation:modify_attributes', None, None)
            return HttpResponseTemporaryRedirect('%s?%s' % (base, query))

    data['json'] = get_json_string(data)
    data['graph_single'] = [(name, 'checked' if data.get('graph_single:%s' % name, '')  == '1' else '', '' if data.get('graph_single:%s' % name, '')  == '1' else 'checked') for name in sorted(utils.get_plugin_names('graphing/single'))]
    data['graph_group'] = [(name, 'checked' if data.get('graph_group:%s' % name, '') == '1' else '', '' if data.get('graph_group:%s' % name, '') == '1' else 'checked') for name in sorted(utils.get_plugin_names('graphing/group'))]
    data['job_type'] = data['job_type']

    if data['job_type'] == 'batch':
        data['back'] = reverse('simulation:modify_attributes', None, None)
        data['back_text'] = 'Modify Attributes'
    else:
        data['back'] = reverse('simulation:simulation_setup', None, None)
        data['back_text'] = 'Simulation Setup'
    data.update(utils.name_lookup_template)
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
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/performance_parameters.html', data)

@login_required
def sensitivity_setup(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))
    

    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    sensitivities = []
    isotherm_name = data.get('ADSORPTION_TYPE').upper().replace(' ', '_')

    for name, units, type, per_component, per_section, sensitive, description, human_name in utils.parameters:
        if sensitive:
            if name not in utils.isotherm_name_set or name in utils.isotherm_name_set and name in utils.isotherm_set[isotherm_name]:
                sensitivities.append( (name, per_component, per_section, description), )

    ABS_TOL = float(data['ABSTOL'])

    entry = []
    for sensitivity in sensitivities:
        name, per_component, per_section, description = sensitivity
        if per_component == 1 and per_section == 1:
            seq = itertools.product(list_of_names, list_of_steps)
        elif per_component == 0 and per_section == 1:
            seq = itertools.product(itertools.repeat('', 1), list_of_steps)
        elif per_component == 1 and per_section == 0:
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
            human_name, tool_tip, units = utils.name_lookup_python[name]
            entry.append( (
                'choice:%s' % (form_name),
                'checked' if data.get('choice:%s' % (form_name), '') == '1' else '',
                human_name,
                tool_tip,
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
    #data['back'] = reverse('simulation:performance_parameters', None, None)
    #data['back_text'] = 'Performance Parameters Setup'
    data['back'] = reverse('simulation:graph_setup', None, None)
    data['back_text'] = 'Graph Setup'
    data.update(utils.name_lookup_template)
    return render(request, 'simulation/sensitivity_setup.html', data)

@login_required
def job_setup(request):
    post = request.POST

    data = get_json(post)
    table_data = get_json_table_dict(post)

    keep = set()
    sensitivities = []

    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
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

    data['CADET_ISOTHERM'] = process_isotherm(data, data.get('ADSORPTION_TYPE'))

    context = {'json':get_json_string(data),
               'back':reverse('simulation:sensitivity_setup', None, None),
            'back_text':'Sensitivity Setup'}
    return render(request, 'simulation/job_setup.html', context)

@login_required
def confirm_job(request):
    post = request.POST

    data = get_json(post)
    table_data = get_json_table_dict(post)

    keep = set()
    sensitivities = []

    list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
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

    data['CADET_ISOTHERM'] = process_isotherm(data, data.get('ADSORPTION_TYPE'))

    data['json'] = get_json_string(data)
    data['back'] = reverse('simulation:sensitivity_setup', None, None)
    data['back_text'] = 'Sensitivity Setup'
    data['steps'] = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]
    data['comps'] = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    return render(request, 'simulation/confirm_job.html', data)

@login_required
def choose_search_query(request):
    data = {}
    #data['queries'] = utils.get_plugin_names('search')
    data['queries'] = utils.call_plugins_by_name('search', 'get_form', request)
    return render(request, 'simulation/choose_search_query.html', data)

@login_required
def query_options(request):
    data = {}
    query = request.POST['search_query']
    data['query'] = query
    data['query_form'] = utils.call_plugin_by_name(query, 'search', 'run', request)
    return render(request, 'simulation/query_options.html', data)

@login_required
def query_results(request, name=None):

    post = request.POST
    data = get_json(post)
    data['user_name'] = request.user.username
    name = name if name is not None else data['search_query']
    headers, results = utils.call_plugin_by_id(name, 'process_search', request, data)
    search_results = []

    job_ids = [result[0] for result in results]
    JOBS = models.Job.objects.filter(id__in = job_ids)

    parameter = models.Parameters.objects.get(name='ADSORPTION_TYPE')


    for job, result in zip(JOBS, results):
        # (Job ID, Study Name, Model Name, Isotherm, [list of additional headers], rating
        #will have a search function here later that gathers up all the info we need from a jobid
        jobid = job.id
        study_name = job.study_name
        model_name = job.Model_ID.model
        isotherm = models.Job_String.objects.get(Job_ID=job, Parameter_ID=parameter).Data
        additional = result[1:]

        try:
            rating = models.Job_Notes.objects.get(Job_ID=job).rating
        except ObjectDoesNotExist:
            rating = 0

        url = reverse('simulation:run_job_get', None, None) + "?path=%s" % job.uid
        search_results.append([jobid, study_name, model_name, isotherm, additional, rating, url])
    if results:
        headers = results[0][1:]
    else:
        headers = []
    context = {'json':get_json_string(data),
              'search_results':search_results,
              'headers':headers}
    return render(request, 'simulation/query_results.html', context)

@login_required
def find_simulations(request):
    return query_results(request, "plugins.search.find_by_user")

@login_required
def generate_other_graphs(request):
    context = {}
    return render(request, 'simulation/generate_other_graphs.html', context)

def about_us(request):
    context = {}
    return render(request, 'simulation/about_us.html', context)

@login_required
def run_job_get(request):
    path = request.GET['path']
    sim_id = request.GET.get('sim_id', '')

    if sim_id:
        simulation = models.Simulation.objects.get(id=int(sim_id))
        rel_path = simulation.Rel_Path
    else:
        simulation = None
        rel_path = ''

    job_id = models.Job.objects.get(uid=path).id

    if sim_id and job_id:
        prefix = 'job_%s_sim_%s' % (job_id, sim_id)
    else:
        prefix = 'job_%s' % job_id

    print(path, rel_path)
    json_path, hdf5_path, graphs, json_data, alive, complete, stdout, stderr = utils.get_graph_data(path, settings.chunk_size, rel_path)

    query = request.GET.dict()
    query = urllib.urlencode(query)
    base = reverse('simulation:single_start', None, None)
    url_new = '%s?%s' % (base, query)

    data = {}
    data['graphs'] = graphs

    hdf5_path = '/static/simulation/sims/' + hdf5_path.replace(utils.storage_path, '')
    json_cache = hdf5_path.replace('sim.h5', 'json_cache')
    progress_path = os.path.join(os.path.dirname(hdf5_path), 'progress')

    try:
        job = models.Job.objects.get(uid=path)
        notes = models.Job_Notes.objects.get(Job_ID=job)
        rating = notes.rating
        notes = notes.notes
    except ObjectDoesNotExist:
        #create job type if it dies not exist
        rating = 0
        notes = ''

    data['read_only'] = '' if request.user.username == models.Job.objects.get(uid = path).username else 'readonly'

    data['prefix'] = prefix
    data['advanced_ui'] = json_data['advanced_ui']
    data['download_url'] = hdf5_path
    data['new_simulation'] = url_new
    data['batch_simulation'] = reverse('simulation:choose_attributes_to_modify', None, None) + "?path=%s" % path
    #data['new_simulation_batch'] = url_new_batch
    data['path'] = path
    data['chunk_size'] = settings.chunk_size
    data['rating'] = '%.1f' % rating
    data['notes'] = notes
    data['json_url'] = json_cache
    data['progress'] = progress_path
    data['job_id'] = job_id
    data['dropdown'] = generate_batch_choice(json_data, simulation, request, path)
    data['sim_id'] = sim_id

    if 'comparison' in request.session:
        data['comparison'] = format_comparison(request.session['comparison'].items())

    return render(request, 'simulation/run_job.html', data)

def format_comparison(seq):
    "reformat the comparison information from the cookie"
    temp = []
    for comparison_id, name in seq:
        try:
            job_id, sim_id = comparison_id.split('_')
        except ValueError:
            job_id = comparison_id
            sim_id = ''
        temp.append( (comparison_id, name, job_id, sim_id) )
    return temp
    
@login_required
def draw_comparison(request):
    selected = request.GET.getlist('selected')

    temp = []
    all_graphs = []

    for item in selected:
        id = item
        tag = request.GET[item]
        if '_' in item:
            job_id, sim_id = item.split('_')
            path = models.Job.objects.get(pk=int(job_id)).uid
            rel_path = models.Simulation.objects.get(id=int(sim_id)).Rel_Path
            
        else:
            job_id = item
            path = models.Job.objects.get(pk=int(job_id)).uid
            rel_path = ''

        json_path, hdf5_path, graphs, json_data, alive, complete, stdout, stderr = utils.get_graph_data(path, settings.chunk_size, rel_path)
        graphs_available = set([(name, human_name) for name, human_name, png, csv, csv_excel, filename_csv, filename_xls in graphs])
        all_graphs.append(graphs_available)
        hdf5_path = '/static/simulation/sims/' + hdf5_path.replace(utils.storage_path, '')
        temp.append(  (id, tag, hdf5_path, graphs_available) )

    data = {}
    data['selected'] = temp

    data['session_lookup'] = [(i, request.GET[i]) for i in selected]

    data['selected_jobs'] = ','.join(selected)
    data['json_url'] = reverse('simulation:get_data_comparison', None, None)
    data['graphs_common'] = set.intersection(*all_graphs)
    return render(request, 'simulation/draw_comparison.html', data)

def generate_batch_choice(json_data, simulation, request, path):
    temp = []
    if json_data['job_type'] == 'batch':
        temp.append('<table><tr>')
        for key,values in json_data['batch_distribution']:
            temp.append('<th>')
            temp.append(key)
            temp.append('</th>')
        temp.append('<th></th>')
        temp.append('</tr><tr>')

        for key,values in json_data['batch_distribution']:
            temp.append('<td>')
            temp.append(json_data[key])
            temp.append('</td>')
        temp.append('<td></td>')
        url = url = reverse('simulation:run_job_get', None, None) + "?path=%s" % path
        temp.append('<td><a href="%s" class="btn btn-default">Load Base Case</a></td>' % url)

        temp.append('</tr><tr>')
        for key,values in json_data['batch_distribution']:
            temp.append('<td>')
            temp.append(draw_selection(key, values, simulation, request))
            temp.append('</td>')
        temp.append('<td></td>')
        temp.append('<td><input type="submit" value="Load Simulation" class="btn btn-default"></td>')
        temp.append('</tr></table>')
    return ''.join(temp)

def draw_selection(key, values, simulation, request):
    temp = []
    try:
        checked = float(request.GET[u'batch:' + key.decode()])
    except KeyError:
        checked =None
    temp.append('<select class="form-control" name="batch:%s">' % key)
    for value in values:
        if value == checked:
            temp.append('<option value="%s" %s>%.3g</option>' % (repr(value), 'selected', value))
        else:
            temp.append('<option value="%s" %s>%.3g</option>' % (repr(value), "", value))
    temp.append('</select>')
    return ''.join(temp)

@login_required
def batch_choose(request):
    check_sum = request.POST.get('check_sum')

    job = models.Job.objects.get(uid=check_sum)

    search = {}
    for key, value in request.POST.items():
        if key.startswith('batch:'):
            search[key.replace('batch:', '')] = float(value)

    settings = serialization_settings()


    data = {}

    for key,value in search.items():
        key = key.encode('ascii').split(':')
        if len(key) == 1:
            name = key[0]
            comp = 'Column'
            step = 'Setup'
        elif len(key) == 2:
            comp, name = key
            step = 'Setup'
        elif len(key) == 3:
            step, comp, name = key
        data[name] = (step, comp, name, value)

    #temp = models.Simulation.objects
    #FIXME: For now to do the join in python until I can figure out how to get the db to do it.
    temp = []
    for name, type, per_component, per_section  in settings:
        if name in data:
            step, comp, name, value = data[name]

            step = models.Steps.objects.get(Job_ID=job,  Step=step)
            comp = models.Components.objects.get(Job_ID=job, Component=comp)
            name = models.Parameters.objects.get(name=name)

            if type in ('int', 'boolean'):
                value = int(value)
                temp.append(set([i.Simulation_ID for i in  models.Sim_Int.objects.filter(Data=value, Step_ID=step, Parameter_ID=name, Component_ID=comp)]))

            elif type == 'double':
                temp.append(set([i.Simulation_ID for i in  models.Sim_Double.objects.filter(Data=value, Step_ID=step, Parameter_ID=name, Component_ID=comp)]))
    temp = set.intersection(*temp)

    simulation = temp.pop()
    query = {}
    query['path'] = check_sum
    query['sim_id'] = simulation.id

    for key, value in request.POST.items():
        if key.startswith('batch:'):
            query[key] = value

    query = urllib.urlencode(query)
    base = reverse('simulation:run_job_get', None, None)
    return redirect('%s?%s' % (base, query))


@login_required
def process_comparison(request):
    if 'comparison' not in request.session:
        request.session['comparison'] = {}

    type = request.POST.get('type')

    if type == 'add':
        comparison_name = request.POST.get('comparison_name')
        simulation_id = request.POST.get('simulation_id')
    
        if simulation_id not in request.session['comparison'] and comparison_name:
            request.session['comparison'][simulation_id] = comparison_name
            request.session.modified = True
        return redirect(request.META.get('HTTP_REFERER'))
    elif type == 'delete':
        selected = request.POST.getlist('selected')
        for item in selected:
            del request.session['comparison'][item]
        request.session.modified = True
        return redirect(request.META.get('HTTP_REFERER'))
    elif type == 'graph':
        query = [('selected', item) for item in request.POST.getlist('selected')]
        query = query + [(item, request.session['comparison'][item]) for key,item in query]
        query = urllib.urlencode(query)
        base = reverse('simulation:draw_comparison', None, None)
        return redirect('%s?%s' % (base, query))

    

@login_required
def simulation_rate(request):
    path = request.POST['path']
    rating = float(request.POST['rating'])
    notes = request.POST['notes']

    try:
        job = models.Job.objects.get(uid=path)

        if request.user.username == job.username:
            notes, created = models.Job_Notes.objects.update_or_create(Job_ID=job, defaults={'rating':rating, 'notes':notes})

    except ObjectDoesNotExist:
        #create job type if it dies not exist
        pass

    query = {}
    query['path'] = path
    query['chunk_size'] = settings.chunk_size
    query = urllib.urlencode(query)
    base = reverse('simulation:run_job_get', None, None)
    return redirect('%s?%s' % (base, query))

@login_required
def run_job(request):
    post = request.POST
    data = get_json(post)

    json_data = get_json_string(data)
    check_sum = hashlib.sha256(json_data).hexdigest()

    relative_parts = [storage_path,] + [''.join(i for i in seq if i is not None) for seq in utils.grouper(check_sum, settings.chunk_size)]
    relative_path = os.path.join(*relative_parts)

    try:
        os.makedirs(relative_path)
    except OSError:
        print('Simulation directory already exists')

    path = os.path.join(relative_path, 'setup.json')

    json.dump(data, open(path, 'w'))
    out = open(os.path.join(relative_path, 'stdout'), 'w')
    err = open(os.path.join(relative_path, 'stderr'), 'w')
    simulation_path = cadet_runner.create_simulation_file(relative_path, data)

    try:
        open(os.path.join(relative_path, 'pid'), 'r')
        run_job = 0
    except IOError:
        run_job = 1

    if run_job:
        write_job_to_db(data, json_data, check_sum, request.user.username)

        data = {}
        data['complete'] = 0
        data['ok'] = 0

        json_cache = os.path.join(relative_path, 'json_cache')
        open(json_cache, 'wb').write(json.dumps(data))


        models.Job_Status.objects.update_or_create(Job_ID__uid=path, defaults={'seen': 0, 'successful':0, 'running':1, 'start':datetime.now(), 'end':None})

        popen = subprocess.Popen(['python', cadet_runner_path, '--json', path, '--sim', simulation_path,], stdout=out, stderr=err)

        with open(os.path.join(relative_path,'pid'), 'w') as pid:
            pid.write(str(popen.pid))

    query = {}
    query['path'] = check_sum
    query = urllib.urlencode(query)
    base = reverse('simulation:run_job_get', None, None)
    return redirect('%s?%s' % (base, query))

def remove_without_error(path):
    try:
        os.remove(path)
    except OSError:
        pass

@login_required
def force_rerun(request):
    "force rerun the simulation"
    check_sum = request.POST['path']

    relative_parts = [storage_path,] + [''.join(i for i in seq if i is not None) for seq in utils.grouper(check_sum, settings.chunk_size)]
    relative_path = os.path.join(*relative_parts)

    reset_sim = ['progress', 'status', 'stderr', 'json_cache', 'pid', 'sim.h5']
    reset_sim = [os.path.join(relative_path, i) for i in reset_sim]

    map(remove_without_error, reset_sim)

    reset_sim_wildcards = ['*.csv', '*.xlsx', '.png']
    reset_sim_wildcards = [os.path.join(relative_path, i) for i in reset_sim_wildcards]

    for path in reset_sim_wildcards:
        map(remove_without_error, glob.glob(path))
        
    #remove all the batch stuff    
    shutil.rmtree(os.path.join(relative_path, 'batch'), True)


    path = os.path.join(relative_path, 'setup.json')
    
    json_data = open(path, 'rb').read()
    json_data = json.loads(json_data)
    json_data = utils.encode_to_ascii(json_data)

    simulation_path = cadet_runner.create_simulation_file(relative_path, json_data)
    
    out = open(os.path.join(relative_path, 'stdout'), 'w')
    err = open(os.path.join(relative_path, 'stderr'), 'w')

    data = {}
    data['complete'] = 0
    data['ok'] = 0

    json_cache = os.path.join(relative_path, 'json_cache')
    print(json_cache)
    open(json_cache, 'wb').write(json.dumps(data))

    models.Job_Status.objects.update_or_create(Job_ID__uid=path, defaults={'seen': 0, 'successful':0, 'running':1, 'start':datetime.now(), 'end':None})

    popen = subprocess.Popen(['python', cadet_runner_path, '--json', path, '--sim', simulation_path,], stdout=out, stderr=err)

    with open(os.path.join(relative_path,'pid'), 'w') as pid:
        pid.write(str(popen.pid))

    query = {}
    query['path'] = check_sum
    query = urllib.urlencode(query)
    base = reverse('simulation:run_job_get', None, None)
    return redirect('%s?%s' % (base, query))

def write_job_to_db(data, json_data, check_sum, username):
    #first check if we already have this entry

    try:
        job = models.Job.objects.get(uid=check_sum)
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


        list_of_names = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
        list_of_steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

        #create job
        job = models.Job.objects.create(Product_ID = product,
            Job_Type_ID = job_type,
            Model_ID = model,
            study_name = data['study_name'],
            json = json_data,
            uid = check_sum,
            username = username)

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

        settings = serialization_settings()

        write_job_values(job, data, comps, steps, settings)

        insert_simulations(job, data, comps, steps, settings)

def write_job_values(job, data, comps, steps, settings):
    for name, type, per_component, per_section  in settings:

        if type in ('int', 'string', 'double', 'boolean'):
            if per_component and per_section:
                db_add_comp_and_section(name, type, data, steps, comps, job)
            elif per_component and not per_section:
                db_add_comp(name, type, data, steps[0], comps, job)
            elif per_section and not per_component:
                pass #we don't have any of these but leave this here in case it happens later
            else:
                db_add_var(name, name, type, data, steps[0], comps[0], job)

def serialization_settings():
    temp = []
    for name, units, type, per_component, per_section, sensitive, description, human_name in utils.parameters:
        temp.append( (name, type, per_component, per_section), )
    return temp

def insert_simulations(job, data, comps, steps, settings):
    if data['job_type'] == 'batch':
        keys, combos = cadet_runner.generate_permutations(data)
        diffs = [dict(zip(keys, combo)) for combo in combos]

        for idx,diff in enumerate(diffs):
            sim = models.Simulation.objects.create(Job_ID = job, Rel_Path = str(idx))
            write_job_values(sim, diff, comps, steps, settings)

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

        class_name = job.__class__.__name__

        if class_name == 'Simulation':
            class_name = 'Sim'

        if class_name == 'Job':
            model_args['Job_ID'] = job
        else:
            model_args['Simulation_ID'] = job

        if type in ('int', 'boolean'):
            model_args['Data'] = int(data[lookup])
            getattr(models, '%s_Int' % class_name).objects.create(**model_args)

        elif type == 'string':
            model_args['Data'] = data[lookup]
            getattr(models, '%s_String' % class_name).objects.create(**model_args)

        elif type == 'double':
            model_args['Data'] = float(data[lookup])
            getattr(models, '%s_Double' % class_name).objects.create(**model_args)

    except KeyError:
        #print 'Missing', lookup, lookup in data
        pass

def sync_db():
    for name,isotherm in utils.isotherms:
        try:
            models.Isotherms.objects.get(Name = name, Isotherm=isotherm)
        except ObjectDoesNotExist:
            models.Isotherms.objects.create(Name = name, Isotherm=isotherm)

    for name, units, type, per_component, per_section, sensitive, description, human_name in utils.parameters:
        try:
            models.Parameters.objects.get(name=name, units=units, description=description)
        except ObjectDoesNotExist:
            models.Parameters.objects.create(name=name, units=units, description=description)

def get_graph_data(path, rel_path, job_id, sim_id):
    json_path, hdf5_path, graphs, data, alive, complete, stdout, stderr = utils.get_graph_data(path, settings.chunk_size, rel_path)
    parent, hdf5_name = os.path.split(hdf5_path)
    json_cache = os.path.join(parent, 'json_cache')

    if job_id and sim_id:
        prefix = 'Job %s Sim: %s' % (job_id, sim_id)
    else:
        prefix = 'Job %s ' % job_id

    json_data = open(json_cache, 'rb').read()
    json_data = json.loads(json_data)
    json_data = utils.encode_to_ascii(json_data)
    return json_data

@login_required
@gzip.gzip_page
def get_data_comparison(request):
    """This function has to call an external process because of scipy. DO NOT MERGE that code into here. It causes apache
    to deadlock and go into some kind of memory allocation loop. I tried many different options but none worked. Instead
    will pass the needed json to an external process and then read the result back."""
    selected = request.GET.get('selected').split(',')

    temp = []
    job_ids = []
    filename_parts = []
    for i in selected:
        tag = request.GET[i]
        try:
            (job_id, sim_id) = map(int, i.split('_'))
            filename_parts.append('%s_%s' % (job_id, sim_id))
        except ValueError:
            (job_id, sim_id) = (int(i), None)
            filename_parts.append(str(job_id))
        temp.append( (job_id, sim_id, tag) )
        job_ids.append(job_id)
    
    temp.sort()

    JOBS = models.Job.objects.filter(id__in = job_ids)

    job_lookup = {}
    for job in JOBS:
        job_lookup[job.id] = job.uid

    all_graphs = []
    all_data = {}
    for job_id, sim_id, tag in temp:
        if sim_id:
            rel_path = models.Simulation.objects.get(id=int(sim_id)).Rel_Path
        else:
            rel_path = ''
        path = job_lookup[job_id]
        
        json_data = get_graph_data(path, rel_path, job_id, sim_id)
        all_data[tag] = json_data
        all_graphs.append(set(json_data['data'].keys()))

    common_graphs = set.intersection(*all_graphs)

    #Filter data
    all_components = {}
    for key, value in all_data.items():
        local_graphs = set(value['data'].keys())
        to_remove = local_graphs - common_graphs
        for i in to_remove:
            del value['data'][i]
        for i in common_graphs:
            if i not in all_components:
                all_components[i] = []
            all_components[i].append([data['label'] for data in value['data'][i]])

    #find all components
    for key, values in all_components.items():
        unique_components = list(OrderedDict.fromkeys(itertools.chain.from_iterable(values)))
        comps = {}
        for idx, val in enumerate(unique_components):
            comps[idx] = {'label':val}

        all_components[key] = comps

    #rearrange by graph type instead of by comparison for simpler graphing
    comparison_data = {}
    for tag, job_data in all_data.items():
        for graph_name, graph_data in job_data['data'].items():
            if graph_name not in comparison_data:
                comparison_data[graph_name] = {}
                comparison_data[graph_name]['data'] = {}

            for value in graph_data:
                value['comp_type'] = value['label']
                value['label'] = '%s %s' % (tag, value['label'])

            comparison_data[graph_name]['data'][tag] = graph_data
            comparison_data[graph_name]['components'] = all_components[graph_name]





    path = JOBS[0].uid
    filename = '__'.join(sorted(filename_parts)) + '.json'

    json_data = {}
    json_data['comparison_data'] = comparison_data

    return JsonResponse(json_data, safe=False)

@login_required
@gzip.gzip_page
def inlet_graph(request):
    post = request.POST
    data = get_json(post)

    section_times = cadet_runner.get_section_times(data)
    components = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
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
    for name, value in seq:

        human_name, tool_tip, units = utils.name_lookup_python[name]

        value = data.get(name, value)
        if value == '1':
            yes = 'checked="checked"'
            no = ''
        else:
            yes = ''
            no = 'checked="checked"'
        temp.append( (human_name, tool_tip, name, yes, no))
    return temp

@login_required
def choose_attributes_to_modify(request):

    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    if 'path' in request.GET:
        relative_parts = [''.join(i for i in seq if i is not None) for seq in utils.grouper(request.GET.get('path'), settings.chunk_size)]
        relative_path = os.path.join(*relative_parts)

        json_data = open(os.path.join(storage_path, relative_path, 'setup.json'), 'rb').read()

        json_data = json.loads(json_data)
        json_data = utils.encode_to_ascii(json_data)
        data.update(json_data)

    comps = [data.get('component%s' % i) for i in range(1, int(data.get('numberOfComponents', ''))+1)]
    steps = [data.get('step%s' % i) for i in range(1, int(data.get('NSEC', ''))+1)]

    modify = []
    #every attribute can be modified except for strings, blobs, number of steps and number of components, sensitivities and checkbox settings
    for name, units, type, per_component, per_section, sensitive, description, human_name in utils.parameters:

        if name not in ('NCOMP', 'NSEC') and type in ('int', 'double'):
            if per_component and per_section:
                for step in steps:
                    for comp in comps:
                        key = '%s:%s:%s' % (step, comp, name)
                        if key in data:
                            checked_1, checked_2, checked_3 = get_checked(key, data)
                            human_name, tool_tip, units = utils.name_lookup_python[name]
                            modify.append( (human_name, tool_tip, comp, step, description, key, checked_1, checked_2, checked_3) )
            elif per_component and not per_section:
                for comp in comps:
                    key = '%s:%s' % (comp, name)
                    if key in data:
                        checked_1, checked_2, checked_3 = get_checked(key, data)
                        human_name, tool_tip, units = utils.name_lookup_python[name]
                        modify.append( (human_name, tool_tip, comp, '', description, key, checked_1, checked_2, checked_3) )
            elif per_section and not per_component:
                pass #we don't have any of these but leave this here in case it happens later
            else:
                if name in data:
                    checked_1, checked_2, checked_3 = get_checked(name, data)
                    human_name, tool_tip, units = utils.name_lookup_python[name]
                    modify.append( (human_name, tool_tip, '', '', description, name, checked_1, checked_2, checked_3) )

    data['json'] = get_json_string(data)
    data['modifies'] = modify

    return render(request, 'simulation/choose_attributes_to_modify.html', data)

def get_checked(key, data):
    try:
        choice = data['choose_attributes:%s' % key]
        if choice == 'choose':
            return 'checked', '', ''
        elif choice == 'distribution':
            return '', 'checked', ''
        elif choice == 'no_change':
            return  '', '', 'checked'
    except KeyError:
        return '', '', 'checked'


@login_required
def create_batch_simulation(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    search_results = []

    #notes = models.Job_Notes.objects.all().order_by('-rating')[:5]

    #print notes

    #JOBS = models.Job.objects.filter(id = notes)
    JOBS = models.Job.objects.exclude(job_notes=None).order_by('-job_notes__rating')[:5]

    parameter = models.Parameters.objects.get(name='ADSORPTION_TYPE')


    for job in JOBS:
        # (Job ID, Study Name, Model Name, Isotherm, [list of additional headers], rating
        #will have a search function here later that gathers up all the info we need from a jobid
        jobid = job.id
        study_name = job.study_name
        model_name = job.Model_ID.model
        isotherm = models.Job_String.objects.get(Job_ID=job, Parameter_ID=parameter).Data
        rating = models.Job_Notes.objects.get(Job_ID=job).rating
        url = reverse('simulation:choose_attributes_to_modify', None, None) + "?path=%s" % job.uid
        search_results.append([jobid, study_name, model_name, isotherm, rating, url])
    context = {'json':get_json_string(data),
              'search_results':search_results}

    return render(request, 'simulation/create_batch_simulation.html', context)

@login_required
def modify_attributes(request):
    post = request.POST
    data = default_value.copy()
    data.update(get_json(post))

    context = {'json':get_json_string(data)}
    choose_attributes = [(key,value) for (key,value) in data.items() if 'choose_attributes:' in key]
    context['choices'] = [key.replace('choose_attributes:', '') for key, value in choose_attributes if value == 'choose']
    context['choices'] = format_choices(context['choices'], data)

    context['distributions'] = [key.replace('choose_attributes:', '') for key, value in choose_attributes if value == 'distribution']
    context['distributions'] = format_distributions(context['distributions'], data)

    context['back'] = reverse('simulation:choose_attributes_to_modify', None, None)
    context['back_text'] = 'Choose Attributes to Modify'

    context['allowed'] = ['Linear', 'Random Uniform', 'Truncated Random Normal']

    context['combinations'] =  settings.batch_limit
    context['message'] = ''
    if request.GET.get('batch_limit', '0') != '0':
        context['message'] = 'Too many combinations where chosen. Only %d are allowed and %s where chosen' % (settings.batch_limit, request.GET.get('batch_limit'))

    return render(request, 'simulation/modify_attributes.html', context)

def format_distributions(seq, data):
    "format distributions"
    temp = []
    
    for key in seq:
        choice = key
        value = data[key]
        lb = data.get("modify_dist_lb:%s" % key, '')
        ub = data.get("modify_dist_ub:%s" % key, '')
        dist_points = data.get("modify_dist_number:%s" % key, '')
        dist_stdev = data.get("modify_dist_stdev:%s" % key, '1')
        dist_type = data.get("modify_dist_type:%s" % key, '')
    
        parts = choice.split(':')
        if len(parts) == 1:
            name = parts[0]
            human_name, tool_tip, units = utils.name_lookup_python[name]
        elif len(parts) == 2:
            comp, name = parts
            human_name, tool_tip, units = utils.name_lookup_python[name]
            human_name = '%s %s' % (comp, human_name)
            tool_tip = '%s for component %s' % (tool_tip, comp)            
        elif len(parts) == 3:
            step, comp, name = parts
            human_name, tool_tip, units = utils.name_lookup_python[name]
            human_name = '%s %s %s' % (step, comp, human_name)
            tool_tip = '%s for component %s during step %s' % (tool_tip, comp, step)
            
        temp.append( (human_name, tool_tip, choice, value, lb, ub, dist_points, dist_stdev, dist_type) )
    
    return temp    
    
def format_choices(seq, data):
    "format the choices to include a tooltip"
    temp = []
    for key in seq:
        choice = key
        
        parts = choice.split(':')
        if len(parts) == 1:
            name = parts[0]
            human_name, tool_tip, units = utils.name_lookup_python[name]
        elif len(parts) == 2:
            comp, name = parts
            human_name, tool_tip, units = utils.name_lookup_python[name]
            human_name = '%s %s' % (comp, human_name)
            tool_tip = '%s for component %s' % (tool_tip, comp)            
        elif len(parts) == 3:
            step, comp, name = parts
            human_name, tool_tip, units = utils.name_lookup_python[name]
            human_name = '%s %s %s' % (step, comp, human_name)
            tool_tip = '%s for component %s during step %s' % (tool_tip, comp, step)
        value = data[key]
        text = data.get('modify_choice:%s' % key, '')
        temp.append(( human_name, tool_tip, choice, value, text) )
    return temp    
    