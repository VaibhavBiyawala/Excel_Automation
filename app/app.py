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
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']
        file4 = request.files['file4']
        file5 = request.files['file5']

        file1_path = file1.filename
        file2_path = file2.filename
        file3_path = file3.filename
        file4_path = file4.filename
        file5_path = file5.filename

        # Save the uploaded files
        file1.save(file1_path)
        file2.save(file2_path)
        file3.save(file3_path)
        file4.save(file4_path)
        file5.save(file5_path)
        
        concat_file = concat_trans_his_files(file4_path, file5_path)

        # Process the files
        d1_path, d2_path = process_files(file1_path, file2_path, file3_path, concat_file)

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

        return redirect(url_for('results'))

    return render_template('upload.html')

@app.route('/results')
def results():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    file1 = session.get('file1', None)
    file2 = session.get('file2', None)
    return render_template('results.html', file1=file1, file2=file2)

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    file_path = os.path.join(filename)
    return send_file(file_path, as_attachment=True)

def extract_utr(description):
    match = re.search(r'(UTIBR|AXIS)[0-9A-Z]*', description)
    return match.group(0) if match else None

def process_files(file1_path, file2_path, file3_path, file4_path):
    file1, file2, file3, file4 = load_files(file1_path, file2_path, file3_path, file4_path)

    file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
        lambda row: pd.Series(process_row(row, file2, file3)),
        axis=1
    )

    process_unmatched_rows(file1, file2, file3)
    file1.drop(columns=['case_flag'], inplace=True)
    file1 = reorder_columns(file1)

    # Extract UTR from file4 descriptions
    file4['Extracted UTR'] = file4['Description'].apply(extract_utr)


    # Add 'Account Number' column to file1 by matching UTR
    file1['Account Number'] = file1['UTR'].apply(lambda utr: file4[file4['Extracted UTR'] == utr]['Account Number'].values[0] if not file4[file4['Extracted UTR'] == utr].empty else None)
    file1['Account Number'] = file1['Account Number'].astype("string")
    
    print(file1.columns)

    # Reorder columns to ensure 'Account Number' is included
    # file1 = reorder_columns(file1)

    print(file1.columns)

    d1_path = save_output(file1)
    
    print(file1.columns)
    
    grouped_results = process_final_results(file1, file4)
    d2_path = save_final_results(grouped_results)
    
    return d1_path, d2_path


if __name__ == "__main__":
    app.run(debug=True)