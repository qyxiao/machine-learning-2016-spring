"""Code for parsing docvec_text shards into a sparse matrix."""

__author__ = 'Alex Pine'

import collections
import cPickle as pickle
import extract_metadata
import numpy as np
import os
import random
import scipy.sparse
import sklearn.datasets
import sklearn.feature_extraction
from sklearn.preprocessing import OneHotEncoder
import sys
import time

# Constants
CASE_DATA_FILENAME = 'merged_caselevel_data.csv'
SHARD_FILE_PREFIX = 'part-'
OPINION_DATA_DIR = 'docvec_text'
# NOTE: change this to control the number of shard files to read. Max number is 1340.
TOTAL_NUM_SHARDS = 1340
NGRAM_COUNTS_FILE_PREFIX = 'total_ngram_counts.p.'

# A global variable hack to be set when the program is run.
GLOBAL_INPUT_DATA_DIR = None

# Stats:
# num unique case_ids:  17178
# Number of cases with 1 opinions: 15466
# Number of cases with 2 opinions: 1630
# Number of cases with 3 opinions: 82


def extract_docvec_lines(case_ids, opinion_data_dir, num_opinion_shards, 
                         print_stats=False):
    """
    Opens the court opinion n-gram files, and extracts the lines that have a
    case_id in the given list. 
    NOTE: Only case_ids with exactly one opinion are returned.

    Args:
      case_ids: an iterable of case ID strings.
      opinion_data_dir: string. The directory that contains the court opinion 
        n-grams.
      num_opinion_shards: The maximum number of opinion shard files to read.
      print_stats: If true, prints the number of opinions per case_id.

    Returns:
      A dict that maps a case_id string to a '||' delimited opinion n-gram line.
    """
    # NOTE: Throwing out cases with more than one opinion.
    case_ids = frozenset(case_ids)
    # convert case_ids to a hashset for fast lookup
    filenames = [opinion_data_dir + '/' + SHARD_FILE_PREFIX + '%05d' % (shardnum) 
                 for shardnum in range(num_opinion_shards)]
    case_id_counts = collections.defaultdict(int)
    case_id_opinion_lines = collections.defaultdict(list)

    for filename in filenames:
        with open(filename, 'rb') as f:
            for line in f:
                line = line.strip()
                case_id_end = line.find('||')
                assert case_id_end != -1
                assert line[:2] == "('" or line[:2] == "(\"", line[:2]
                assert line[-2:] == "')" or line[-2:] == "\")", line[-2:]
                case_id = line[2:case_id_end] # cut out the initial ('
                line = line[2:-2] # cut out the (' and ')
                if case_id in case_ids:
                    case_id_counts[case_id] += 1
                    case_id_opinion_lines[case_id].append(line)
    if print_stats:
        print 'num unique case_ids: ', len(case_id_opinion_lines)
        histogram = {}
        for case_id, count in case_id_counts.iteritems():
            if count not in histogram:
                histogram[count] = 0
            histogram[count] += 1 

        for num_counts, num in histogram.iteritems():
            print "Number of cases with %d opinions: %d" % (num_counts, num)
    # Deleting items with more than one opinion
    for case_id, count in case_id_counts.iteritems():
        if count > 1:
            del case_id_opinion_lines[case_id]
    # The return dict does case_id -> line.
    return {case_id: lines[0] for case_id, lines, in case_id_opinion_lines.iteritems()}


