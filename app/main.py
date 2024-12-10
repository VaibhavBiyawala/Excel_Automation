from data_loader import load_files
from processing import process_row, process_unmatched_rows
from utils import reorder_columns, save_output

import pandas as pd

def main():
    # Load files
    file1 = '13150114648874_fee_reciept.csv'
    file2 = 'Transfer Nov 2024.xlsx'
    file3 = 'Combine November 2024.xlsx'
    file1, file2, file3 = load_files(file1, file2, file3)

    # Initial processing for Case 1 and Case 2
    file1[['trf_id', 'UTR', 'Rozarpay', 'difference', 'case_flag']] = file1.apply(
        lambda row: pd.Series(process_row(row, file2, file3)),
        axis=1
    )

    # Further processing for unmatched rows
    process_unmatched_rows(file1, file2, file3)

    # Remove unnecessary columns and reorder
    file1.drop(columns=['case_flag'], inplace=True)
    file1 = reorder_columns(file1)

    # Save the final output
    save_output(file1)

if __name__ == "__main__":
    main()
