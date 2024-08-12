#!/bin/bash
#SBATCH -o amanda_job_array.sh.log-%j-%a
#SBATCH -a 0-170
#SBATCH -c 40
# Initialize Modules
source /etc/profile
module load anaconda/2023a
module load gurobi
python LCA_multi_run.py $SLURM_ARRAY_TASK_ID
