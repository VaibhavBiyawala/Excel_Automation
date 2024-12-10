from flask import Flask, request, render_template, redirect, url_for, send_file, session
from data_loader import load_files
from processing import process_row, process_unmatched_rows
from result_processor import process_final_results, save_final_results
from utils import reorder_columns, save_output, concat_trans_his_files

import pandas as pd
import os

app = Flask(__name__)
app.secret_key = '1234567890'
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def upload_files():
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
    file1 = session.get('file1', None)
    file2 = session.get('file2', None)
    return render_template('results.html', file1=file1, file2=file2)

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(filename)
    return send_file(file_path, as_attachment=True)

def process_files(file1_path, file2_path, file3_path, file4_path):
    file1, file2, file3, file4 = load_files(file1_path, file2_path, file3_path, file4_path)

    file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
        lambda row: pd.Series(process_row(row, file2, file3)),
        axis=1
    )

    process_unmatched_rows(file1, file2, file3)
    file1.drop(columns=['case_flag'], inplace=True)
    file1 = reorder_columns(file1)

    d1_path = save_output(file1)
    grouped_results = process_final_results(file1, file4)
    d2_path = save_final_results(grouped_results)
    
    return d1_path, d2_path


if __name__ == "__main__":
    app.run(debug=False)
