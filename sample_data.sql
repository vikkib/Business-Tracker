-- Initialize database with sample data for testing

-- Create tables if they don't exist
PRAGMA foreign_keys = ON;

-- Insert sample categories
INSERT OR IGNORE INTO categories (id, name, type, is_tax_deductible, description) VALUES
(1, 'Consulting Services', 'income', 0, 'Income from consulting work'),
(2, 'Product Sales', 'income', 0, 'Income from product sales'),
(3, 'Contract Work', 'income', 0, 'Income from contract-based projects'),
(4, 'Office Supplies', 'expense', 1, 'Office supplies and stationery'),
(5, 'Software Subscriptions', 'expense', 1, 'Software and online services'),
(6, 'Travel', 'expense', 1, 'Business travel expenses'),
(7, 'Meals & Entertainment', 'expense', 1, 'Business meals and entertainment'),
(8, 'Equipment', 'expense', 1, 'Business equipment purchases'),
(9, 'Client Meetings', 'mileage', 1, 'Travel to client meetings'),
(10, 'Conferences', 'mileage', 1, 'Travel to conferences and events'),
(11, 'Site Visits', 'mileage', 1, 'Travel to project sites');

-- Insert sample contacts (clients and vendors)
INSERT OR IGNORE INTO contacts (id, name, type, email, phone, address, notes) VALUES
(1, 'Acme Corporation', 'client', 'contact@acme.com', '555-123-4567', '123 Business Ave, Suite 100', 'Major client for consulting services'),
(2, 'TechStart Inc.', 'client', 'info@techstart.com', '555-987-6543', '456 Innovation Dr', 'Startup client, monthly retainer'),
(3, 'Global Enterprises', 'client', 'sales@globalent.com', '555-456-7890', '789 Corporate Blvd', 'International client, quarterly projects'),
(4, 'Office Depot', 'vendor', 'support@officedepot.com', '800-123-4567', '100 Supply Chain Rd', 'Office supplies vendor'),
(5, 'Adobe', 'vendor', 'billing@adobe.com', '800-833-6687', '345 Park Ave', 'Software subscription vendor'),
(6, 'Dell', 'vendor', 'sales@dell.com', '800-624-9897', '1 Dell Way', 'Computer equipment vendor');

-- Insert sample payment methods
INSERT OR IGNORE INTO payment_methods (id, name, description) VALUES
(1, 'Credit Card', 'Business credit card'),
(2, 'Bank Transfer', 'Direct bank transfer'),
(3, 'PayPal', 'PayPal business account'),
(4, 'Check', 'Business checks'),
(5, 'Cash', 'Cash payments');

-- Insert sample vehicles
INSERT OR IGNORE INTO vehicles (id, name, make, model, year, license_plate, notes) VALUES
(1, 'Primary Car', 'Toyota', 'Camry', 2022, 'ABC-1234', 'Main business vehicle'),
(2, 'Secondary Car', 'Honda', 'Accord', 2020, 'XYZ-5678', 'Backup business vehicle');

-- Insert sample mileage rates
INSERT OR IGNORE INTO mileage_rates (id, year, rate_per_mile, effective_date, notes) VALUES
(1, 2023, 0.655, '2023-01-01', 'IRS standard mileage rate for 2023'),
(2, 2024, 0.67, '2024-01-01', 'IRS standard mileage rate for 2024'),
(3, 2025, 0.685, '2025-01-01', 'IRS standard mileage rate for 2025');

-- Insert sample income transactions
INSERT OR IGNORE INTO income (id, date, description, amount, category_id, client_id, payment_method_id, invoice_number, payment_status, notes) VALUES
(1, '2025-01-15', 'January Consulting Retainer', 5000.00, 1, 1, 2, 'INV-2025-001', 'paid', 'Monthly retainer payment'),
(2, '2025-01-22', 'Website Development Project', 3500.00, 3, 2, 2, 'INV-2025-002', 'paid', 'Phase 1 payment'),
(3, '2025-02-01', 'Product License Sales', 1200.00, 2, 3, 3, 'INV-2025-003', 'paid', 'Q1 license sales'),
(4, '2025-02-15', 'February Consulting Retainer', 5000.00, 1, 1, 2, 'INV-2025-004', 'paid', 'Monthly retainer payment'),
(5, '2025-02-28', 'Website Development Project', 3500.00, 3, 2, 2, 'INV-2025-005', 'paid', 'Phase 2 payment'),
(6, '2025-03-15', 'March Consulting Retainer', 5000.00, 1, 1, 2, 'INV-2025-006', 'paid', 'Monthly retainer payment'),
(7, '2025-03-20', 'Custom Software Development', 7500.00, 3, 3, 2, 'INV-2025-007', 'paid', 'New project payment'),
(8, '2025-04-01', 'Product License Sales', 1500.00, 2, 3, 3, 'INV-2025-008', 'paid', 'Q2 license sales'),
(9, '2025-04-15', 'April Consulting Retainer', 5000.00, 1, 1, 2, 'INV-2025-009', 'pending', 'Monthly retainer payment'),
(10, '2025-04-18', 'Website Maintenance', 1200.00, 3, 2, 3, 'INV-2025-010', 'pending', 'Quarterly maintenance fee');