def filter_infrequent_ngrams(rows_ngram_counts, case_ids, min_required_count, 
                             write_total_counts_to_disk=True):
    """
    Counts the number of times each n-gram occurs throughout the corpus, and 
    filters out the low-occuring ones.
    As a side effect, this also writes the total_ngram_counts dict to disk in
    GLOBAL_INPUT_DATA_DIR. I want to use this to decode the data dictionary.

    Args:
      rows_ngram_counts: The list of n-gram counts for each case.
      case_ids: The case IDs corresponding to each set of n-grams.
      min_required_count: Positive integer. The minimum number of times an
        n-gram must occur in total in order to be left in.

    Returns:
      filtered_rows_ngram_counts: The list of n-gram counts for each case. The
        infrequently occuring n-grams have been filtered out. If all of the 
          n-grams of a document were removed, the whole row was removed.
      filtered_case_ids: The case IDs corresponding to each set of filtered 
        n-grams.
    """
    print 'Computing total n-gram counts...'
    total_ngram_counts = collections.defaultdict(int)
    for ngram_counts in rows_ngram_counts:
        for ngram_id, count in ngram_counts.iteritems():
            total_ngram_counts[ngram_id] += count

    # <HACK> to save the total counts dict to a file
    if GLOBAL_INPUT_DATA_DIR:
        filename = GLOBAL_INPUT_DATA_DIR + '/' + NGRAM_COUNTS_FILE_PREFIX + str(len(case_ids))
        if os.path.isfile(filename):
            print 'Writing n-gram counts to disk...'
            with open(filename, 'wb') as f:
                pickle.dump(total_ngram_counts, f)
        else:
            print 'NGram counts file already exists, skipping generation.'
    # </HACK>

    print 'Filtering n-grams...'
    ngrams_to_keep = set([])
    for ngram_id, count in total_ngram_counts.iteritems():
        if count >= min_required_count:
            ngrams_to_keep.add(ngram_id)

    # Note: a desperate attempt to free up memory
    del total_ngram_counts

    row_indices_to_delete = []
    for i, ngram_counts in enumerate(rows_ngram_counts):
        ngram_ids = ngram_counts.keys()
        num_ngrams_deleted = 0
        for ngram_id in ngram_ids:
            if ngram_id not in ngrams_to_keep:
                del ngram_counts[ngram_id]
                num_ngrams_deleted += 1
        if len(ngram_ids) == num_ngrams_deleted:
            row_indices_to_delete.append(i)
    # The rows and their corresponding and case_ids that had all their ngrams
    # deleted should be removed entirely.
    # NOTE: deleting indices in reverse order is necessary.
    for i in sorted(row_indices_to_delete, reverse=True):
        del rows_ngram_counts[i]
        del case_ids[i]

    assert len(rows_ngram_counts) == len(case_ids)
    return rows_ngram_counts, case_ids


def parse_opinion_shards(case_ids, opinion_data_dir, num_opinion_shards):
    """
    Builds a dictionary containing the n-gram counts from the court opinion
    shard files.
    NOTE: This takes ~10 minutes to run on my macbook on all shards.

    Args:
      case_ids: The list of case_ids to extract.
      opinion_data_dir: The directory where the opinion n-gram shard files
        reside.
      num_opinion_shards: The number of opinion shard files to read in. Defaults
        to TOTAL_NUM_SHARDS.

    Returns:
      rows_ngram_counts: A list of dictionaries containing n-gram counts.
      ordered_case_ids: A list of case ID strings. The index of each case ID
        corresponds to the index of corresponding row of n-grams in
        sparse_feature_matrix.
    """
    print 'Parsing opinion shard files...'
    # Extract only the n-grams with the given case IDs
    case_id_opinion_lines = extract_docvec_lines(case_ids, opinion_data_dir, 
                                                 num_opinion_shards)
    # Constants needed to parse opinion lines
    SEPARATOR = "', '"
    SEPARATOR_ALT = "\", '"
    NGRAM_SEPARATOR = "||"

    # This case_ids will be sorted in the order that the final matrix is sorted.
    filtered_case_ids = case_id_opinion_lines.keys()
    # List of dictionaries of ngram counts
    rows_ngram_counts = []

    for case_id in filtered_case_ids:
        opinion_line = case_id_opinion_lines[case_id]
        # Each line into metadata portion and ngram portion, separated by either
        # ', ' or ", '
        separator_index = opinion_line.find(SEPARATOR)
        if separator_index == -1:
            separator_index = opinion_line.find(SEPARATOR_ALT)
            assert separator_index != -1, 'Unparsable opinion line. Case ID: %s' % (case_id)
        ngram_line = opinion_line[separator_index+len(SEPARATOR):]
        assert len(ngram_line) > 0 and ngram_line[0] != "'" and ngram_line[-1] != "'", 'bad ngram line at case %s' % (case_id)
        ngrams = ngram_line.split('||')
        ngram_counts = {}
        for ngram in ngrams:
            ngram_id, count = ngram.split(':')
            assert ngram_id != '', 'Bad ngram ID: %s' % ngram_id
            count = int(count)
            assert count > 0, 'Bad ngram count %d' % count
            ngram_counts[ngram_id] = count
        rows_ngram_counts.append(ngram_counts)
    # Testing code
    assert len(rows_ngram_counts) == len(filtered_case_ids)
    for i in random.sample(range(len(rows_ngram_counts)), len(rows_ngram_counts)/100):
        case_id = filtered_case_ids[i]
        opinion_line = case_id_opinion_lines[case_id]
        ngram_counts = rows_ngram_counts[i]
        for ngram_id, count in ngram_counts.iteritems():
            assert opinion_line.find(case_id) != -1
            assert opinion_line.find(ngram_id) != -1
            assert opinion_line.find(str(count)) != -1

    return rows_ngram_counts, filtered_case_ids


