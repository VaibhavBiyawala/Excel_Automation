# Excel Automation Web Application

A Flask-based web application for automating Excel file processing and transaction reconciliation. This application processes payment data, matches transactions across multiple sources, and generates detailed reports.

## Features

- **Secure Login System**: Basic authentication with hardcoded credentials
- **File Upload & Processing**: Support for multiple file formats (CSV, Excel)
- **Transaction Matching**: Automated matching of payments using UTR and TRF ID
- **Data Reconciliation**: Compare transaction amounts and identify discrepancies
- **Report Generation**: Generate filtered reports for different sections (Pre-primary, Primary)
- **Download Results**: Download processed files and reports

## File Structure

```
Excel_Automation/
├── app/
│   ├── app.py                 # Main Flask application
│   ├── data_loader.py         # File loading utilities
│   ├── processing.py          # Transaction processing logic
│   ├── result_processor.py    # Result processing and grouping
│   ├── utils.py              # Utility functions
│   ├── requirements.txt      # Python dependencies
│   └── templates/            # HTML templates
│       ├── login.html
│       ├── upload.html
│       ├── online_upload.html
│       ├── cash_upload.html
│       └── results.html
|       └── header.html
|       └── footer.html
└── README.md
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Excel_Automation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r app/requirements.txt
   ```

3. **Run the application**:
   ```bash
   cd app
   python app.py
   ```

4. **Access the application**:
   Open your browser and navigate to `http://localhost:5000`

## Dependencies

- Flask - Web framework
- pandas - Data manipulation and analysis
- numpy - Numerical computing
- xlrd - Reading Excel files
- openpyxl - Writing Excel files

## Usage

### Login
- Username: `admin`
- Password: `password`

### Processing Types

#### 1. Online Transaction Processing
Upload 5 files:
- **File 1**: Payment data (CSV format)
- **File 2**: Transaction records (Excel)
- **File 3**: Order data (Excel)
- **File 4**: Transaction history (Excel)
- **File 5**: Additional transaction history (Excel)

#### 2. Cash Transaction Processing
Upload 1 file:
- **Cash File**: Payment data (CSV format)

### File Processing Logic

The application performs the following operations:

1. **Data Loading**: Loads and standardizes column names across files
2. **Transaction Matching**: 
   - Case 1: Extract UTR and TRF ID from payment notes
   - Case 2: Match using payment mode and cross-reference with other files
3. **UTR Extraction**: Uses regex to extract UTR numbers from descriptions
4. **Account Validation**: Validates transactions based on collection type and account numbers
5. **Report Generation**: Creates filtered reports and identifies discrepancies

### Output Files

The application generates several output files:

- `result_file_all.xlsx` - Complete processed data
- `grouped_results.xlsx` - Grouped transaction summary
- `*_non_zero_diff.xlsx` - Transactions with discrepancies
- `*_zero_diff.xlsx` - Matching transactions
- `*_pre_primary.xlsx` - Pre-primary section data
- `*_primary.xlsx` - Primary section data

## Key Features

### UTR Extraction
Automatically extracts UTR (Unique Transaction Reference) numbers from payment descriptions using regex patterns for UTIBR and AXIS bank formats.

### Transaction Validation
Validates transactions based on:
- Collection type (extra fees, regular fees)
- Account number verification
- Amount reconciliation

### Section Filtering
Automatically filters data into educational sections:
- **Pre-primary**: N -, U K G -, L K G -
- **Primary**: C1 - through C8 -

### Error Handling
- Missing or improper data identification
- Unmatched transaction tracking
- Data validation and integrity checks

## Configuration

### Account Numbers
The application uses specific account numbers for validation:
- Extra fees account: `5205010739`
- Regular fees account: `5205009403`

### File Formats
- **CSV files**: Should have data starting from row 5 (skiprows=4)
- **Excel files**: Standard format with headers

## Security Notes

⚠️ **Important**: This application uses hardcoded credentials for demonstration purposes. In a production environment, implement proper authentication and security measures.

## Troubleshooting

### Common Issues

1. **File Upload Errors**:
   - Ensure files are in the correct format (CSV/Excel)
   - Check file permissions and size limits

2. **Processing Errors**:
   - Verify column names match expected format
   - Check for missing data in required fields

3. **UTR Matching Issues**:
   - Ensure UTR formats match regex patterns
   - Check for special characters in descriptions

### Debug Mode

To enable debug mode, change the last line in `app.py`:
```python
app.run(debug=True)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for internal use and automation purposes.

## Support

For issues or questions, please contact the development team or create an issue in the repository.