-- Insert sample expense transactions
INSERT OR IGNORE INTO expenses (id, date, description, amount, category_id, vendor_id, payment_method_id, receipt_number, is_tax_deductible, is_reimbursable, is_reimbursed, notes) VALUES
(1, '2025-01-05', 'Office Supplies', 125.75, 4, 4, 1, 'REC-2025-001', 1, 0, 0, 'Paper, pens, notebooks'),
(2, '2025-01-10', 'Adobe Creative Cloud Subscription', 52.99, 5, 5, 1, 'REC-2025-002', 1, 0, 0, 'Monthly subscription'),
(3, '2025-01-20', 'Client Lunch Meeting', 85.43, 7, NULL, 1, 'REC-2025-003', 1, 0, 0, 'Lunch with Acme Corp team'),
(4, '2025-02-05', 'Office Supplies', 78.32, 4, 4, 1, 'REC-2025-004', 1, 0, 0, 'Printer ink, folders'),
(5, '2025-02-10', 'Adobe Creative Cloud Subscription', 52.99, 5, 5, 1, 'REC-2025-005', 1, 0, 0, 'Monthly subscription'),
(6, '2025-02-15', 'New Laptop', 1299.99, 8, 6, 1, 'REC-2025-006', 1, 0, 0, 'Development laptop'),
(7, '2025-03-05', 'Office Supplies', 45.67, 4, 4, 1, 'REC-2025-007', 1, 0, 0, 'Desk organizers'),
(8, '2025-03-10', 'Adobe Creative Cloud Subscription', 52.99, 5, 5, 1, 'REC-2025-008', 1, 0, 0, 'Monthly subscription'),
(9, '2025-03-25', 'Conference Registration', 499.00, 6, NULL, 1, 'REC-2025-009', 1, 0, 0, 'Annual industry conference'),
(10, '2025-04-05', 'Office Supplies', 112.45, 4, 4, 1, 'REC-2025-010', 1, 0, 0, 'Paper, business cards'),
(11, '2025-04-10', 'Adobe Creative Cloud Subscription', 52.99, 5, 5, 1, 'REC-2025-011', 1, 0, 0, 'Monthly subscription'),
(12, '2025-04-12', 'Hotel for Conference', 425.60, 6, NULL, 1, 'REC-2025-012', 1, 0, 0, '2 nights accommodation');

-- Insert sample mileage entries - removed distance column as it's generated automatically
INSERT OR IGNORE INTO mileage (id, date, vehicle_id, start_odometer, end_odometer, purpose, category_id, client_id, is_round_trip, notes) VALUES
(1, '2025-01-08', 1, 12500.0, 12528.5, 'Meeting with Acme Corp', 9, 1, 1, 'Quarterly planning meeting'),
(2, '2025-01-17', 1, 12600.0, 12615.0, 'Meeting with TechStart', 9, 2, 1, 'Project kickoff meeting'),
(3, '2025-02-05', 1, 12700.0, 12728.5, 'Meeting with Acme Corp', 9, 1, 1, 'Progress review meeting'),
(4, '2025-02-20', 1, 12800.0, 12815.0, 'Meeting with TechStart', 9, 2, 1, 'Phase 2 planning'),
(5, '2025-03-08', 1, 12900.0, 12928.5, 'Meeting with Acme Corp', 9, 1, 1, 'Monthly status meeting'),
(6, '2025-03-15', 1, 13000.0, 13015.0, 'Meeting with TechStart', 9, 2, 1, 'Project review'),
(7, '2025-03-26', 1, 13100.0, 13250.0, 'Travel to Conference', 10, NULL, 1, 'Annual industry conference'),
(8, '2025-04-05', 1, 13300.0, 13328.5, 'Meeting with Acme Corp', 9, 1, 1, 'Quarterly planning meeting'),
(9, '2025-04-12', 1, 13400.0, 13415.0, 'Meeting with TechStart', 9, 2, 1, 'Maintenance planning'),
(10, '2025-04-18', 1, 13500.0, 13545.0, 'Site Visit with Global Enterprises', 11, 3, 1, 'Project site inspection');
