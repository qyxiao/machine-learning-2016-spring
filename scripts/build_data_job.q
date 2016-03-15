#!/bin/bash

## A qsub job that builds the ML dataset

#PBS -l nodes=1:ppn=1
#PBS -l walltime=1:00:00
#PBS -l mem=64GB
#PBS -N build_opinion_data
#PBS -j oe
#PBS -M charles.d.guthrie@gmail.com

cd /scratch/cdg356/appeals

module purge
module load scikit-learn/intel/0.15.1
module load numpy/intel/1.8.1
module load scipy/intel/0.16.0


ipython scripts/join_data.py
