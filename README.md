# Invoice Generator

A desktop invoice generator built with Python and Tkinter for small businesses and freelancers. The app creates branded PDF invoices, keeps a CSV invoice log, and exports a formatted Excel invoice with formulas.

## Features

- Desktop GUI built with Tkinter
- Branded PDF invoice generation
- Automatic invoice numbering
- Customer and company details
- BSB, bank account name, and account number support
- Item-level discount as a percentage
- Invoice-level discount as a fixed dollar amount
- GST calculation
- Due date and payment status
- Invoice notes
- CSV export for invoice logging
- Excel export with formulas and formatting
- Safe fallback when Excel export fails

## Tech Stack

- Python
- Tkinter
- ReportLab
- OpenPyXL
- Pillow

## Installation

```bash
python3 -m pip install -r requirements.txt
python3 invoice_generator.py
```

## Output

Generated files are saved under:

```text
invoice_data/
├── pdf/
├── csv/
├── excel/
└── config/
```

## Portfolio Description

This project demonstrates:
- desktop application development in Python
- GUI design with Tkinter
- PDF document generation
- Excel automation
- data export workflows
- defensive error handling for real-world compatibility issues
