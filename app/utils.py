import os

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
def save_output(file1, filename='result_file_4.xlsx'):
    filepath = os.path.join('..', 'output', filename)
    file1.to_excel(filepath, index=False)
    print(f"Processing complete. File saved as {filename}")
