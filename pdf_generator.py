import os
import csv
import io
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect('data/business_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_income_pdf(start_date=None, end_date=None, category_id=None, client_id=None, output_path=None):
    """Generate a PDF report for income transactions"""
    if output_path is None:
        # Generate default filename if not provided
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"data/exports/income_report_{timestamp}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Connect to database
    conn = get_db_connection()
    
    # Build query
    query = """
        SELECT i.*, c.name as category_name, ct.name as client_name, p.name as payment_method_name
        FROM income i
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN contacts ct ON i.client_id = ct.id
        LEFT JOIN payment_methods p ON i.payment_method_id = p.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND i.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND i.date <= ?"
        params.append(end_date)
    
    if category_id:
        query += " AND i.category_id = ?"
        params.append(category_id)
    
    if client_id:
        query += " AND i.client_id = ?"
        params.append(client_id)
    
    query += " ORDER BY i.date"
    
    # Execute query
    cursor = conn.execute(query, params)
    income = cursor.fetchall()
    
    # Calculate total
    total_amount = sum(row['amount'] for row in income)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Add title
    title = "Income Report"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"
    elif start_date:
        title += f" (From {start_date})"
    elif end_date:
        title += f" (Until {end_date})"
    
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add summary
    content.append(Paragraph(f"Total Income: ${total_amount:.2f}", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add date and time of report generation
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Create table data
    table_data = [
        ['Date', 'Description', 'Category', 'Client', 'Amount', 'Payment Method', 'Status', 'Notes']
    ]
    
    for item in income:
        table_data.append([
            item['date'],
            item['description'],
            item['category_name'] or 'Uncategorized',
            item['client_name'] or 'N/A',
            f"${item['amount']:.2f}",
            item['payment_method_name'] or 'N/A',
            item['payment_status'],
            item['notes'] or ''
        ])
    
    # Add total row
    table_data.append(['', '', '', 'TOTAL', f"${total_amount:.2f}", '', '', ''])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Add alternating row colors
    for i in range(1, len(table_data) - 1):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    # Close connection
    conn.close()
    
    return output_path

def generate_expenses_pdf(start_date=None, end_date=None, category_id=None, vendor_id=None, tax_deductible=None, output_path=None):
    """Generate a PDF report for expense transactions"""
    if output_path is None:
        # Generate default filename if not provided
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"data/exports/expenses_report_{timestamp}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Connect to database
    conn = get_db_connection()
    
    # Build query
    query = """
        SELECT e.*, c.name as category_name, ct.name as vendor_name, p.name as payment_method_name
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN contacts ct ON e.vendor_id = ct.id
        LEFT JOIN payment_methods p ON e.payment_method_id = p.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)
    
    if category_id:
        query += " AND e.category_id = ?"
        params.append(category_id)
    
    if vendor_id:
        query += " AND e.vendor_id = ?"
        params.append(vendor_id)
    
    if tax_deductible == '1':
        query += " AND e.is_tax_deductible = 1"
    
    query += " ORDER BY e.date"
    
    # Execute query
    cursor = conn.execute(query, params)
    expenses = cursor.fetchall()
    
    # Calculate total
    total_amount = sum(row['amount'] for row in expenses)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Add title
    title = "Expense Report"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"
    elif start_date:
        title += f" (From {start_date})"
    elif end_date:
        title += f" (Until {end_date})"
    
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add summary
    content.append(Paragraph(f"Total Expenses: ${total_amount:.2f}", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add date and time of report generation
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Create table data
    table_data = [
        ['Date', 'Description', 'Category', 'Vendor', 'Amount', 'Payment Method', 'Tax Deductible', 'Notes']
    ]
    
    for item in expenses:
        table_data.append([
            item['date'],
            item['description'],
            item['category_name'] or 'Uncategorized',
            item['vendor_name'] or 'N/A',
            f"${item['amount']:.2f}",
            item['payment_method_name'] or 'N/A',
            'Yes' if item['is_tax_deductible'] else 'No',
            item['notes'] or ''
        ])
    
    # Add total row
    table_data.append(['', '', '', 'TOTAL', f"${total_amount:.2f}", '', '', ''])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Add alternating row colors
    for i in range(1, len(table_data) - 1):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    # Close connection
    conn.close()
    
    return output_path

def generate_mileage_pdf(start_date=None, end_date=None, vehicle_id=None, category_id=None, client_id=None, output_path=None):
    """Generate a PDF report for mileage entries"""
    if output_path is None:
        # Generate default filename if not provided
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"data/exports/mileage_report_{timestamp}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Connect to database
    conn = get_db_connection()
    
    # Build query
    query = """
        SELECT m.*, c.name as category_name, v.name as vehicle_name, ct.name as client_name
        FROM mileage m
        LEFT JOIN categories c ON m.category_id = c.id
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        LEFT JOIN contacts ct ON m.client_id = ct.id
        WHERE 1=1
    """
    params = []
    
    if start_date:
        query += " AND m.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND m.date <= ?"
        params.append(end_date)
    
    if vehicle_id:
        query += " AND m.vehicle_id = ?"
        params.append(vehicle_id)
    
    if category_id:
        query += " AND m.category_id = ?"
        params.append(category_id)
    
    if client_id:
        query += " AND m.client_id = ?"
        params.append(client_id)
    
    query += " ORDER BY m.date"
    
    # Execute query
    cursor = conn.execute(query, params)
    mileage = cursor.fetchall()
    
    # Calculate total distance
    total_distance = sum(row['distance'] for row in mileage)
    
    # Get current mileage rate
    current_year = datetime.now().year
    cursor = conn.execute(
        "SELECT * FROM mileage_rates WHERE year = ? ORDER BY effective_date DESC LIMIT 1", 
        [current_year]
    )
    mileage_rate = cursor.fetchone()
    
    if not mileage_rate:
        # If no rate for current year, get the most recent rate
        cursor = conn.execute("SELECT * FROM mileage_rates ORDER BY year DESC, effective_date DESC LIMIT 1")
        mileage_rate = cursor.fetchone()
    
    # Calculate deduction
    rate_per_mile = mileage_rate['rate_per_mile'] if mileage_rate else 0
    deduction_amount = total_distance * rate_per_mile
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Add title
    title = "Mileage Report"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"
    elif start_date:
        title += f" (From {start_date})"
    elif end_date:
        title += f" (Until {end_date})"
    
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add summary
    content.append(Paragraph(f"Total Distance: {total_distance:.1f} miles", subtitle_style))
    content.append(Paragraph(f"IRS Rate: ${rate_per_mile:.3f}/mile", normal_style))
    content.append(Paragraph(f"Deduction Amount: ${deduction_amount:.2f}", subtitle_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add date and time of report generation
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Create table data
    table_data = [
        ['Date', 'Vehicle', 'Purpose', 'Start', 'End', 'Distance', 'Category', 'Client', 'Deduction']
    ]
    
    for item in mileage:
        item_deduction = item['distance'] * rate_per_mile
        table_data.append([
            item['date'],
            item['vehicle_name'] or 'N/A',
            item['purpose'],
            f"{item['start_odometer']:.1f}",
            f"{item['end_odometer']:.1f}",
            f"{item['distance']:.1f} miles",
            item['category_name'] or 'Uncategorized',
            item['client_name'] or 'N/A',
            f"${item_deduction:.2f}"
        ])
    
    # Add total row
    table_data.append(['', '', '', '', 'TOTAL', f"{total_distance:.1f} miles", '', '', f"${deduction_amount:.2f}"])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    
    # Style the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
        ('ALIGN', (8, 1), (8, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Add alternating row colors
    for i in range(1, len(table_data) - 1):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(table_style)
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    # Close connection
    conn.close()
    
    return output_path

def generate_profit_loss_pdf(start_date=None, end_date=None, output_path=None):
    """Generate a PDF report for profit and loss"""
    if output_path is None:
        # Generate default filename if not provided
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"data/exports/profit_loss_report_{timestamp}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Connect to database
    conn = get_db_connection()
    
    # Build queries
    income_query = "SELECT SUM(amount) as total FROM income WHERE 1=1"
    expense_query = "SELECT SUM(amount) as total FROM expenses WHERE 1=1"
    
    income_params = []
    expense_params = []
    
    if start_date:
        income_query += " AND date >= ?"
        expense_query += " AND date >= ?"
        income_params.append(start_date)
        expense_params.append(start_date)
    
    if end_date:
        income_query += " AND date <= ?"
        expense_query += " AND date <= ?"
        income_params.append(end_date)
        expense_params.append(end_date)
    
    # Execute queries
    cursor = conn.execute(income_query, income_params)
    income_total = cursor.fetchone()
    
    cursor = conn.execute(expense_query, expense_params)
    expense_total = cursor.fetchone()
    
    # Calculate profit/loss
    income_amount = income_total['total'] if income_total['total'] else 0
    expense_amount = expense_total['total'] if expense_total['total'] else 0
    profit_loss = income_amount - expense_amount
    
    # Get income by category
    income_by_category_query = """
        SELECT c.name, SUM(i.amount) as total
        FROM income i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE 1=1
    """
    
    if start_date:
        income_by_category_query += " AND i.date >= ?"
    
    if end_date:
        income_by_category_query += " AND i.date <= ?"
    
    income_by_category_query += " GROUP BY c.name ORDER BY total DESC"
    
    cursor = conn.execute(income_by_category_query, income_params)
    income_by_category = cursor.fetchall()
    
    # Get expenses by category
    expense_by_category_query = """
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    
    if start_date:
        expense_by_category_query += " AND e.date >= ?"
    
    if end_date:
        expense_by_category_query += " AND e.date <= ?"
    
    expense_by_category_query += " GROUP BY c.name ORDER BY total DESC"
    
    cursor = conn.execute(expense_by_category_query, expense_params)
    expense_by_category = cursor.fetchall()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Add title
    title = "Profit & Loss Report"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"
    elif start_date:
        title += f" (From {start_date})"
    elif end_date:
        title += f" (Until {end_date})"
    
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add summary
    content.append(Paragraph("Summary", subtitle_style))
    
    summary_data = [
        ['Income', f"${income_amount:.2f}"],
        ['Expenses', f"${expense_amount:.2f}"],
        ['Profit/Loss', f"${profit_loss:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
    
    summary_style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue if profit_loss >= 0 else colors.lightcoral),
    ])
    
    summary_table.setStyle(summary_style)
    content.append(summary_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add date and time of report generation
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add income by category
    content.append(Paragraph("Income by Category", subtitle_style))
    
    if income_by_category:
        income_cat_data = [['Category', 'Amount', 'Percentage']]
        
        for item in income_by_category:
            category_name = item['name'] or 'Uncategorized'
            amount = item['total']
            percentage = (amount / income_amount * 100) if income_amount else 0
            
            income_cat_data.append([
                category_name,
                f"${amount:.2f}",
                f"{percentage:.1f}%"
            ])
        
        income_cat_table = Table(income_cat_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        income_cat_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add alternating row colors
        for i in range(1, len(income_cat_data)):
            if i % 2 == 0:
                income_cat_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        income_cat_table.setStyle(income_cat_style)
        content.append(income_cat_table)
    else:
        content.append(Paragraph("No income data available", normal_style))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add expenses by category
    content.append(Paragraph("Expenses by Category", subtitle_style))
    
    if expense_by_category:
        expense_cat_data = [['Category', 'Amount', 'Percentage']]
        
        for item in expense_by_category:
            category_name = item['name'] or 'Uncategorized'
            amount = item['total']
            percentage = (amount / expense_amount * 100) if expense_amount else 0
            
            expense_cat_data.append([
                category_name,
                f"${amount:.2f}",
                f"{percentage:.1f}%"
            ])
        
        expense_cat_table = Table(expense_cat_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        expense_cat_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add alternating row colors
        for i in range(1, len(expense_cat_data)):
            if i % 2 == 0:
                expense_cat_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        expense_cat_table.setStyle(expense_cat_style)
        content.append(expense_cat_table)
    else:
        content.append(Paragraph("No expense data available", normal_style))
    
    # Build PDF
    doc.build(content)
    
    # Close connection
    conn.close()
    
    return output_path

def generate_year_end_pdf(year, output_path=None):
    """Generate a year-end summary PDF report"""
    if output_path is None:
        # Generate default filename if not provided
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"data/exports/year_end_report_{year}_{timestamp}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Date range for the year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    # Connect to database
    conn = get_db_connection()
    
    # Get income data
    cursor = conn.execute("""
        SELECT SUM(amount) as total FROM income 
        WHERE date >= ? AND date <= ?
    """, [start_date, end_date])
    income_total_row = cursor.fetchone()
    income_total = income_total_row['total'] if income_total_row['total'] else 0
    
    # Get expense data
    cursor = conn.execute("""
        SELECT SUM(amount) as total FROM expenses 
        WHERE date >= ? AND date <= ?
    """, [start_date, end_date])
    expense_total_row = cursor.fetchone()
    expense_total = expense_total_row['total'] if expense_total_row['total'] else 0
    
    # Get mileage data
    cursor = conn.execute("""
        SELECT SUM(distance) as total FROM mileage 
        WHERE date >= ? AND date <= ?
    """, [start_date, end_date])
    mileage_total_row = cursor.fetchone()
    mileage_total = mileage_total_row['total'] if mileage_total_row['total'] else 0
    
    # Get mileage rate for the year
    cursor = conn.execute("""
        SELECT * FROM mileage_rates 
        WHERE year = ? 
        ORDER BY effective_date DESC LIMIT 1
    """, [year])
    mileage_rate = cursor.fetchone()
    
    if not mileage_rate:
        # If no rate for the year, get the most recent rate
        cursor = conn.execute("""
            SELECT * FROM mileage_rates 
            ORDER BY year DESC, effective_date DESC LIMIT 1
        """)
        mileage_rate = cursor.fetchone()
    
    # Calculate mileage deduction
    rate_per_mile = mileage_rate['rate_per_mile'] if mileage_rate else 0
    mileage_deduction = mileage_total * rate_per_mile
    
    # Calculate profit/loss
    profit_loss = income_total - expense_total - mileage_deduction
    
    # Get income by category
    cursor = conn.execute("""
        SELECT c.name, SUM(i.amount) as total
        FROM income i
        LEFT JOIN categories c ON i.category_id = c.id
        WHERE i.date >= ? AND i.date <= ?
        GROUP BY c.name
        ORDER BY total DESC
    """, [start_date, end_date])
    income_by_category = cursor.fetchall()
    
    # Get expenses by category
    cursor = conn.execute("""
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.date >= ? AND e.date <= ?
        GROUP BY c.name
        ORDER BY total DESC
    """, [start_date, end_date])
    expense_by_category = cursor.fetchall()
    
    # Get tax deductible expenses
    cursor = conn.execute("""
        SELECT SUM(e.amount) as total
        FROM expenses e
        WHERE e.date >= ? AND e.date <= ? AND e.is_tax_deductible = 1
    """, [start_date, end_date])
    tax_deductible_row = cursor.fetchone()
    tax_deductible_total = tax_deductible_row['total'] if tax_deductible_row['total'] else 0
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    subsubtitle_style = styles['Heading3']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Add title
    content.append(Paragraph(f"Year-End Summary Report {year}", title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add date and time of report generation
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add summary section
    content.append(Paragraph("Financial Summary", subtitle_style))
    
    summary_data = [
        ['Income', f"${income_total:.2f}"],
        ['Expenses', f"${expense_total:.2f}"],
        ['Mileage Deduction', f"${mileage_deduction:.2f}"],
        ['Profit/Loss', f"${profit_loss:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    
    summary_style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue if profit_loss >= 0 else colors.lightcoral),
    ])
    
    summary_table.setStyle(summary_style)
    content.append(summary_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add income section
    content.append(Paragraph("Income", subtitle_style))
    
    if income_by_category:
        income_cat_data = [['Category', 'Amount', 'Percentage']]
        
        for item in income_by_category:
            category_name = item['name'] or 'Uncategorized'
            amount = item['total']
            percentage = (amount / income_total * 100) if income_total else 0
            
            income_cat_data.append([
                category_name,
                f"${amount:.2f}",
                f"{percentage:.1f}%"
            ])
        
        income_cat_table = Table(income_cat_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        income_cat_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add alternating row colors
        for i in range(1, len(income_cat_data)):
            if i % 2 == 0:
                income_cat_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        income_cat_table.setStyle(income_cat_style)
        content.append(income_cat_table)
    else:
        content.append(Paragraph("No income data available", normal_style))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add expenses section
    content.append(Paragraph("Expenses", subtitle_style))
    
    if expense_by_category:
        expense_cat_data = [['Category', 'Amount', 'Percentage']]
        
        for item in expense_by_category:
            category_name = item['name'] or 'Uncategorized'
            amount = item['total']
            percentage = (amount / expense_total * 100) if expense_total else 0
            
            expense_cat_data.append([
                category_name,
                f"${amount:.2f}",
                f"{percentage:.1f}%"
            ])
        
        expense_cat_table = Table(expense_cat_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        
        expense_cat_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Add alternating row colors
        for i in range(1, len(expense_cat_data)):
            if i % 2 == 0:
                expense_cat_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
        
        expense_cat_table.setStyle(expense_cat_style)
        content.append(expense_cat_table)
    else:
        content.append(Paragraph("No expense data available", normal_style))
    
    content.append(Spacer(1, 0.25*inch))
    
    # Add tax deductions section
    content.append(Paragraph("Tax Deductions", subtitle_style))
    
    tax_data = [
        ['Type', 'Amount'],
        ['Business Expenses', f"${tax_deductible_total:.2f}"],
        ['Mileage Deduction', f"${mileage_deduction:.2f}"],
        ['Total Deductions', f"${(tax_deductible_total + mileage_deduction):.2f}"]
    ]
    
    tax_table = Table(tax_data, colWidths=[3*inch, 2*inch])
    
    tax_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ])
    
    tax_table.setStyle(tax_style)
    content.append(tax_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add mileage section
    content.append(Paragraph("Mileage Summary", subtitle_style))
    
    mileage_data = [
        ['Total Miles', f"{mileage_total:.1f} miles"],
        ['Rate per Mile', f"${rate_per_mile:.3f}"],
        ['Deduction Amount', f"${mileage_deduction:.2f}"]
    ]
    
    mileage_table = Table(mileage_data, colWidths=[3*inch, 2*inch])
    
    mileage_style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ])
    
    mileage_table.setStyle(mileage_style)
    content.append(mileage_table)
    
    # Build PDF
    doc.build(content)
    
    # Close connection
    conn.close()
    
    return output_path
