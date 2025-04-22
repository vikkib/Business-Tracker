import os
import csv
import io
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, send_file, Response

# Import export functions
from pdf_generator import (
    generate_income_pdf, 
    generate_expenses_pdf, 
    generate_mileage_pdf, 
    generate_profit_loss_pdf, 
    generate_year_end_pdf
)

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['DATABASE'] = 'data/business_tracker.db'

# Database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Routes
from datetime import datetime

@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()

    # Total income
    cursor.execute("SELECT SUM(amount) FROM income")
    result = cursor.fetchone()
    income_total = result[0] if result[0] is not None else 0.00

    # Total expenses
    cursor.execute("SELECT SUM(amount) FROM expenses")
    result = cursor.fetchone()
    expense_total = result[0] if result[0] is not None else 0.00

    # Total mileage
    cursor.execute("SELECT SUM(distance) FROM mileage")
    result = cursor.fetchone()
    mileage_total = result[0] if result[0] is not None else 0.0

    return render_template(
        "index.html",
        now=datetime.now(),
        income_total=income_total,
        expense_total=expense_total,
        mileage_total=mileage_total
    )
    
    # Get current year
    current_year = datetime.now().year
    start_date = f"{current_year}-01-01"
    end_date = f"{current_year}-12-31"
    
    # Get income total
    cursor = conn.execute(
        "SELECT SUM(amount) as total FROM income WHERE date >= ? AND date <= ?", 
        [start_date, end_date]
    )
    income_total = cursor.fetchone()['total'] or 0
    
    # Get expense total
    cursor = conn.execute(
        "SELECT SUM(amount) as total FROM expenses WHERE date >= ? AND date <= ?", 
        [start_date, end_date]
    )
    expense_total = cursor.fetchone()['total'] or 0
    
    # Get mileage total
    cursor = conn.execute(
        "SELECT SUM(distance) as total FROM mileage WHERE date >= ? AND date <= ?", 
        [start_date, end_date]
    )
    mileage_total = cursor.fetchone()['total'] or 0
    
    # Get mileage rate
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
    mileage_deduction = mileage_total * rate_per_mile
    
    # Calculate profit/loss
    profit_loss = income_total - expense_total
    
    # Get recent transactions
    cursor = conn.execute(
        "SELECT date, description, amount, 'income' as type FROM income ORDER BY date DESC LIMIT 5"
    )
    recent_income = cursor.fetchall()
    
    cursor = conn.execute(
        "SELECT date, description, amount, 'expense' as type FROM expenses ORDER BY date DESC LIMIT 5"
    )
    recent_expenses = cursor.fetchall()
    
    # Combine and sort by date
    recent_transactions = sorted(
        list(recent_income) + list(recent_expenses),
        key=lambda x: x['date'],
        reverse=True
    )[:5]
    
    return render_template(
        'index.html',
        now=datetime.now(),
        income_total=income_total,
        expense_total=expense_total,
        profit_loss=profit_loss,
        mileage_total=mileage_total,
        mileage_rate=rate_per_mile,
        mileage_deduction=mileage_deduction,
        recent_transactions=recent_transactions,
        current_year=current_year
    )

# Income routes
@app.route('/income')
def income_list():
    conn = get_db()
    cursor = conn.execute("""
        SELECT i.*, c.name as category_name, ct.name as client_name, p.name as payment_method_name
        FROM income i
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN contacts ct ON i.client_id = ct.id
        LEFT JOIN payment_methods p ON i.payment_method_id = p.id
        ORDER BY i.date DESC
    """)
    income = cursor.fetchall()
    return render_template('income/list.html', income=income, now=datetime.now())

