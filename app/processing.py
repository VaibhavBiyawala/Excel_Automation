import re
import pandas as pd

# Case 1: Extract TRF ID and UTR from Payment Note
def handle_case1(payment_note):
    utr_match = re.search(r'(UTIBR|AXIS)[0-9A-Z]*(-|.| )', payment_note)
    trf_id_match = re.search(r'(trf_[^ ]+)', payment_note)
    utr = utr_match.group(0)[:-1] if utr_match else None
    trf_id = trf_id_match.group(0) if trf_id_match else None
    return trf_id, utr, None, None, 'case1'

# Case 2: Match using `file2` and `file3`
def handle_case2(payment_mode, file2, file3, file1_amount):
    pay_match = re.search(r'pay_[0-9a-zA-Z]+', payment_mode)
    if not pay_match:
        return None, None, None, None, None

    pay_value = pay_match.group(0)
    match3 = file3[file3['trf_id'] == pay_value]
    if match3.empty:
        return None, None, None, None, None

    order_id = match3.iloc[0]['order_id']
    matches_file2 = file2[file2['source'] == order_id]
    if matches_file2.empty:
        return None, None, None, None, None

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

# Main processing function for each row
def process_row(row, file2, file3):
    if pd.notnull(row.get('UTR')) and not pd.isna(row.get('case_flag')):  # Skip already processed rows
        return row['trf_id'], row['UTR'], row.get('Amount(₹)', 0), 0, 'processed'

    if row['trf_id'] == '-':  # Handle missing TRF ID
        payment_note = str(row.get('Payment Note', '')).strip()
        payment_mode = str(row.get('Payment mode', '')).strip()

        if payment_note and payment_note.lower() != 'nan':  # Case 1
            return handle_case1(payment_note)

        if pd.isnull(payment_note) or payment_note == '' or payment_note.lower() == 'nan':  # Case 2
            file1_amount = row['Amount(₹)']
            return handle_case2(payment_mode, file2, file3, file1_amount)

    # Default case: no processing required
    return row['trf_id'], row.get('UTR', None), None, None, None

# Process unmatched rows
def process_unmatched_rows(file1, file2, file3):
    for idx, row in file1.iterrows():
        if pd.notnull(row['UTR']) and row['case_flag'] != 'case1':
            continue

        trf_id = row['trf_id']
        match2 = file2[file2['trf_id'] == trf_id]
        if not match2.empty:
            file1.at[idx, 'UTR'] = match2.iloc[0]['settlement_utr']
            file1.at[idx, 'Rozarpay'] = match2.iloc[0]['amount']
        else:
            match3 = file3[file3['trf_id'] == trf_id]
            if not match3.empty:
                file1.at[idx, 'UTR'] = match3.iloc[0]['settlement_utr']
                file1.at[idx, 'Rozarpay'] = match3.iloc[0]['amount']

        file1.at[idx, 'difference'] = (
            row['Amount(₹)'] - file1.at[idx, 'Rozarpay'] if pd.notnull(file1.at[idx, 'Rozarpay']) else None
        )
