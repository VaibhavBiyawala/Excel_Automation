import pandas as pd
import re

# Read the three Excel files
file1 = pd.read_csv('13150114648874_fee_reciept.csv')
file2 = pd.read_excel('Transfer Nov 2024.xlsx')
file3 = pd.read_excel('Combine November 2024.xlsx')

# Ensure consistent column names
file1.rename(columns={'TRF ID': 'trf_id'}, inplace=True)
file2.rename(columns={'id': 'trf_id'}, inplace=True)
file3.rename(columns={'entity_id': 'trf_id'}, inplace=True)

print(file1.columns)

def process_trf_and_utr(row, file2, file3):
    if pd.notnull(row.get('UTR')) and not pd.isna(row.get('case1_flag')):  # Skip rows not requiring processing
        return row['trf_id'], row['UTR'], row.get('Amount(₹)', 0), 0, 'processed'

    if row['trf_id'] == '-':  # Check for missing TRF ID
        payment_note = str(row.get('Payment Note', '')).strip()
        payment_mode = str(row.get('Payment mode', '')).strip()

        # Case 1: Extract TRF ID and UTR from Payment Note
        if payment_note and payment_note.lower() != 'nan':
            utr_match = re.search(r'(UTIBR|AXIS)[0-9A-Z]*(-|.| )', payment_note)
            trf_id_match = re.search(r'(trf_[^ ]+)', payment_note)

            utr = utr_match.group(0)[:-1] if utr_match else None
            trf_id = trf_id_match.group(0) if trf_id_match else None

            return trf_id, utr, None, None, 'case1'

        # Case 2: Null or empty Payment Note
        if pd.isnull(payment_note) or payment_note == '' or payment_note.lower() == 'nan':
            pay_match = re.search(r'pay_[0-9a-zA-Z]+', payment_mode)
            if not pay_match:
                return None, None, None, None, None

            pay_value = pay_match.group(0)
            match3 = file3[file3['trf_id'] == pay_value]
            if match3.empty:
                return None, None, None, None, None

            # Fetch `order_id` and match in `file2`
            order_id = match3.iloc[0]['order_id']
            matches_file2 = file2[file2['source'] == order_id]
            if matches_file2.empty:
                return None, None, None, None, None

            # Filter by matching amounts
            file1_amount = row['Amount(₹)']
            final_matches = matches_file2[matches_file2['amount'] == file1_amount]

            if final_matches.empty:
                return None, None, None, None, None

            selected_match = final_matches.iloc[0]
            file2.drop(index=selected_match.name, inplace=True)

            return (
                selected_match['trf_id'],
                selected_match['settlement_utr'],
                selected_match['amount'],
                file1_amount - selected_match['amount'],
                'case2'
            )

    # Default return for rows that do not match either case
    return row['trf_id'], row.get('UTR', None), None, None, None


# Apply the function to file1 rows for Case 1 and Case 2
file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
    lambda row: pd.Series(process_trf_and_utr(row, file2, file3)),
    axis=1
)

# Further processing for rows not handled by the previous step
for idx, row in file1.iterrows():
    # Skip rows already processed in the initial stage, unless they are from Case 1
    if pd.notnull(row['UTR']) and row['case_flag'] != 'case1':
        continue

    trf_id = row['trf_id']
    # Check in file2
    match2 = file2[file2['trf_id'] == trf_id]
    if not match2.empty:
        file1.at[idx, 'UTR'] = match2.iloc[0]['settlement_utr'] if pd.notnull(match2.iloc[0]['settlement_utr']) else None
        file1.at[idx, 'Rozarpay'] = match2.iloc[0]['amount']
    else:
        # Check in file3 if not found in file2
        match3 = file3[file3['trf_id'] == trf_id]
        if not match3.empty:
            file1.at[idx, 'UTR'] = match3.iloc[0]['settlement_utr'] if pd.notnull(match3.iloc[0]['settlement_utr']) else None
            file1.at[idx, 'Rozarpay'] = match3.iloc[0]['amount']

    # Calculate the difference
    file1.at[idx, 'difference'] = row['Amount(₹)'] - file1.at[idx, 'Rozarpay'] if pd.notnull(file1.at[idx, 'Rozarpay']) else None

# Remove unnecessary columns and save the updated DataFrame
file1.drop(columns=['case_flag'], inplace=True)

file1.rename(columns={'trf_id': 'TRF ID'}, inplace=True)

# Define the desired column order
desired_column_order = ['Receipt', 'Payer name', 'Payer type', 'Section / Department', 'TRF ID', 'UTR', 'Payment Note', 'Collection', 'Payment date', 
    'Rozarpay', 'Amount(₹)', 'difference', 'Payment mode', 'Cashier(Employee)', 'Receipt created date and time']

# Reorder the columns in file1
file1 = file1[desired_column_order]
file1.to_excel('result_file_4.xlsx', index=False)

print("Processing complete with corrections.")