@app.route('/income/add', methods=['GET', 'POST'])
def income_add():
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id') or None
        client_id = request.form.get('client_id') or None
        payment_method_id = request.form.get('payment_method_id') or None
        invoice_number = request.form.get('invoice_number')
        payment_status = request.form.get('payment_status')
        notes = request.form.get('notes')
        
        # Insert into database
        conn.execute("""
            INSERT INTO income (date, description, amount, category_id, client_id, 
                               payment_method_id, invoice_number, payment_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [date, description, amount, category_id, client_id, 
              payment_method_id, invoice_number, payment_status, notes])
        conn.commit()
        
        flash('Income transaction added successfully!', 'success')
        return redirect(url_for('income_list'))
    
    # Get categories, clients, and payment methods for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'income' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM payment_methods ORDER BY name")
    payment_methods = cursor.fetchall()
    
    return render_template(
        'income/add.html',
        categories=categories,
        clients=clients,
        payment_methods=payment_methods
    )

@app.route('/income/edit/<int:id>', methods=['GET', 'POST'])
def income_edit(id):
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id') or None
        client_id = request.form.get('client_id') or None
        payment_method_id = request.form.get('payment_method_id') or None
        invoice_number = request.form.get('invoice_number')
        payment_status = request.form.get('payment_status')
        notes = request.form.get('notes')
        
        # Update database
        conn.execute("""
            UPDATE income 
            SET date = ?, description = ?, amount = ?, category_id = ?, 
                client_id = ?, payment_method_id = ?, invoice_number = ?, 
                payment_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [date, description, amount, category_id, client_id, 
              payment_method_id, invoice_number, payment_status, notes, id])
        conn.commit()
        
        flash('Income transaction updated successfully!', 'success')
        return redirect(url_for('income_list'))
    
    # Get income transaction
    cursor = conn.execute("SELECT * FROM income WHERE id = ?", [id])
    income = cursor.fetchone()
    
    if not income:
        flash('Income transaction not found!', 'danger')
        return redirect(url_for('income_list'))
    
    # Get categories, clients, and payment methods for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'income' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM payment_methods ORDER BY name")
    payment_methods = cursor.fetchall()
    
    return render_template(
        'income/edit.html',
        income=income,
        categories=categories,
        clients=clients,
        payment_methods=payment_methods
    )

@app.route('/income/delete/<int:id>', methods=['POST'])
def income_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM income WHERE id = ?", [id])
    conn.commit()
    
    flash('Income transaction deleted successfully!', 'success')
    return redirect(url_for('income_list'))

# Expense routes
@app.route('/expenses')
def expenses_list():
    conn = get_db()
    cursor = conn.execute("""
        SELECT e.*, c.name as category_name, ct.name as vendor_name, p.name as payment_method_name
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN contacts ct ON e.vendor_id = ct.id
        LEFT JOIN payment_methods p ON e.payment_method_id = p.id
        ORDER BY e.date DESC
    """)
    expenses = cursor.fetchall()
    return render_template('expenses/list.html', expenses=expenses, now=datetime.now())

