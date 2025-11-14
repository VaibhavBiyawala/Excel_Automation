import re
import pandas as pd

# Case 1: Extract TRF ID and UTR from Payment Note
# def handle_case1(payment_note):
#     utr_match = re.search(r'(UTIBR|AXIS)[0-9A-Z]*(-|.| )', payment_note)
#     trf_id_match = re.search(r'(trf_[^ ]+)', payment_note)
#     utr = utr_match.group(0)[:-1] if utr_match else None
#     trf_id = trf_id_match.group(0) if trf_id_match else None
#     return trf_id, utr, None, None, 'case1'

def handle_case1(payment_note):
    # Updated regex for UTR
    utr_match = re.search(r'(UTIBR|AXISCN)[0-9]+', payment_note)
    trf_id_match = re.search(r'(trf_[^ ]+)', payment_note)
    
    # Extract matched UTR and TRF ID
    utr = utr_match.group(0) if utr_match else None
    trf_id = trf_id_match.group(0) if trf_id_match else None
    
    found = True
    
    if utr is None:
        found = False
    
    return trf_id, utr, None, None, 'case1', found

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
    

    non_null_utr_matches = final_matches[final_matches['settlement_utr'] != '']
    # print(final_matches['settlement_utr'])
    if not non_null_utr_matches.empty:
        selected_match = non_null_utr_matches.iloc[0]
    else:
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
            trf_id, utr, value1, value2, case_flag, found = handle_case1(payment_note)
            if found:
                return trf_id, utr, None, None, case_flag
            else:
                file1_amount = row['Amount(₹)']
                return handle_case2(payment_mode, file2, file3, file1_amount)

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

# Extract trf_ or pay_ values from text
def extract_trf_or_pay(text):
    if pd.isna(text) or text == '':
        return None
    
    # First try to match trf_
    trf_match = re.search(r'trf_[a-zA-Z0-9]+', str(text))
    if trf_match:
        return trf_match.group(0)
    
    # If no trf_ found, try to match pay_
    pay_match = re.search(r'pay_[a-zA-Z0-9]+', str(text))
    if pay_match:
        return pay_match.group(0)
    
    return None

# Fill empty TRF IDs in file1
def fill_empty_trf_ids(file1):
    for idx, row in file1.iterrows():
        if row['trf_id'] == '-' or pd.isna(row['trf_id']):
            # Try Payment Note first
            payment_note = str(row.get('Payment Note', '')).strip()
            extracted_value = extract_trf_or_pay(payment_note)
            
            # If not found in Payment Note, try Payment mode
            if not extracted_value:
                payment_mode = str(row.get('Payment mode', '')).strip()
                extracted_value = extract_trf_or_pay(payment_mode)
            
            # Update the trf_id if a value was extracted
            if extracted_value:
                file1.at[idx, 'trf_id'] = extracted_value
    
    return file1

# Group file1 by specified columns
def group_file1_by_receipt(file1):
    groupby_columns = ['Receipt', 'Payer name', 'Payer type', 'Section / Department', 'trf_id', 'Payment date']
    
    # Group and sum Amount(₹)
    grouped_df = file1.groupby(groupby_columns, as_index=False).agg({
        'Amount(₹)': 'sum'
    })
    
    return grouped_df

def enrich_group_with_file6(group_df, file6, how='left'):
    """
    Join grouped_df with file6 on trf_id (group) vs entity_id/trf_id/id (file6),
    bring in amount and additional_utr, compute difference.
    """
    if group_df.empty:
        return group_df.assign(amount=None, UTIB=None, difference=None)
    # Determine entity id column in file6
    entity_col = next((c for c in ['entity_id', 'trf_id', 'id'] if c in file6.columns), None)
    if entity_col is None:
        raise ValueError("file6 must contain one of: entity_id, trf_id, id")
    needed_cols = [entity_col]
    for col in ['amount', 'additional_utr']:
        if col not in file6.columns:
            raise ValueError(f"file6 missing required column: {col}")
        needed_cols.append(col)
    subset = file6[needed_cols].rename(columns={
        entity_col: 'trf_id',
        'amount': 'amount',
        'additional_utr': 'UTIB'
    })
    merged = group_df.merge(subset, on='trf_id', how=how)
    merged['difference'] = merged['Amount(₹)'] - merged['amount']
    return merged