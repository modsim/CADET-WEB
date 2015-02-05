__author__ = 'kosh_000'

import compress_series
import cadet_runner
import h5py
import plot_sensitivity
import utils


def run():
    json_data = {}
    path = '2caf85b3667a73db8225046897e1612014715fc5c87783245ce9c833c3cc9da5'
    chunk_size =20

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
                print id,title
                data_sets = compress_series.compress_time_series(data_sets, 0.2)

                for data_set in data_sets:
                    time = list(data_set['data'][0])
                    values = list(data_set['data'][1])
                    data_set['data'] = zip(time, values)

                json_data['data'][id] = data_sets

            if key.startswith('graph_group') and value == '1':
                _, name = key.split(':')
                id, title, data_sets = utils.call_plugin_by_name(name, 'graphing/group', 'get_data', hdf5_path)
                print id,title
                data_sets = compress_series.compress_time_series(data_sets, 0.2)
                for data_set in data_sets:
                    time = list(data_set['data'][0])
                    values = list(data_set['data'][1])
                    data_set['data'] = zip(time, values)

                json_data['data'][id] = data_sets

        for sensitivity_number in range(len(data.get("sensitivities", []))):
            id, title, data_sets = plot_sensitivity.get_data(hdf5_path, sensitivity_number)
            print id,title
            data_sets = compress_series.compress_time_series(data_sets, 0.2)
            for data_set in data_sets:
                time = list(data_set['data'][0])
                values = list(data_set['data'][1])
                data_set['data'] = zip(time, values)

            json_data['data'][id] = data_sets


if __name__ == "__main__":
    run()