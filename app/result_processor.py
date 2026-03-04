import pandas as pd
import re
import os

def process_payment_date_results(file1, file4):
    grouped = file1.groupby('Payment date', as_index=False)['Amount(₹)'].sum()
    grouped.rename(columns={'Amount(₹)': 'Subtotal'}, inplace=True)

    grouped['Value Date'] = None
    grouped['Account Number'] = None

    for idx, row in grouped.iterrows():
        subtotal = row['Subtotal']
        pay_date = pd.to_datetime(row['Payment date'], dayfirst=True, errors='coerce')
        matched_rows = file4[file4['Transaction Amount(INR)'] == subtotal]

        if not matched_rows.empty and pd.notna(pay_date):
            for _, match in matched_rows.iterrows():
                val_date = pd.to_datetime(match['Value Date'], dayfirst=True, errors='coerce')
                if pd.notna(val_date) and pay_date <= val_date and (val_date - pay_date).days <= 7:
                    grouped.at[idx, 'Value Date'] = match['Value Date']
                    grouped.at[idx, 'Account Number'] = match['Account Number']
                    break

    return grouped
