import csv
import io
from flask import Response

# Add these routes to app.py

@app.route('/export/income/csv')
def export_income_csv():
    """Export income data as CSV"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
    # Connect to database
    conn = get_db()
    
    # Build query
    query = """
        SELECT i.date, i.description, c.name as category, ct.name as client, 
               i.amount, p.name as payment_method, i.invoice_number, i.payment_status, i.notes
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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Category', 'Client', 'Amount', 
                    'Payment Method', 'Invoice Number', 'Status', 'Notes'])
    
    # Write data
    for item in income:
        writer.writerow([
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
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=income_export_{timestamp}.csv'}
    )

@app.route('/export/expenses/csv')
def export_expenses_csv():
    """Export expenses data as CSV"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    vendor_id = request.args.get('vendor_id', '')
    tax_deductible = request.args.get('tax_deductible', '')
    
    # Connect to database
    conn = get_db()
    
    # Build query
    query = """
        SELECT e.date, e.description, c.name as category, ct.name as vendor, 
               e.amount, p.name as payment_method, e.receipt_number, 
               e.is_tax_deductible, e.is_reimbursable, e.is_reimbursed, e.notes
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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Category', 'Vendor', 'Amount', 
                    'Payment Method', 'Receipt Number', 'Tax Deductible', 
                    'Reimbursable', 'Reimbursed', 'Notes'])
    
    # Write data
    for item in expenses:
        writer.writerow([
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
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=expenses_export_{timestamp}.csv'}
    )

@app.route('/export/mileage/csv')
def export_mileage_csv():
    """Export mileage data as CSV"""
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_id = request.args.get('vehicle_id', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
    # Connect to database
    conn = get_db()
    
    # Build query
    query = """
        SELECT m.date, v.name as vehicle, m.start_odometer, m.end_odometer, 
               m.distance, m.purpose, c.name as category, ct.name as client, 
               m.is_round_trip, m.notes
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
    
    rate_per_mile = mileage_rate['rate_per_mile'] if mileage_rate else 0
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Vehicle', 'Start Odometer', 'End Odometer', 
                    'Distance', 'Purpose', 'Category', 'Client', 'Round Trip', 
                    'Deduction Amount', 'Notes'])
    
    # Write data
    for item in mileage:
        deduction = item['distance'] * rate_per_mile
        writer.writerow([
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
    
    # Create response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=mileage_export_{timestamp}.csv'}
    )
