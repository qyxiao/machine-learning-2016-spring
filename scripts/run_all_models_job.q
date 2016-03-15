#!/bin/bash

## A qsub job that runs all of our models

## One node, many cores (apparently most nodes have 12 or 20 cores).
#PBS -l nodes=1:ppn=8
## Quit if this takes longer than eight hours.
#PBS -l walltime=8:00:00
## Give it 128 GB of memory
#PBS -l mem=128GB
## Job name
#PBS -N run_all_appeals_models
## Pipeline output and errors to the same file
#PBS -j oe
## Email when a job starts, ends, or aborts
#PBS -m abe 
## Email address to which errors are sent.
#PBS -M alex.pine@nyu.edu

module purge

cd /home/akp258/appeals/

ipython scripts/models.py
