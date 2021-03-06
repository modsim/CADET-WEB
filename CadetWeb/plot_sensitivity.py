from __future__ import division
#import matplotlib
#matplotlib.use('AGG')

import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
import numpy as np
import h5py
import os.path
import shutil



name = "Sensitivity"

depends_performance = []
depends_sensitivity = []
file_name = 'dynamic.png'

def get_picture_id(hdf5_path, sensitivity_number):
    "return the filename and html id of the picture"
    h5 = h5py.File(hdf5_path, 'r')

    component =  h5['/input/sensitivity/param_%03d/SENS_COMP' % sensitivity_number].value
    name = h5['/input/sensitivity/param_%03d/SENS_NAME' % sensitivity_number].value
    section = h5['/input/sensitivity/param_%03d/SENS_SECTION' % sensitivity_number].value


    components = [node.value for key,node in h5['/web/COMPONENTS'].items()]
    number_of_components = len(components)

    #number_of_components = h5['/input/model/NCOMP'].value

    #components = [h5['/web/COMPONENTS/COMP_%03d' % i].value for i in  range(number_of_components)]

    #number_of_sections = h5['/input/model/inlet/NSEC'].value
    #sections = [h5['/web/STEPS/STEP_%03d' % i].value for i in  range(number_of_sections)]

    sections = [node.value for key,node in h5['/web/STEPS/'].items()]

    file_name = '%s_%s_%s.png' % (name, section, component)
    file_name = file_name.replace('-', 'minus')

    file_name_csv = '%s_%s_%s.csv' % (name, section, component)
    file_name_csv = file_name_csv.replace('-', 'minus')

    file_name_xls = file_name_csv.replace('.csv', '.xlsx')

    if component == -1:
        component = "All"
    else:
        component = components[component]

    if section == -1:
        section = "All"
    else:
        section = sections[section]

    title = 'Sensitivity Name:%s  Component:%s  Section:%s' % (name.replace('_', ' ').title(), component, section)
    h5.close()

    return file_name, file_name_csv, file_name_xls, title

def run(hdf5_path, sensitivity_number):
    #generate a chromatogram
    parent, hdf5_name = os.path.split(hdf5_path)

    file_name, file_name_csv, file_name_xls, title = get_picture_id(hdf5_path, sensitivity_number)

    #generate_plot(file_name, title, hdf5_path, sensitivity_number, parent)
    generate_csv(file_name_csv, file_name_xls, hdf5_path, sensitivity_number, parent)

def generate_csv(file_name, file_name_xls, hdf5_path, sensivitity_number, parent):
    h5 = h5py.File(hdf5_path, 'r')
    
    data = pd.DataFrame()
    data['Time'] = h5['/output/solution/SOLUTION_TIMES']
    
    #number_of_components = h5['/input/model/NCOMP'].value
    #components = [h5['/web/COMPONENTS/COMP_%03d' % i].value for i in  range(number_of_components)]

    components = [node.value for key,node in h5['/web/COMPONENTS'].items()]

    number_of_components = len(components)

    columns = ['Time']

    for idx, comp in enumerate(components):
        columns.append(comp)
        #data[comp] = h5['/output/sensitivity/param_%03d/SENS_COLUMN_OUTLET_COMP_%03d' % (sensivitity_number, idx)]

        try:
            data[comp] = h5['/output/sensitivity/param_%03d/SENS_COLUMN_OUTLET_COMP_%03d' % (sensivitity_number, idx)]
        except KeyError:
            data[comp] = h5['/output/sensitivity/param_%03d/unit_001/SENS_COLUMN_OUTLET_COMP_%03d' % (sensivitity_number, idx)]

    data.to_csv(os.path.join(parent, file_name), columns=columns, index=False)
    data.to_excel(os.path.join(parent, file_name_xls), columns=columns, index=False)
    h5.close()


def generate_plot(file_name, title, hdf5_path, sensitivity_number, parent):
    figure = plt.figure(file_name)
    figure.clear()
    figure.suptitle(title)
    axis = figure.add_subplot(111)

    #need to set this up for multiple scales and color
    salt_axis = axis.twinx()

    axis.set_position([0.2,0.1,0.7,0.7])
    salt_axis.set_position([0.2,0.1,0.7,0.7])

    axis.set_xlabel('Time (s)')
    axis.set_ylabel('Concentration (mMol)')

    id, title, data = get_data(hdf5_path, sensitivity_number)
    for idx, data in enumerate(data):
        if idx == 0:
            plot = salt_axis.plot
            axis.plot([0], [0], label=data['label'])
        else:
            plot = axis.plot
        plot(*data['data'], label=data['label'])

    axis.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=2, mode="expand", borderaxespad=0.)

    src = os.path.join(parent, 'test.png')
    dst = os.path.join(parent, file_name)
    figure.savefig(src, dpi=300)
    shutil.move(src, dst)

def get_data(hdf5_path, sensitivity_number):
    #generate a chromatogram
    parent, hdf5_name = os.path.split(hdf5_path)
    data = []

    file_name, file_name_csv, file_name_xls, title = get_picture_id(hdf5_path, sensitivity_number)

    dst = os.path.join(parent, file_name_csv)
    if not os.path.exists(dst):
        generate_csv(file_name_csv, file_name_xls, hdf5_path, sensitivity_number, parent)

    h5 = h5py.File(hdf5_path, 'r')

    #number_of_components = h5['/input/model/NCOMP'].value
    #components = [h5['/web/COMPONENTS/COMP_%03d' % i].value for i in  range(number_of_components)]

    components = [node.value for key,node in h5['/web/COMPONENTS'].items()]

    number_of_components = len(components)

    solution_values = np.array(h5['/web/compress/param_%03d' % sensitivity_number])
    solution_times = solution_values[:,0]

    for idx, comp_name in enumerate(components):
        values = solution_values[:, idx+1]

        temp = {}
        temp['label'] = comp_name
        temp['data'] = (solution_times, values)
        temp['yaxis'] = 1 if comp_name.lower() != 'salt' else 2
        data.append(temp)

    h5.close()
    return title.replace(' ', '_').replace(':', '_'), title, data

#if this is called from the command line then call the run function with the first arguement handed to it as a path
if __name__ == "__main__":
    import sys
    run(sys.argv[1])
