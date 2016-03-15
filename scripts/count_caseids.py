#!/usr/bin/python

# Results:

# num unique caseids:  373146
# Number of cases with 1 opinions: 337606
# Number of cases with 2 opinions: 33671
# Number of cases with 3 opinions: 1839
# Number of cases with 4 opinions: 30
#
# Implications: 90% of the 373,146 cases only have 1 opinion. 
# Question: When only one opinion is given, can we assume it is the majority opinion?

import sys

FILE_PREFIX = '/Users/pinesol/mlcs_data/docvec_text/part-'
filenames = [FILE_PREFIX+'%05d' % (shardnum) for shardnum in range(1340)]

caseid_counts = {}

filecount = 0

for filename in filenames:
    with open(filename, 'rb') as f:
        for line in f:
            caseid_end = line.find('||')
            assert caseid_end != -1
            assert line[:2] == "('" or line[:2] == "(\"", line[:2]
            caseid = line[2:caseid_end] # cut out the initial ('
            if caseid not in caseid_counts:
                caseid_counts[caseid] = 0
            caseid_counts[caseid] += 1
    if filecount % 50 == 0:
        print filename
    filecount += 1

print 'num unique caseids: ', len(caseid_counts)

histogram = {}
for caseid, counts in caseid_counts.iteritems():
    if counts not in histogram:
        histogram[counts] = 0
    histogram[counts] += 1 

for num_counts, num in histogram.iteritems():
    print "Number of cases with %d opinions: %d" % (num_counts, num)
