# AWS Billing Report Generator

Python project that uses **Boto3 and AWS Cost Explorer API** to retrieve AWS billing information and generate a PDF report.

## Features

* Select billing start and end dates
* Display total AWS cost
* Display service-wise costs
* Display daily costs
* Display currency
* Generate PDF billing report
* Uses standard AWS credentials — no hardcoded keys

## Technologies

* Python
* Boto3
* AWS Cost Explorer
* ReportLab

## Installation

```bash
pip install -r requirements.txt
```

Configure AWS credentials:

```bash
aws configure
```

Run the program:

```bash
python aws_billing_report.py
```

## Project Structure

```text
AWS-Billing-Report/
├── aws_billing_report.py
├── requirements.txt
├── README.md
└── .gitignore
```

> **Note:** AWS credentials and generated PDF reports are excluded from Git using `.gitignore`.
