from flask import Flask, request, render_template, redirect, url_for, send_file, session, flash
from data_loader import load_files
from processing import process_row, process_unmatched_rows
from result_processor import process_payment_date_results
from utils import reorder_columns, save_output, load_trans_his_files

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
    grouped_results_non_ecd = session.get('grouped_results_non_ecd', None)
    grouped_results_ecd = session.get('grouped_results_ecd', None)
    non_zero_diff = session.get('non_zero_diff', None)
    return render_template('results.html', file1=file1, file2=file2, grouped_results_non_ecd=grouped_results_non_ecd, grouped_results_ecd=grouped_results_ecd, non_zero_diff=non_zero_diff)

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
        
        file4_df = load_trans_his_files(file4_path)
        file5_df = load_trans_his_files(file5_path)

        # Process the files
        d1_path, d2_path, grouped_results_ecd, grouped_results_non_ecd = process_files(file1_path, file2_path, file3_path, file4_df, file5_df)

        # Delete the uploaded files after processing
        os.remove(file1_path)
        os.remove(file2_path)
        os.remove(file3_path)
        os.remove(file4_path)
        os.remove(file5_path)

        # Store processed file paths in session for download
        session['file1'] = d1_path
        session['file2'] = d2_path
        session['grouped_results_ecd'] = grouped_results_ecd
        session['grouped_results_non_ecd'] = grouped_results_non_ecd

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
    match = re.search(r'(UTIB|AXIS)[0-9A-Z]*', description)
    return match.group(0) if match else None

def process_files(file1_path, file2_path, file3_path, file4, file5):
    file1, file2, file3 = load_files(file1_path, file2_path, file3_path)

    file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
        lambda row: pd.Series(process_row(row, file2, file3)),
        axis=1 )

    process_unmatched_rows(file1, file2, file3)
    file1.drop(columns=['case_flag'], inplace=True)
    file1 = reorder_columns(file1)    

    # Split file1 into ECD and non-ECD based on 'Receipt' column
    df1 = file1[file1['Receipt'].str.startswith('ECD/', na=False)]
    d1_path = save_output(df1, filename='result_file_ecd.xlsx')
    df2 = file1[~file1.index.isin(df1.index)]
    d2_path = save_output(df2, filename='result_file_non_ecd.xlsx')

    # Process payment date results for both ECD and non-ECD files
    grouped_results_ecd = process_payment_date_results(df1, file4)
    grouped_results_ecd_path = save_output(grouped_results_ecd, filename='grouped_results_ecd.xlsx')
    
    grouped_results_non_ecd = process_payment_date_results(df2, file5)
    grouped_results_non_ecd_path = save_output(grouped_results_non_ecd, filename='grouped_results_non_ecd.xlsx')
    
    return d1_path, d2_path, grouped_results_ecd_path, grouped_results_non_ecd_path
    
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