def sort_case_lists(cases_df, rows_ngram_counts, case_ids):
    """
    Sorts the ngram_count dictionaries and case_ids by the date that each case 
    occured on, from oldest to newest.

    Args:
      cases_df: The dataframe of cases information. Used to get the case dates.
      rows_ngram_counts: The list of n-gram counts for each case.
      case_ids: The case IDs corresponding to each set of n-grams.

    Returns:
      rows_ngram_counts: The list of n-gram counts for each case, sorted by the
        date of the corresponding case.
      case_ids: The case IDs corresponding to each set of n-grams, sorted by the
        date of the corresponding case.
    """
    # Case ID -> date as integer YYYYMMDD.
    case_id_date_map = {}
    for index, row in cases_df.iterrows():
        date_int = int(str(row['year']) + str(int(float(row['month']))).zfill(2)
                       + str(int(float(row['day']))).zfill(2))
        case_id_date_map[row['caseid']] = date_int
    # This creates a list of (index, case_id) pairs, sorted by the date 
    # corresponding to the case ID.
    sorted_index_case_id_pairs = sorted(enumerate(case_ids), 
                                        key=lambda tup: case_id_date_map[tup[1]])

    case_ids = [case_ids[i] for i, caseid in sorted_index_case_id_pairs]
    rows_ngram_counts = [rows_ngram_counts[i] 
                         for i, caseid in sorted_index_case_id_pairs]

    # testing code
    sorted_dateints = [case_id_date_map[caseid] 
                       for i, caseid in sorted_index_case_id_pairs]
    assert sorted_dateints == sorted(sorted_dateints)

    return rows_ngram_counts, case_ids

def filter_cases_df(cases_df,case_ids):
    """
    Pares down the cases dataframe, which has coded data,
    to match the number and order of the case_ids list.
    args:
      cases_df: A dataframe containing the case variables.
      case_ids: list of sorted case_ids
    returns:
      filtered_cases_df: Dataframe containing the sorted, filtered case variables
    """
    foo = cases_df.set_index('caseid')
    filtered_cases_df = foo.loc[case_ids,:]
    return filtered_cases_df

