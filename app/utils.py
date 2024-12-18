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
    filepath = filename
    file1.to_excel(filepath, index=False)
    return filepath

def concat_trans_his_files(file4_path, file5_path):
    file4 = pd.read_excel(file4_path, skiprows=5, header=None)
    account_no = str(file4.iloc[0, 0][-12:])  
    file4 = pd.read_excel(file4_path, skiprows=6)
    file4['Account Number'] = account_no

    
    file5 = pd.read_excel(file5_path, skiprows=5, header=None)
    account_no = str(file5.iloc[0, 0][-12:])  
    file5 = pd.read_excel(file5_path, skiprows=6)
    file5['Account Number'] = account_no    
    
    combined_file = pd.concat([file4, file5])
    output_path = file4_path  + 'x'
    combined_file.to_excel(output_path, index=False)
    
    return output_path

