from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, send_file, Response
import os
import csv
import io
import sqlite3
from datetime import datetime
from pdf_generator import (
    generate_income_pdf, 
    generate_expenses_pdf, 
    generate_mileage_pdf, 
    generate_profit_loss_pdf, 
    generate_year_end_pdf
)

# Add these routes to app.py

@app.route('/export/income/pdf')
def export_income_pdf():
    """Export income data as PDF"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
    # Generate PDF
    pdf_path = generate_income_pdf(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        client_id=client_id
    )
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/export/expenses/pdf')
def export_expenses_pdf():
    """Export expenses data as PDF"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    vendor_id = request.args.get('vendor_id', '')
    tax_deductible = request.args.get('tax_deductible', '')
    
    # Generate PDF
    pdf_path = generate_expenses_pdf(
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        vendor_id=vendor_id,
        tax_deductible=tax_deductible
    )
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/export/mileage/pdf')
def export_mileage_pdf():
    """Export mileage data as PDF"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_id = request.args.get('vehicle_id', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
    # Generate PDF
    pdf_path = generate_mileage_pdf(
        start_date=start_date,
        end_date=end_date,
        vehicle_id=vehicle_id,
        category_id=category_id,
        client_id=client_id
    )
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/export/profit-loss/pdf')
def export_profit_loss_pdf():
    """Export profit and loss data as PDF"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Generate PDF
    pdf_path = generate_profit_loss_pdf(
        start_date=start_date,
        end_date=end_date
    )
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/export/year-end/pdf/<int:year>')
def export_year_end_pdf(year):
    """Export year-end summary as PDF"""
    # Generate PDF
    pdf_path = generate_year_end_pdf(year)
    
    # Return the PDF file
    return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))