def get_coded_data(cases_df, case_ids, coded_feature_names):
    """
    Retrieves the valences corresponding to case_ids, 
    along with coded features, if any
    Recode unknown valences to neutral.
    args:
      cases_df: A dataframe containing the case variables.
      case_ids: list of sorted case_ids
      coded_feature_names: list of column names to pull from cases_df (ie 'geniss' or ['geniss','casetyp1'])
    returns:
      valences: np array of valences
      coded_feature_array: np array of coded features
      filtered_cases_df: Dataframe containing the sorted, filtered case variables
    """
    UNKNOWN_VALENCE = 0
    NEUTRAL_VALENCE = 2

    if isinstance(coded_feature_names, str):
        coded_feature_names = [coded_feature_names]

    print "coded_feature_names: ",coded_feature_names

    valences = []
    coded_feature_list = []
    for case_id in case_ids:
        valence = cases_df[cases_df['caseid'] == case_id]['direct1'].values[0]
        if np.isnan(valence)==False:
            valence = int(valence)
        else: valence = 2

        if coded_feature_names is not None:
            coded_feature_row = cases_df[cases_df['caseid'] == case_id][coded_feature_names].values[0]
            clean_row = []

            #clean row
            for val in coded_feature_row:
                if val and np.isnan(val) == False:
                    clean_row.append(int(val))
                else:
                    clean_row.append(0)
            assert clean_row[0]>=0, ""
            coded_feature_list.append(clean_row)
            
        # Replacing unknown valence variables with netural scores.
        if valence == UNKNOWN_VALENCE:
            valence = NEUTRAL_VALENCE
        valences.append(valence)

    #one-hot encoding
    if coded_feature_names is not None:
        enc = OneHotEncoder()
        coded_feature_array = enc.fit_transform(np.array(coded_feature_list))
        print "Coded Feature Array shape: ", coded_feature_array.shape
    else: 
        coded_feature_array = np.array([])

    #Filter case df
    filtered_case_df = filter_cases_df(cases_df,case_ids)

    return np.array(valences),coded_feature_array,filtered_case_df


def construct_sparse_opinion_matrix(cases_df, opinion_data_dir,
                                    num_opinion_shards,
                                    min_required_count,
                                    tfidf,
                                    coded_feature_names):
    """
    Builds a CSR sparse matrix containing the n-gram counts from the court
    opinion shard files. Also returns the corresponding case_ids and valences.
    The rows of these lists are sorted in order of the dates of the
    corresponding cases, oldest to newest.
    NOTE: This takes ~10 minutes to run with all shards on my macbook.

    Args:
      cases_df: A dataframe containing the case variables. Must include caseid, 
        year, month, day, and direct1.
      opinion_data_dir: The directory where the opinion n-gram shard files
        reside.
      num_opinion_shards: The number of opinion shard files to read in. 
      min_required_count: The minimum number of of times an n-gram must appear
        throughout all documents in order to be included in the data.
      tfidf: Boolean. If set, the returned feature matrix has been normalized
        using TF-IDF.
      coded_feature_names: None or list of features to include from the coded data set.

    Returns:
      sparse_feature_matrix: A scipy.sparse.csr_matrix with n-gram counts.
      ordered_case_ids: A list of case ID strings. The index of each case ID
        corresponds to the index of corresponding row of n-grams in
        sparse_feature_matrix.
      valences: A list of valences as ints, with the unknown valences (0) 
        replaced with the neutral valence (2).
      filtered_cases_df: Dataframe containing the sorted, filtered case variables 
      ngram_ids: The list of ngram IDs corresponding to the columns of 
        sparse_feature_matrix. If coded_feature_names are included, those
        features won't be included in this list.
    """
    case_ids_df = cases_df['caseid']

    rows_ngram_counts, case_ids = parse_opinion_shards(
        case_ids_df, opinion_data_dir, num_opinion_shards)

    if min_required_count > 1:
        rows_ngram_counts, case_ids = filter_infrequent_ngrams(
            rows_ngram_counts, case_ids, min_required_count)

    rows_ngram_counts, case_ids = sort_case_lists(cases_df, rows_ngram_counts, 
                                                  case_ids)

    valences,coded_feature_matrix,filtered_cases_df = get_coded_data(cases_df, case_ids,coded_feature_names)

    print 'Building sparse matrix...'
    # Make sure the matrics created by this vectorizer are sparse.
    # set sort=False so that the ordering of the rows by date is preserved.
    dict_vectorizer = sklearn.feature_extraction.DictVectorizer(
        sparse=True, sort=False)
    sparse_feature_matrix = dict_vectorizer.fit_transform(rows_ngram_counts)

    ngram_ids = dict_vectorizer.get_feature_names()

    if tfidf:
        print 'Running tfidf transformation...'
        transformer = sklearn.feature_extraction.text.TfidfTransformer()
        sparse_feature_matrix = transformer.fit_transform(sparse_feature_matrix)

    if coded_feature_matrix.shape[0]>0:
        print 'Including coded features:', coded_feature_names
        assertion_string = "Matrices have different number of rows.  N-gram matrix has %r, coded_feature_matrix has %r" %(sparse_feature_matrix.shape[0],coded_feature_matrix.shape[0])
        assert sparse_feature_matrix.shape[0]==coded_feature_matrix.shape[0], assertion_string
        sparse_feature_matrix = scipy.sparse.hstack([sparse_feature_matrix,coded_feature_matrix],format='csr')

    assert sparse_feature_matrix.shape[0] == len(case_ids)
    assert len(valences) == len(case_ids)

    print 'shape: ', sparse_feature_matrix.get_shape()
    print 'number of cases', len(case_ids)

    return sparse_feature_matrix, case_ids, valences,filtered_cases_df, ngram_ids


