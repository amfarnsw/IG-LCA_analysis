import pandas as pd
import fusion_version_stripped as fsc
import os
idx = os.getenv('SLURM_ARRAY_TASK_ID')


case_parameters = pd.read_csv("case_settings.csv")
case = int(idx)
region = case_parameters.iloc[case,0]
cap = case_parameters.iloc[case,1]
OCC_fusion = case_parameters.iloc[case,2]
fsc.single_case(region,cap, OCC_fusion)
