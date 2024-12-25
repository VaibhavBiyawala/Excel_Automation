from flask import Flask, request, render_template, redirect, url_for, send_file, session, flash
from data_loader import load_files
from processing import process_row, process_unmatched_rows
from result_processor import process_final_results, save_final_results
from utils import reorder_columns, save_output, concat_trans_his_files

import pandas as pd
import os
import re

app = Flask(__name__)
app.secret_key = '1234567890'
UPLOAD_FOLDER = ''
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Hardcoded credentials
USERNAME = 'admin'
PASSWORD = 'password'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('upload_files'))
        else:
            flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session variables
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    return render_template('upload.html')

@app.route('/results')
def results():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    file1 = session.get('file1', None)
    file2 = session.get('file2', None)
    pre_primary = session.get('pre_primary', None)
    primary = session.get('primary', None)
    non_zero_diff = session.get('non_zero_diff', None)
    return render_template('results.html', file1=file1, file2=file2, pre_primary=pre_primary, primary=primary, non_zero_diff=non_zero_diff)

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    file_path = os.path.join(filename)
    return send_file(file_path, as_attachment=True)

@app.route('/online_upload', methods=['GET', 'POST'])
def online_upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']
        file4 = request.files['file4']
        file5 = request.files['file5']

        file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
        file3_path = os.path.join(app.config['UPLOAD_FOLDER'], file3.filename)
        file4_path = os.path.join(app.config['UPLOAD_FOLDER'], file4.filename)
        file5_path = os.path.join(app.config['UPLOAD_FOLDER'], file5.filename)

        # Save the uploaded files
        file1.save(file1_path)
        file2.save(file2_path)
        file3.save(file3_path)
        file4.save(file4_path)
        file5.save(file5_path)
        
        concat_file = concat_trans_his_files(file4_path, file5_path)

        # Process the files
        d1_path, d2_path, pre_primary_path, primary_path, non_zero_diff_path = process_files(file1_path, file2_path, file3_path, concat_file)

        # Delete the uploaded files after processing
        os.remove(file1_path)
        os.remove(file2_path)
        os.remove(file3_path)
        os.remove(file4_path)
        os.remove(file5_path)
        os.remove(concat_file)

        # Store processed file paths in session for download
        session['file1'] = d1_path
        session['file2'] = d2_path
        session['pre_primary'] = pre_primary_path
        session['primary'] = primary_path
        session['non_zero_diff'] = non_zero_diff_path

        return redirect(url_for('results'))

    return render_template('online_upload.html')

@app.route('/cash_upload', methods=['GET', 'POST'])
def cash_upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        file_cash = request.files['fileCash']
        file_cash_path = os.path.join(app.config['UPLOAD_FOLDER'], file_cash.filename)

        # Save the uploaded file
        file_cash.save(file_cash_path)

        # Process the cash file
        pre_primary_path, primary_path = process_cash_file(file_cash_path)

        # Delete the uploaded file after processing
        os.remove(file_cash_path)

        # Clear online transaction session variables
        session.pop('file1', None)
        session.pop('file2', None)

        # Store processed file paths in session for download
        session['pre_primary'] = pre_primary_path
        session['primary'] = primary_path

        return redirect(url_for('results'))

    return render_template('cash_upload.html')

def extract_utr(description):
    match = re.search(r'(UTIBR|AXIS)[0-9A-Z]*', description)
    return match.group(0) if match else None

