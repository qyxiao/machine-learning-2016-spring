import cPickle as pickle
'''
use cPickle to load and save objects quickly
'''


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
        
def load_object(filename):
    
    with open(filename, 'rb') as input:
        out = pickle.load(input)

    return out