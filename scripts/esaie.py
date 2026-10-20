import pandas as pd 
import os 

df = pd.read_excel("D:/stage 2026/Project_new_version/Project-ETL-for-Credits/data/raw/damane sakane genre/2025/août not like others _2025.xls", header=None)
for i, row in df.iterrows():
    print(i, row.tolist())