def process_files(file1_path, file2_path, file3_path, file4_path):
    file1, file2, file3, file4 = load_files(file1_path, file2_path, file3_path, file4_path)

    file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
        lambda row: pd.Series(process_row(row, file2, file3)),
        axis=1 )

    process_unmatched_rows(file1, file2, file3)
    file1.drop(columns=['case_flag'], inplace=True)
    file1 = reorder_columns(file1)

    # Extract UTR from file4 descriptions
    file4['Extracted UTR'] = file4['Description'].apply(extract_utr)


    # Add 'Account Number' column to file1 by matching UTR
    file1['Account Number'] = file1['UTR'].apply(lambda utr: file4[file4['Extracted UTR'] == utr]['Account Number'].values[0] if not file4[file4['Extracted UTR'] == utr].empty else None)    
    
    # Add 'Name Valid Transaction' column based on conditions
    def validate_transaction(row):
        collection = row['Collection']
        account_number = row['Account Number']
        
        if pd.isna(collection) or pd.isna(account_number):
            return 'missing / improper data'
        
        if 'extra' in collection.lower() and account_number != 5205010739:
            return False
        if 'fee' in collection.lower() and account_number != 5205009403:
            return False
        
        return None


    file1['Valid Transaction'] = file1.apply(validate_transaction, axis=1)

    d1_path = save_output(file1)

    grouped_results = process_final_results(file1, file4)
    
    d2_path = save_final_results(grouped_results)
    
    # Filter entries from file1 where the UTR associated with difference is non-zero in grouped_results
    non_zero_diff_utr = grouped_results[grouped_results['Difference'] != 0]['UTR']
    non_zero_diff_entries = file1[file1['UTR'].isin(non_zero_diff_utr)]

    # Save the filtered data to a new Excel file
    non_zero_diff_path = d1_path.replace('.xlsx', '_non_zero_diff.xlsx')
    non_zero_diff_entries.to_excel(non_zero_diff_path, index=False)
    
    zero_diff_utr = grouped_results[grouped_results['Difference'] == 0]['UTR']
    zero_diff_entries = file1[file1['UTR'].isin(zero_diff_utr)]
    zero_diff_entries_path = d1_path.replace('.xlsx', '_zero_diff.xlsx')
    zero_diff_entries.to_excel(zero_diff_entries_path, index=False)
    pre_primary_path, primary_path = filter_section(zero_diff_entries_path)       
    
    return d1_path, d2_path, pre_primary_path, primary_path, non_zero_diff_path
    
def filter_section(file_cash_path):
    # read the excel file
    file_cash = pd.read_excel(file_cash_path)

    # Filter pre-primary and primary sections
    pre_primary_sections = ['N -', 'U K G -', 'L K G -']
    primary_sections = ['C1 -', 'C2 -', 'C3 -', 'C4 -', 'C5 -', 'C6 -', 'C7 -', 'C8 -']
    
    # Ensure the 'Section / Department' column is treated as string
    file_cash['Section / Department'] = file_cash['Section / Department'].astype(str)
    
    # Filter pre-primary and primary sections
    pre_primary_df = file_cash[file_cash['Section / Department'].apply(lambda x: any(x.startswith(prefix) for prefix in pre_primary_sections))]
    primary_df = file_cash[file_cash['Section / Department'].apply(lambda x: any(x.startswith(prefix) for prefix in primary_sections))]

    # Save the filtered data to new Excel files
    pre_primary_path = file_cash_path.replace('.xlsx', '_pre_primary.xlsx')
    primary_path = file_cash_path.replace('.xlsx', '_primary.xlsx')
    pre_primary_df.to_excel(pre_primary_path, index=False)
    primary_df.to_excel(primary_path, index=False)

    return pre_primary_path, primary_path

def process_cash_file(file_cash_path, skip_row = True):
    if skip_row:
        file_cash = pd.read_csv(file_cash_path, skiprows=4)
    else:
        file_cash = pd.read_csv(file_cash_path)

    # Filter pre-primary and primary sections
    pre_primary_sections = ['N -', 'U K G -', 'L K G -']
    primary_sections = ['C1 -', 'C2 -', 'C3 -', 'C4 -', 'C5 -', 'C6 -', 'C7 -', 'C8 -']
    
    # Ensure the 'Section / Department' column is treated as string
    file_cash['Section / Department'] = file_cash['Section / Department'].astype(str)
    
    # Filter pre-primary and primary sections
    pre_primary_df = file_cash[file_cash['Section / Department'].apply(lambda x: any(x.startswith(prefix) for prefix in pre_primary_sections))]
    primary_df = file_cash[file_cash['Section / Department'].apply(lambda x: any(x.startswith(prefix) for prefix in primary_sections))]

    pre_primary_path = file_cash_path.replace('.csv', '_pre_primary.csv')
    primary_path = file_cash_path.replace('.csv', '_primary.csv')
    pre_primary_df.to_csv(pre_primary_path, index=False)
    primary_df.to_csv(primary_path, index=False)

    return pre_primary_path, primary_path

if __name__ == "__main__":
    app.run(debug=False)