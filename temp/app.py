import pandas as pd

# Read the three Excel files
file1 = pd.read_excel('fee_receipt.xlsx')
file2 = pd.read_excel('Transfer Nov 2024.xlsx')
file3 = pd.read_excel('Combine November 2024.xlsx')

columns_to_drop = ['UTR', 'Rozarpay', 'Diff']  
file1.drop(columns=columns_to_drop, inplace=True) 

# Ensure column names are consistent for processing
file1.rename(columns={'TRF ID': 'trf_id'}, inplace=True)
file2.rename(columns={'id': 'trf_id'}, inplace=True)
file3.rename(columns={'entity_id': 'trf_id'}, inplace=True)

# Initialize new columns in file1 for results
file1['utr'] = 0  # Default value for UTR if no match
file1['rozarpay'] = 0
file1['difference'] = 0

# Match and fetch data from file2 and file3
for idx, row in file1.iterrows():
    trf_id = row['trf_id']
    # Check in file2
    match2 = file2[file2['trf_id'] == trf_id]
    if not match2.empty:
        file1.at[idx, 'UTR'] = match2.iloc[0]['settlement_utr'] if pd.notnull(match2.iloc[0]['settlement_utr']) else 0
        file1.at[idx, 'rozarpay'] = match2.iloc[0]['amount']
    else:
        # Check in file3 if not found in file2
        match3 = file3[file3['trf_id'] == trf_id]
        if not match3.empty:
            file1.at[idx, 'UTR'] = match3.iloc[0]['settlement_utr'] if pd.notnull(match3.iloc[0]['settlement_utr']) else 0
            file1.at[idx, 'rozarpay'] = match3.iloc[0]['amount']

    # Calculate the difference
    file1.at[idx, 'difference'] = row['Amount(â‚¹)'] - file1.at[idx, 'rozarpay']

# Save the results to a new Excel file
file1.to_excel('result_file.xlsx', index=False)