@app.route('/expenses/add', methods=['GET', 'POST'])
def expenses_add():
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id') or None
        vendor_id = request.form.get('vendor_id') or None
        payment_method_id = request.form.get('payment_method_id') or None
        receipt_number = request.form.get('receipt_number')
        is_tax_deductible = 1 if request.form.get('is_tax_deductible') else 0
        is_reimbursable = 1 if request.form.get('is_reimbursable') else 0
        is_reimbursed = 1 if request.form.get('is_reimbursed') else 0
        notes = request.form.get('notes')
        
        # Insert into database
        conn.execute("""
            INSERT INTO expenses (date, description, amount, category_id, vendor_id, 
                                payment_method_id, receipt_number, is_tax_deductible,
                                is_reimbursable, is_reimbursed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [date, description, amount, category_id, vendor_id, 
              payment_method_id, receipt_number, is_tax_deductible,
              is_reimbursable, is_reimbursed, notes])
        conn.commit()
        
        flash('Expense transaction added successfully!', 'success')
        return redirect(url_for('expenses_list'))
    
    # Get categories, vendors, and payment methods for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'expense' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('vendor', 'both') ORDER BY name")
    vendors = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM payment_methods ORDER BY name")
    payment_methods = cursor.fetchall()
    
    return render_template(
        'expenses/add.html',
        categories=categories,
        vendors=vendors,
        payment_methods=payment_methods
    )

@app.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
def expenses_edit(id):
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        description = request.form.get('description')
        amount = request.form.get('amount')
        category_id = request.form.get('category_id') or None
        vendor_id = request.form.get('vendor_id') or None
        payment_method_id = request.form.get('payment_method_id') or None
        receipt_number = request.form.get('receipt_number')
        is_tax_deductible = 1 if request.form.get('is_tax_deductible') else 0
        is_reimbursable = 1 if request.form.get('is_reimbursable') else 0
        is_reimbursed = 1 if request.form.get('is_reimbursed') else 0
        notes = request.form.get('notes')
        
        # Update database
        conn.execute("""
            UPDATE expenses 
            SET date = ?, description = ?, amount = ?, category_id = ?, 
                vendor_id = ?, payment_method_id = ?, receipt_number = ?, 
                is_tax_deductible = ?, is_reimbursable = ?, is_reimbursed = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [date, description, amount, category_id, vendor_id, 
              payment_method_id, receipt_number, is_tax_deductible,
              is_reimbursable, is_reimbursed, notes, id])
        conn.commit()
        
        flash('Expense transaction updated successfully!', 'success')
        return redirect(url_for('expenses_list'))
    
    # Get expense transaction
    cursor = conn.execute("SELECT * FROM expenses WHERE id = ?", [id])
    expense = cursor.fetchone()
    
    if not expense:
        flash('Expense transaction not found!', 'danger')
        return redirect(url_for('expenses_list'))
    
    # Get categories, vendors, and payment methods for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'expense' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('vendor', 'both') ORDER BY name")
    vendors = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM payment_methods ORDER BY name")
    payment_methods = cursor.fetchall()
    
    return render_template(
        'expenses/edit.html',
        expense=expense,
        categories=categories,
        vendors=vendors,
        payment_methods=payment_methods
    )

@app.route('/expenses/delete/<int:id>', methods=['POST'])
def expenses_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", [id])
    conn.commit()
    
    flash('Expense transaction deleted successfully!', 'success')
    return redirect(url_for('expenses_list'))

# Mileage routes
@app.route('/mileage')
def mileage_list():
    conn = get_db()
    cursor = conn.execute("""
        SELECT m.*, c.name as category_name, v.name as vehicle_name, ct.name as client_name
        FROM mileage m
        LEFT JOIN categories c ON m.category_id = c.id
        LEFT JOIN vehicles v ON m.vehicle_id = v.id
        LEFT JOIN contacts ct ON m.client_id = ct.id
        ORDER BY m.date DESC
    """)
    mileage = cursor.fetchall()
    return render_template('mileage/list.html', mileage=mileage, now=datetime.now())

