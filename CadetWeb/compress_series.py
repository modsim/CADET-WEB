import numpy as np
from scipy.signal import argrelextrema

def compress_time_series(values, epsilon):
    """compress a time series that is in the flot format expect a sequence of times and then a dictionary of the form
    { label: "Foo", data: (solution_times, values) }"""

    #create a 2d array of values
    temp_values = np.transpose(np.vstack([value['data'][1] for value in values]))
    time = values[0]['data'][0]

    #filter any value below 0.1% of the smallest components peak max to zero
    filter_level = min(np.max(temp_values,0)) * .0001
    temp_values[(temp_values < filter_level)] = 0

    maximums = set()
    for i in range(0, temp_values.shape[1]):
        maximums.update(argrelextrema(temp_values[:,i], np.greater)[0].tolist())

    #always keep first point
    new_time = np.array([time[0]])
    new_values = np.array(temp_values[0,:])

    current = temp_values[0,:]

    for idx in xrange(1, len(time)):
        #always keep peak max
        if idx in maximums:
            current = temp_values[idx,:]
            new_time = np.vstack([new_time, time[idx]])
            new_values = np.vstack([new_values, temp_values[idx,:]])
        elif np.max(np.absolute(temp_values[idx,:]-current) > np.absolute(current * epsilon)):

            #this is for step change detection if we change by more than 5 times our epsilon store the
            #previous point also if we have not already stored it
            if np.max(np.absolute(temp_values[idx,:]-current) > np.absolute(current * 5 * epsilon)) and time[idx-1] != new_time[-1]:
                new_time = np.vstack([new_time, time[idx-1]])
                new_values = np.vstack([new_values, temp_values[idx-1,:]])

            current = temp_values[idx,:]
            new_time = np.vstack([new_time, time[idx]])
            new_values = np.vstack([new_values, temp_values[idx,:]])

    #always keep last point
    new_time = np.vstack([new_time, time[-1]])
    new_values = np.vstack([new_values, temp_values[-1,:]])

    #convert back to the time series format for flot
    for idx, value in enumerate(values):
        value['data'] = (new_time[:,0].tolist(), new_values[:,idx].tolist())


    return values

if __name__ == "__main__":
    import sys
    import json
    data = sys.stdin.read()
    #data = open('/tmp/data.json', 'r').read()
    data = json.loads(data.replace("'", '"'))

    for id, data_sets in data['data'].items():
        data['data'][id] = compress_time_series(data_sets, 0.01)

    output = json.dumps(data).replace('"', "'")
    #open('/tmp/data2.json', 'w').write(output)
    print output




