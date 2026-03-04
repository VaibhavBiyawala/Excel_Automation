import os
import pandas as pd

# Reorder columns to the desired format
def reorder_columns(file1):
    file1.rename(columns={'trf_id': 'TRF ID'}, inplace=True)
    desired_column_order = [
        'Receipt', 'Payer name', 'Payer type', 'Section / Department', 'TRF ID', 'UTR', 
        'Payment Note', 'Collection', 'Payment date', 'Rozarpay', 'Amount(₹)', 'difference', 
        'Payment mode', 'Cashier(Employee)', 'Receipt created date and time'
    ]
    return file1[desired_column_order]

# Save the final output to Excel
def save_output(file1, filename='result_file_all.xlsx'):
    file1.to_excel(filename, index=False)
    return filename

def load_trans_his_files(file_path):
    file = pd.read_excel(file_path, skiprows=5, header=None)
    account_no = str(file.iloc[0, 0][-12:])  
    file = pd.read_excel(file_path, skiprows=6)
    file['Account Number'] = account_no    
    return file

