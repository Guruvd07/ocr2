PDF Text Extraction Comparison Tool

Overview

This project compares two PDF text extraction methods:
PyPDF2 (Python library)
PDF.js (JavaScript library)

The tool provides performance metrics (execution time, memory usage) and accuracy analysis for both methods, with OCR fallback capabilities for difficult-to-parse PDFs.

Features
Text extraction from PDF files using both PyPDF2 and PDF.js
Performance monitoring (time and memory usage)
Automatic OCR fallback when direct extraction fails
Comparison reports in PDF format
Streamlit-based web interface for PyPDF2
Standalone HTML interface for PDF.js
Support for complex PDFs (including menus with special characters)

Installation
Prerequisites
Python 3.7+

Node.js (for PDF.js web interface)

Tesseract OCR (for fallback functionality)


Python Requirements :

Install required Python packages:
pip install -r requirements.txt
The requirements.txt should contain:
streamlit==1.22.0
PyPDF2==3.0.1
fpdf2==2.7.4
pytesseract==0.3.10
pdf2image==1.16.3
pillow==10.0.0
psutil==5.9.5
requests==2.31.0


