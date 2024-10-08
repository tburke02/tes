import re
import h5py
import numpy as np 

def load_state_from_h5(h5_file, state):
    h5 = h5py.File(h5_file, 'r')
    n = 0
    for key in h5.keys():
        n += len(h5[key][state]['energy'])

    energies = np.zeros(n)
    unixnanos = np.zeros(n)
    seconds_after_last_external_trigger = np.zeros(n)

    i0 = 0
    for key in h5.keys():
        g = h5[key][state]
        n = len(g['energy'])
        energies[i0:i0+n] = g['energy']
        unixnanos[i0:i0+n] = g['unixnano']
        seconds_after_last_external_trigger[i0:i0+n] = g['seconds_after_last_external_trigger']
        i0+=n
    return np.vstack([energies,unixnanos,seconds_after_last_external_trigger])

def load_multi_h5s(files): # WIP
     for h5_file in files:
        h5 = h5py.File(h5_file, 'r')
        n = 0
        for key in h5.keys():
            states = [i for i in key if (bool(re.match(r'[A-Z][A-Z]?',i))) & (len(i)<3)]
            for state in states:
                n += len(h5[key][state]['energy'])

        energies = np.zeros(n)
        unixnanos = np.zeros(n)
        seconds_after_last_external_trigger = np.zeros(n)

        i0 = 0
        for key in h5.keys():
            for state in states:
                g = h5[key][state]
                n = len(g['energy'])
                energies[i0:i0+n] = g['energy']
                unixnanos[i0:i0+n] = g['unixnano']
                seconds_after_last_external_trigger[i0:i0+n] = g['seconds_after_last_external_trigger']
                i0+=n
        np.vstack([energies,unixnanos,seconds_after_last_external_trigger])

def parfor(func, arr):
    import concurrent.futures
    with concurrent.futures.ProcessPoolExecutor() as executor:
            out = list(executor.map(func, arr))
    return np.array(out)

def midpoints(x):
    return x[:-1]+(x[1]-x[0])/2

def pcm_edges(x):
    return np.concatenate((x,[x[1]-x[0]]))