def build_filenames_from_params(output_data_dir, num_shards, min_required_count,
                                tfidf,coded_feature_names):
    """
    Builds filenames that include the given parameter values in them, for 
    documentation.

    Args:
      output_data_dir: The base directory for all output files.
      num_opinion_shards: The number of opinion shard files to read in.
      min_required_count: The minimum number of of times an n-gram must appear
        throughout all documents in order to be included in the data.
      tfidf: Boolean. If set, the returned feature matrix has been normalized
        using TF-IDF.
      coded_feature_names: None or list of features to include from the coded data set.
    Returns:
      feature_matrix_filename: A string to be used as the name of the feature
        matrix file.
      case_ids_filename: A string to be used as the name of the case IDs file.
      ngram_ids_filename: A string to be used as the name of the ngram IDs file.
    """
    feature_matrix_filename = '%s/feature_matrix.svmlight.shards.%d.mincount.%d' % (
        output_data_dir, num_shards, min_required_count)
    case_ids_filename = '%s/case_ids.shards.p.%d.mincount.%d' % (
        output_data_dir, num_shards, min_required_count)
    cases_df_filename = '%s/cases_df.shards.p.%d.mincount.%d' % (
        output_data_dir, num_shards, min_required_count)
    ngram_ids_filename = '%s/ngram_ids.shards.p.%d.mincount.%d' % (
        output_data_dir, num_shards, min_required_count)
    if tfidf:
        feature_matrix_filename += '.tfidf'
        case_ids_filename += '.tfidf'
        cases_df_filename += '.tfidf'
    if coded_feature_names is not None:
        feature_matrix_filename += "."+str(coded_feature_names)
        case_ids_filename += "."+str(coded_feature_names)
        cases_df_filename += "."+str(coded_feature_names)     
    return feature_matrix_filename, case_ids_filename, cases_df_filename, ngram_ids_filename


