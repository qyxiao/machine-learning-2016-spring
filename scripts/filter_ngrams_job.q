#!/bin/bash

## A qsub job that filters the ngrams

## One node, 1 core
#PBS -l nodes=1:ppn=2
## Quit if this takes longer than eight hours.
#PBS -l walltime=8:00:00
## Give it 64 GB of memory
#PBS -l mem=64GB
## Job name
#PBS -N filter_all_ngrams
## Pipeline output and errors to the same file
#PBS -j oe
## Email when a job starts, ends, or aborts
#PBS -m abe 
## Email address to which errors are sent.
#PBS -M alex.pine@nyu.edu

module purge

cd /home/akp258/appeals/

ipython scripts/filter_ngrams.py