@app.route('/mileage/add', methods=['GET', 'POST'])
def mileage_add():
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        vehicle_id = request.form.get('vehicle_id') or None
        start_odometer = request.form.get('start_odometer')
        end_odometer = request.form.get('end_odometer')
        purpose = request.form.get('purpose')
        category_id = request.form.get('category_id') or None
        client_id = request.form.get('client_id') or None
        is_round_trip = 1 if request.form.get('is_round_trip') else 0
        notes = request.form.get('notes')
        
        # Insert into database
        conn.execute("""
            INSERT INTO mileage (date, vehicle_id, start_odometer, end_odometer, 
                               purpose, category_id, client_id, is_round_trip, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [date, vehicle_id, start_odometer, end_odometer, 
              purpose, category_id, client_id, is_round_trip, notes])
        conn.commit()
        
        flash('Mileage entry added successfully!', 'success')
        return redirect(url_for('mileage_list'))
    
    # Get categories, clients, and vehicles for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'mileage' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM vehicles WHERE is_active = 1 ORDER BY name")
    vehicles = cursor.fetchall()
    
    return render_template(
        'mileage/add.html',
        categories=categories,
        clients=clients,
        vehicles=vehicles
    )

@app.route('/mileage/edit/<int:id>', methods=['GET', 'POST'])
def mileage_edit(id):
    conn = get_db()
    
    if request.method == 'POST':
        # Get form data
        date = request.form.get('date')
        vehicle_id = request.form.get('vehicle_id') or None
        start_odometer = request.form.get('start_odometer')
        end_odometer = request.form.get('end_odometer')
        purpose = request.form.get('purpose')
        category_id = request.form.get('category_id') or None
        client_id = request.form.get('client_id') or None
        is_round_trip = 1 if request.form.get('is_round_trip') else 0
        notes = request.form.get('notes')
        
        # Update database
        conn.execute("""
            UPDATE mileage 
            SET date = ?, vehicle_id = ?, start_odometer = ?, end_odometer = ?, 
                purpose = ?, category_id = ?, client_id = ?, is_round_trip = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [date, vehicle_id, start_odometer, end_odometer, 
              purpose, category_id, client_id, is_round_trip, notes, id])
        conn.commit()
        
        flash('Mileage entry updated successfully!', 'success')
        return redirect(url_for('mileage_list'))
    
    # Get mileage entry
    cursor = conn.execute("SELECT * FROM mileage WHERE id = ?", [id])
    mileage = cursor.fetchone()
    
    if not mileage:
        flash('Mileage entry not found!', 'danger')
        return redirect(url_for('mileage_list'))
    
    # Get categories, clients, and vehicles for the form
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'mileage' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM vehicles WHERE is_active = 1 ORDER BY name")
    vehicles = cursor.fetchall()
    
    return render_template(
        'mileage/edit.html',
        mileage=mileage,
        categories=categories,
        clients=clients,
        vehicles=vehicles
    )

@app.route('/mileage/delete/<int:id>', methods=['POST'])
def mileage_delete(id):
    conn = get_db()
    conn.execute("DELETE FROM mileage WHERE id = ?", [id])
    conn.commit()
    
    flash('Mileage entry deleted successfully!', 'success')
    return redirect(url_for('mileage_list'))

# Report routes
@app.route('/reports')
def reports_index():
    conn = get_db()
    now = datetime.now()
    
    return render_template('reports/index.html', now=now)

@app.route('/reports/income')
def reports_income():
    conn = get_db()
    
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
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
    
    query += " ORDER BY i.date DESC"
    
    # Execute query
    cursor = conn.execute(query, params)
    income = cursor.fetchall()
    
    # Calculate total
    total_amount = sum(row['amount'] for row in income)
    
    # Get categories and clients for filter
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'income' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    return render_template(
        'reports/income.html',
        income=income,
        total_amount=total_amount,
        categories=categories,
        clients=clients,
        filters={
            'start_date': start_date,
            'end_date': end_date,
            'category_id': category_id,
            'client_id': client_id
        }
    )

@app.route('/reports/expenses')
def reports_expenses():
    conn = get_db()
    
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    category_id = request.args.get('category_id', '')
    vendor_id = request.args.get('vendor_id', '')
    tax_deductible = request.args.get('tax_deductible', '')
    
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
    
    query += " ORDER BY e.date DESC"
    
    # Execute query
    cursor = conn.execute(query, params)
    expenses = cursor.fetchall()
    
    # Calculate total
    total_amount = sum(row['amount'] for row in expenses)
    
    # Get categories and vendors for filter
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'expense' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('vendor', 'both') ORDER BY name")
    vendors = cursor.fetchall()
    
    return render_template(
        'reports/expenses.html',
        expenses=expenses,
        total_amount=total_amount,
        categories=categories,
        vendors=vendors,
        filters={
            'start_date': start_date,
            'end_date': end_date,
            'category_id': category_id,
            'vendor_id': vendor_id,
            'tax_deductible': tax_deductible
        }
    )

