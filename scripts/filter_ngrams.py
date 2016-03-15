"""Code that filters out the ngram dictionary to only the ones we use"""


# HPC Files
VOCAB_DATA_DIR = '/scratch/akp258/ml_input_data/vocab_map_text'
NGRAM_ID_COUNTS_FILE = '/scratch/akp258/ml_input_data/total_ngram_counts.p.15466'
#TODO TESTING NGRAM_ID_COUNTS_FILE = '/scratch/akp258/ml_input_data/total_ngram_counts.p.125'
NUM_VOCAB_SHARDS = 508
COUNT_CUTOFF = 50
OUTPUT_FILE_PREFIX = '/scratch/akp258/ml_output_data/filtered_vocab_map.p'

# Alex local files
#VOCAB_DATA_DIR = '/Users/pinesol/mlcs_data/vocab_map_test'
#NGRAM_ID_COUNTS_FILE = '/Users/pinesol/mlcs_data/total_ngram_counts.p.125'
#NUM_VOCAB_SHARDS = 2
#COUNT_CUTOFF = 2 
#OUTPUT_FILE_PREFIX = '/tmp/vocab_map.p'


import cPickle as pickle

kPrefix = 'part-'

def read_ngram_file(ngram_filepath):
    id_ngram_map = {}
    with open(ngram_filepath, 'r') as f:
        for line in f:
            line = line.strip() # ('a',1)
            if len(line) < 8 or not (line[0] == "(" and line[-1] == ")"):
                print 'skipping invalid line:', line
                continue            
            ngram, id = line.split(", ")
            if ngram[:3] == "(u'" or ngram[:3] == '(u"':
                ngram = unicode(ngram[3:-1])
            elif ngram[:2] == "('" or ngram[:2] == '("':
                ngram = unicode(ngram[2:-1])
            else:
                print 'skipping invalid line:', line
                continue                
            id = id[:-1]
            id_ngram_map[id] = ngram
    return id_ngram_map


def read_ngram_ids_file(ngram_ids_filepath):
    ngram_id_counts_map = {}
    with open(ngram_ids_filepath, 'rb') as f:
        ngram_id_counts_map = pickle.load(f)
    return ngram_id_counts_map


def filter_ngrams(shard_id_ngram_map, ngram_id_counts_map, filter_map):
    for id, count in ngram_id_counts_map.iteritems():
        if count < COUNT_CUTOFF:
            continue
        if id in shard_id_ngram_map:
            filter_map[id] = shard_id_ngram_map[id]


def main():
    filter_map = {}

    print 'reading pickle file...'
    ngram_id_counts_map = read_ngram_ids_file(NGRAM_ID_COUNTS_FILE)
    print 'pickle file loaded'
    
    vocab_shard_names = [VOCAB_DATA_DIR + '/' + kPrefix + '%05d' % (shardnum)
                         for shardnum in range(NUM_VOCAB_SHARDS)]
    for vocab_shard_name in vocab_shard_names:
        print 'Filtering', vocab_shard_name
        shard_id_ngram_map = read_ngram_file(vocab_shard_name)
        filter_ngrams(shard_id_ngram_map, ngram_id_counts_map, filter_map)

    print 'There were orginally', len(ngram_id_counts_map), 'n-grams'
    print 'The fitered n-gram dictionary has', len(filter_map), 'n-grams'

    if filter_map:
        output_filepath = '.'.join([OUTPUT_FILE_PREFIX, 'num_shards', 
                                    str(NUM_VOCAB_SHARDS), 'cutoff', str(COUNT_CUTOFF)])
        with open(output_filepath, 'wb') as f:
            pickle.dump(filter_map, f)


if __name__ == '__main__':
    main()

