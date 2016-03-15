
import cPickle as pickle
import numpy as np

def ngram_ids_to_strings(ngram_pickle_filepath, ngram_ids):
    '''Reads in pickle file containing an ngram ID to string dict, a replaces
    the ids in the given list with their corresponding strings.'''
    print 'Reading in ngram dictionary', ngram_pickle_filepath
    with open(ngram_pickle_filepath, 'rb') as f:
        id_ngram_dict = pickle.load(f)
        print 'Loading ngram dictionary with', len(id_ngram_dict), 'keys'
        return [id_ngram_dict.get(id, 'NOT FOUND') for id in ngram_ids]


# note don't know how to map the label index to the actual label
# They're probably in sorted order, though.
def get_important_ngrams(ngrams, coefficients_per_label):
    most_important_ngrams_per_label = []
    for coef_vec in coefficients_per_label:
        top10 = np.argsort(coef_vec)[-10:] # TODO sort by absolute value?
        most_important_ngrams_per_label.append([ngrams[j] for j in top10])
    return most_important_ngrams_per_label