@app.route('/export/all/<int:year>')
def export_all_year_data(year):
    """Export all data for a specific year as a zip file"""
    import zipfile
    from io import BytesIO
    
    # Date range for the year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Create a BytesIO object to store the zip file
    memory_file = BytesIO()
    
    # Create a zip file
    with zipfile.ZipFile(memory_file, 'w') as zf:
        # Generate and add PDF reports
        income_pdf = generate_income_pdf(start_date=start_date, end_date=end_date)
        expenses_pdf = generate_expenses_pdf(start_date=start_date, end_date=end_date)
        mileage_pdf = generate_mileage_pdf(start_date=start_date, end_date=end_date)
        profit_loss_pdf = generate_profit_loss_pdf(start_date=start_date, end_date=end_date)
        year_end_pdf = generate_year_end_pdf(year)
        
        zf.write(income_pdf, os.path.basename(income_pdf))
        zf.write(expenses_pdf, os.path.basename(expenses_pdf))
        zf.write(mileage_pdf, os.path.basename(mileage_pdf))
        zf.write(profit_loss_pdf, os.path.basename(profit_loss_pdf))
        zf.write(year_end_pdf, os.path.basename(year_end_pdf))
        
        # Generate and add CSV files
        conn = get_db()
        
        # Income CSV
        income_query = """
            SELECT i.date, i.description, c.name as category, ct.name as client, 
                   i.amount, p.name as payment_method, i.invoice_number, i.payment_status, i.notes
            FROM income i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN contacts ct ON i.client_id = ct.id
            LEFT JOIN payment_methods p ON i.payment_method_id = p.id
            WHERE i.date >= ? AND i.date <= ?
            ORDER BY i.date
        """
        cursor = conn.execute(income_query, [start_date, end_date])
        income = cursor.fetchall()
        
        income_csv = io.StringIO()
        income_writer = csv.writer(income_csv)
        income_writer.writerow(['Date', 'Description', 'Category', 'Client', 'Amount', 
                               'Payment Method', 'Invoice Number', 'Status', 'Notes'])
        
        for item in income:
            income_writer.writerow([
                item['date'],
                item['description'],
                item['category'] or 'Uncategorized',
                item['client'] or 'N/A',
                item['amount'],
                item['payment_method'] or 'N/A',
                item['invoice_number'] or '',
                item['payment_status'] or '',
                item['notes'] or ''
            ])
        
        zf.writestr(f"income_{year}.csv", income_csv.getvalue())
        
        # Expenses CSV
        expense_query = """
            SELECT e.date, e.description, c.name as category, ct.name as vendor, 
                   e.amount, p.name as payment_method, e.receipt_number, 
                   e.is_tax_deductible, e.is_reimbursable, e.is_reimbursed, e.notes
            FROM expenses e
            LEFT JOIN categories c ON e.category_id = c.id
            LEFT JOIN contacts ct ON e.vendor_id = ct.id
            LEFT JOIN payment_methods p ON e.payment_method_id = p.id
            WHERE e.date >= ? AND e.date <= ?
            ORDER BY e.date
        """
        cursor = conn.execute(expense_query, [start_date, end_date])
        expenses = cursor.fetchall()
        
        expense_csv = io.StringIO()
        expense_writer = csv.writer(expense_csv)
        expense_writer.writerow(['Date', 'Description', 'Category', 'Vendor', 'Amount', 
                                'Payment Method', 'Receipt Number', 'Tax Deductible', 
                                'Reimbursable', 'Reimbursed', 'Notes'])
        
        for item in expenses:
            expense_writer.writerow([
                item['date'],
                item['description'],
                item['category'] or 'Uncategorized',
                item['vendor'] or 'N/A',
                item['amount'],
                item['payment_method'] or 'N/A',
                item['receipt_number'] or '',
                'Yes' if item['is_tax_deductible'] else 'No',
                'Yes' if item['is_reimbursable'] else 'No',
                'Yes' if item['is_reimbursed'] else 'No',
                item['notes'] or ''
            ])
        
        zf.writestr(f"expenses_{year}.csv", expense_csv.getvalue())
        
        # Mileage CSV
        mileage_query = """
            SELECT m.date, v.name as vehicle, m.start_odometer, m.end_odometer, 
                   m.distance, m.purpose, c.name as category, ct.name as client, 
                   m.is_round_trip, m.notes
            FROM mileage m
            LEFT JOIN categories c ON m.category_id = c.id
            LEFT JOIN vehicles v ON m.vehicle_id = v.id
            LEFT JOIN contacts ct ON m.client_id = ct.id
            WHERE m.date >= ? AND m.date <= ?
            ORDER BY m.date
        """
        cursor = conn.execute(mileage_query, [start_date, end_date])
        mileage = cursor.fetchall()
        
        # Get current mileage rate
        cursor = conn.execute("SELECT * FROM mileage_rates WHERE year = ? ORDER BY effective_date DESC LIMIT 1", [year])
        mileage_rate = cursor.fetchone()
        
        if not mileage_rate:
            # If no rate for the year, get the most recent rate
            cursor = conn.execute("SELECT * FROM mileage_rates ORDER BY year DESC, effective_date DESC LIMIT 1")
            mileage_rate = cursor.fetchone()
        
        rate_per_mile = mileage_rate['rate_per_mile'] if mileage_rate else 0
        
        mileage_csv = io.StringIO()
        mileage_writer = csv.writer(mileage_csv)
        mileage_writer.writerow(['Date', 'Vehicle', 'Start Odometer', 'End Odometer', 
                                'Distance', 'Purpose', 'Category', 'Client', 'Round Trip', 
                                'Deduction Amount', 'Notes'])
        
        for item in mileage:
            deduction = item['distance'] * rate_per_mile
            mileage_writer.writerow([
                item['date'],
                item['vehicle'] or 'N/A',
                item['start_odometer'],
                item['end_odometer'],
                item['distance'],
                item['purpose'],
                item['category'] or 'Uncategorized',
                item['client'] or 'N/A',
                'Yes' if item['is_round_trip'] else 'No',
                f"{deduction:.2f}",
                item['notes'] or ''
            ])
        
        zf.writestr(f"mileage_{year}.csv", mileage_csv.getvalue())
    
    # Reset file pointer
    memory_file.seek(0)
    
    # Return the zip file
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'business_data_{year}.zip'
    )
