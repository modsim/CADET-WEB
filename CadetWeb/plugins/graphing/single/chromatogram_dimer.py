from __future__ import division
import matplotlib
matplotlib.use('AGG') 

import numpy as np
import matplotlib.pyplot as plt
import h5py
import os.path
import shutil


name = "Chromatogram 10x Dimer"

depends_performance = []
depends_sensitivity = []
file_name = 'chromatogram_10x.png'

def run(hdf5_path):
    #generate a chromatogram
    figure = plt.figure(name)
    figure.clear()
    figure.suptitle(name)
    axis = figure.add_subplot(111)

    #need to set this up for multiple scales and color
    salt_axis = axis.twinx()

    axis.set_position([0.1,0.1,0.8,0.7])
    salt_axis.set_position([0.1,0.1,0.8,0.7])

    parent, hdf5_name = os.path.split(hdf5_path)

    axis.set_xlabel('Time')
    axis.set_ylabel('Concentration')

    id, title, data = get_data(hdf5_path)
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

def get_data(hdf5_path):
    data = []
    parent, hdf5_name = os.path.split(hdf5_path)

    h5 = h5py.File(hdf5_path, 'r')

    number_of_components = h5['/input/model/NCOMP'].value

    components = [h5['/web/COMPONENTS/COMP_%03d' % i].value for i in  range(number_of_components)]

    solution_times = list(h5['/output/solution/SOLUTION_TIMES'])

    mul = 1
    for idx, comp_name in enumerate(components):
        values = list(h5['/output/solution/SOLUTION_COLUMN_OUTLET_COMP_%03d' % idx])
        temp = {}
        temp['label'] = comp_name
        if name.strip().lower() == 'dimer':
            mul = 10
        else:
            mul = 1

        temp['data'] = (solution_times, values*mul)
        temp['yaxis'] = 1 if comp_name.lower() != 'salt' else 2
        data.append(temp)
    h5.close()
    return name.replace(' ', '_').replace(':', '_'), name, data
    
#if this is called from the command line then call the run function with the first arguement handed to it as a path
if __name__ == "__main__":
    import sys
    run(sys.argv[1])
