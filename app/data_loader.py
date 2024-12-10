import pandas as pd
import os

def load_files(file1, file2, file3, file4):
    
    file1 = pd.read_csv(os.path.join('..', 'input', file1))
    file2 = pd.read_excel(os.path.join('..', 'input', file2))
    file3 = pd.read_excel(os.path.join('..', 'input', file3))
    file4 = pd.read_excel(os.path.join('..', 'input', file4))

    # Ensure consistent column names
    file1.rename(columns={'TRF ID': 'trf_id'}, inplace=True)
    file2.rename(columns={'id': 'trf_id'}, inplace=True)
    file3.rename(columns={'entity_id': 'trf_id'}, inplace=True)
    return file1, file2, file3, file4
