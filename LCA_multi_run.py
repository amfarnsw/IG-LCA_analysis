import pandas as pd
import LCA_version as rn
import os
idx = os.getenv('SLURM_ARRAY_TASK_ID')


case_parameters = pd.read_csv("LCA_case_settings.csv")
case = int(idx)
region = case_parameters.iloc[case,0]
cap = case_parameters.iloc[case,1]
rn.single_case(region,cap)
