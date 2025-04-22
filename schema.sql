-- Initialize the database schema

-- Categories table
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'income', 'expense', or 'mileage'
    description TEXT,
    is_tax_deductible BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts table (clients/vendors)
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'client', 'vendor', or 'both'
    email TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Methods table
CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT 1
);

-- Vehicles table
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    make TEXT,
    model TEXT,
    year INTEGER,
    license_plate TEXT,
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Income Transactions table
CREATE TABLE income (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    category_id INTEGER,
    client_id INTEGER,
    payment_method_id INTEGER,
    invoice_number TEXT,
    payment_status TEXT DEFAULT 'paid',  -- 'paid', 'pending', 'partial'
    is_recurring BOOLEAN DEFAULT 0,
    recurring_frequency TEXT,  -- 'weekly', 'monthly', 'quarterly', 'annually'
    notes TEXT,
    receipt_image TEXT,  -- file path
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (client_id) REFERENCES contacts(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
);

-- Expense Transactions table
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    category_id INTEGER,
    vendor_id INTEGER,
    payment_method_id INTEGER,
    receipt_number TEXT,
    is_tax_deductible BOOLEAN DEFAULT 0,
    is_reimbursable BOOLEAN DEFAULT 0,
    is_reimbursed BOOLEAN DEFAULT 0,
    is_recurring BOOLEAN DEFAULT 0,
    recurring_frequency TEXT,  -- 'weekly', 'monthly', 'quarterly', 'annually'
    notes TEXT,
    receipt_image TEXT,  -- file path
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (vendor_id) REFERENCES contacts(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
);

-- Mileage Logs table
CREATE TABLE mileage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    vehicle_id INTEGER,
    start_odometer DECIMAL(10,1) NOT NULL,
    end_odometer DECIMAL(10,1) NOT NULL,
    distance DECIMAL(10,1) GENERATED ALWAYS AS (end_odometer - start_odometer) STORED,
    purpose TEXT NOT NULL,
    category_id INTEGER,
    client_id INTEGER,  -- if trip is related to a client
    is_round_trip BOOLEAN DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (client_id) REFERENCES contacts(id)
);

-- Mileage Rates table
CREATE TABLE mileage_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    rate_per_mile DECIMAL(10,3) NOT NULL,
    effective_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Settings table
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attachments table
CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    related_to TEXT NOT NULL,  -- 'income', 'expense', or 'mileage'
    related_id INTEGER NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create indexes for performance
CREATE INDEX idx_income_date ON income(date);
CREATE INDEX idx_income_client ON income(client_id);
CREATE INDEX idx_income_category ON income(category_id);

CREATE INDEX idx_expenses_date ON expenses(date);
CREATE INDEX idx_expenses_vendor ON expenses(vendor_id);
CREATE INDEX idx_expenses_category ON expenses(category_id);

CREATE INDEX idx_mileage_date ON mileage(date);
CREATE INDEX idx_mileage_vehicle ON mileage(vehicle_id);
CREATE INDEX idx_mileage_category ON mileage(category_id);
