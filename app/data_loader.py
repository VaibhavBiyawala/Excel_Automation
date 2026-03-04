import pandas as pd

def load_files(file1_path, file2_path, file3_path):
    
    file1 = pd.read_csv(file1_path, skiprows=4)
    file2 = pd.read_excel(file2_path)
    file3 = pd.read_excel(file3_path)

    # Ensure consistent column names
    file1.rename(columns={'TRF ID': 'trf_id'}, inplace=True)
    file2.rename(columns={'id': 'trf_id'}, inplace=True)
    file3.rename(columns={'entity_id': 'trf_id'}, inplace=True)
    return file1, file2, file3