def load_data(input_data_dir, output_data_dir,
              num_opinion_shards, min_required_count,
              tfidf,coded_feature_names):
    """
    Looks to see if the file containing the feature matrix and target labels 
    exists, along with the file containing their corresponding case IDs. If so, 
    this loads them into memory and returns them. Otherwise, it calls
    construct_sparse_opinion_matrix to construct the them. Once they have been 
    constructed, it saves them to disk and returns them.

    Args:
      input_data_dir: The directory that contains all input data. This directory
        should contain another directory that contains the ngram shard files
        (aka OPINION_DATA_DIR).
      output_data_dir: The directory where the generated data should be written
        if it has to be generated from scratch.
      num_opinion_shards: The number of opinion shard files to read in.
      min_required_count: The minimum number of of times an n-gram must appear
        throughout all documents in order to be included in the data.
      tfidf: Boolean. If set, the returned feature matrix has been normalized
        using TF-IDF.
      coded_feature_names: None or list of features to include from the coded data set.

    Returns:
      sparse_feature_matrix: A scipy.sparse.csr_matrix with n-gram counts.
      ordered_case_ids: A list of case ID strings. The index of each case ID
        corresponds to the index of corresponding row of n-grams in
        sparse_feature_matrix.
      valences: A list of valences as ints, with the unknown valences (0) 
        replaced with the neutral valence (2).
      parameters_dict: dictionary of parameters, for debugging
      ngram_ids: The list of ngram IDs corresponding to the columns of 
        sparse_feature_matrix. If coded_feature_names are included, those
        features won't be included in this list.
    """
    start_time = time.time()

    print 'Data parameters:'
    print '  Number of opinion shards:', num_opinion_shards
    print '  Minimum required count:', min_required_count
    print '  Using TF-IDF:', tfidf

    #save parameters
    parameters_dict={}
    for i in ('num_opinion_shards', 'min_required_count','tfidf','coded_feature_names'):
        parameters_dict[i] = locals()[i]

    # Look to see if the data files have already been saved to disk.
    feature_matrix_filename, case_ids_filename,cases_df_filename, ngram_ids_filename = build_filenames_from_params(
        output_data_dir, num_opinion_shards, min_required_count, tfidf,coded_feature_names)

    if os.path.isfile(feature_matrix_filename) and os.path.isfile(case_ids_filename) and os.path.isfile(cases_df_filename):
        with open(feature_matrix_filename, 'rb') as f:
            sparse_feature_matrix, valences = sklearn.datasets.load_svmlight_file(f)
        with open(case_ids_filename, 'rb') as f:
            case_ids = pickle.load(f)
        with open(cases_df_filename, 'rb') as f:
            filtered_cases_df = pickle.load(f)
        with open(ngram_ids_filename, 'rb') as f:
            ngram_ids = pickle.load(f)
        print 'Data loaded from', feature_matrix_filename, ',', case_ids_filename,',' ,cases_df_filename,',', ngram_ids_filename
    else:
        print 'Constructing data from scratch...'
        print 'Reading input data from from:', input_data_dir
        cases_df = extract_metadata.extract_metadata(input_data_dir + '/' + CASE_DATA_FILENAME)
        opinion_data_dir = input_data_dir + '/' + OPINION_DATA_DIR
        # <HACK> to save the total counts dict to a file
        global GLOBAL_INPUT_DATA_DIR
        GLOBAL_INPUT_DATA_DIR = input_data_dir
        # </HACK>
        sparse_feature_matrix, case_ids, valences,filtered_cases_df, ngram_ids = construct_sparse_opinion_matrix(
            cases_df, opinion_data_dir, 
            num_opinion_shards, min_required_count, 
            tfidf, coded_feature_names)
        print 'Writing input data to disk...'
        sklearn.datasets.dump_svmlight_file(sparse_feature_matrix, valences, 
                                            feature_matrix_filename)
        with open(case_ids_filename, 'wb') as f:
            pickle.dump(case_ids, f)
        with open(cases_df_filename, 'wb') as f:
            pickle.dump(filtered_cases_df, f)
        with open(ngram_ids_filename, 'wb') as f:
            pickle.dump(ngram_ids, f)
        print 'Feature matrix saved as %s' % feature_matrix_filename
        print 'Case IDs saved as %s' % case_ids_filename
        print 'Cases DF saved as %s' % cases_df_filename
        print 'NGram IDs saved as %s' % ngram_ids_filename

    print 'Total time spent building data:', time.time() - start_time
    return sparse_feature_matrix, case_ids, valences, filtered_cases_df,parameters_dict, ngram_ids


if __name__ == '__main__':
    # Main Parameters
    num_opinion_shards = 20 #1340
    min_required_count = 20 #150
    tfidf = True
    coded_feature_names=None
    input_data_dir = '/scratch/cdg356/data'
    output_data_dir = '/scratch/cdg356/data'

    coded_feature_names = None # TODO 

    load_data(input_data_dir,
              output_data_dir,
              num_opinion_shards,
              min_required_count,
              tfidf,coded_feature_names)