@app.route('/reports/mileage')
def reports_mileage():
    conn = get_db()
    
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    vehicle_id = request.args.get('vehicle_id', '')
    category_id = request.args.get('category_id', '')
    client_id = request.args.get('client_id', '')
    
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
    
    query += " ORDER BY m.date DESC"
    
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
    
    # Get categories, vehicles, and clients for filter
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'mileage' ORDER BY name")
    categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM vehicles WHERE is_active = 1 ORDER BY name")
    vehicles = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    return render_template(
        'reports/mileage.html',
        mileage=mileage,
        total_distance=total_distance,
        mileage_rate=mileage_rate,
        deduction_amount=deduction_amount,
        categories=categories,
        vehicles=vehicles,
        clients=clients,
        filters={
            'start_date': start_date,
            'end_date': end_date,
            'vehicle_id': vehicle_id,
            'category_id': category_id,
            'client_id': client_id
        }
    )

@app.route('/reports/profit-loss')
def reports_profit_loss():
    conn = get_db()
    
    # Get filter parameters
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
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
    
    return render_template(
        'reports/profit_loss.html',
        income_amount=income_amount,
        expense_amount=expense_amount,
        profit_loss=profit_loss,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        filters={
            'start_date': start_date,
            'end_date': end_date
        }
    )

@app.route('/reports/year-end/<int:year>')
def reports_year_end(year):
    conn = get_db()
    
    # Date range for the year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
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
    profit_loss = income_total - expense_total
    
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
        SELECT e.*, c.name as category_name, ct.name as vendor_name
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        LEFT JOIN contacts ct ON e.vendor_id = ct.id
        WHERE e.date >= ? AND e.date <= ? AND e.is_tax_deductible = 1
        ORDER BY e.date
    """, [start_date, end_date])
    tax_deductible_expenses = cursor.fetchall()
    
    # Calculate tax deductible total
    tax_deductible_total = sum(row['amount'] for row in tax_deductible_expenses)
    
    # Get all categories
    cursor = conn.execute("SELECT * FROM categories")
    categories = cursor.fetchall()
    
    return render_template(
        'reports/year_end.html',
        year=year,
        income_total=income_total,
        expense_total=expense_total,
        mileage_total=mileage_total,
        mileage_rate=mileage_rate,
        mileage_deduction=mileage_deduction,
        profit_loss=profit_loss,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        tax_deductible_expenses=tax_deductible_expenses,
        tax_deductible_total=tax_deductible_total,
        categories=categories,
        now=datetime.now()
    )

# Export routes
@app.route('/export')
def export_index():
    conn = get_db()
    now = datetime.now()
    
    # Get categories for each type
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'income' ORDER BY name")
    income_categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'expense' ORDER BY name")
    expense_categories = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM categories WHERE type = 'mileage' ORDER BY name")
    mileage_categories = cursor.fetchall()
    
    # Get clients, vendors, and vehicles
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('client', 'both') ORDER BY name")
    clients = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM contacts WHERE type IN ('vendor', 'both') ORDER BY name")
    vendors = cursor.fetchall()
    
    cursor = conn.execute("SELECT * FROM vehicles WHERE is_active = 1 ORDER BY name")
    vehicles = cursor.fetchall()
    
    return render_template(
        'export/index.html',
        income_categories=income_categories,
        expense_categories=expense_categories,
        mileage_categories=mileage_categories,
        clients=clients,
        vendors=vendors,
        vehicles=vehicles,
        now=now
    )

# CSV Export routes
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

# PDF Export routes
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

# Run the application
if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize database if it doesn't exist
    if not os.path.exists('data/business_tracker.db'):
        from init_db import init_db
        init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5050)
