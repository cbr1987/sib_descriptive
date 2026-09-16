#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 14:11:11 2026

@author: clarabelessiotis
"""

#!/bin/bash

#SBATCH --job-name=imagebank
# Update path and ensure logs dir is created
#SBATCH --output=/home/%u/imagebank/manual_rig_fsavg/synthseg/logs/%A_%a.out
#SBATCH --export=none
#SBATCH --cpus-per-task=4
# Requires 20G even though nan_slurm reports less used
#SBATCH --mem=30G
#SBATCH --time=3-6:00
# Run lines 1-5259 in batches of 5 at a time.
#SBATCH --array=1-93%5

source /software/system/modules/latest/init/bash
module use /software/system/modules/NaN/generic
module purge
module load nan

module load freesurfer

DATA_ROOT=${HOME}/


#find $HOME/imagebank -name "*.nii.gz" > images.index
INDEX=${DATA_ROOT}/images.index


OUTPUT=${DATA_ROOT}/synthseg/


echo "Running on $HOSTNAME"
echo "Array ID: $SLURM_ARRAY_JOB_ID"
echo "Task ID: $SLURM_ARRAY_TASK_ID"


FILE="`awk FNR==$SLURM_ARRAY_TASK_ID $INDEX`"

# Create a unique filename for the csv file
CSV_NAME=$(basename -s .nii.gz ${FILE}).csv
#QC_NAME=$(basename -s .nii.gz ${FILE})_qc.csv

# Log what we are processing
echo "Processing $FILE"

# Run the mri_synthseg command for this image
echo "mri_synthseg --i ${FILE} --o ${OUTPUT} --parc --robust --fast --vol ${OUTPUT}/${CSV_NAME} --qc ${OUTPUT}/${QC_NAME}"
mri_synthseg --i ${FILE} --o ${OUTPUT} --parc --robust --fast --vol ${OUTPUT}/${CSV_NAME} #--qc ${OUTPUT}/${QC_NAME}

echo "Complete"
