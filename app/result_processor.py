import pandas as pd
import re
import os

def process_final_results(file1, file4):
    grouped = file1.groupby('UTIB', as_index=False)['Amount(₹)'].sum()
    grouped.rename(columns={'Amount(₹)': 'Subtotal'}, inplace=True)

    grouped['Transaction Amount(INR)'] = None
    grouped['Difference'] = None
    grouped['Value Date'] = None
    grouped['Account Number'] = None  # Add Account Number column

    for idx, row in grouped.iterrows():
        utr = row['UTIB']
        # Match UTIB with the Description column in File 4
        matched_row = file4[file4['Description'].str.contains(utr, na=False, regex=True)]

        if not matched_row.empty:
            # Get the Transaction Amount, Value Date, and Account Number from the first match
            transaction_amount = matched_row.iloc[0]['Transaction Amount(INR)']
            value_date = matched_row.iloc[0]['Value Date']
            account_number = matched_row.iloc[0]['Account Number']
            grouped.at[idx, 'Transaction Amount(INR)'] = transaction_amount
            grouped.at[idx, 'Difference'] = row['Subtotal'] - transaction_amount
            grouped.at[idx, 'Value Date'] = value_date
            grouped.at[idx, 'Account Number'] = account_number  # Set Account Number
        else:
            # If no match found, mark as NaN
            grouped.at[idx, 'Transaction Amount(INR)'] = None
            grouped.at[idx, 'Difference'] = None
            grouped.at[idx, 'Value Date'] = None
            grouped.at[idx, 'Account Number'] = None  # Set Account Number as NaN

    return grouped

def save_final_results(grouped, filename='grouped_results.xlsx'):
    filepath = filename
    grouped.to_excel(filepath, index=False)
    return filepath
