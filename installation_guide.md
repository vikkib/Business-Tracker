# Installation Guide

This guide provides instructions for installing and setting up the Business Tracker application.

## System Requirements

- Python 3.8 or higher
- SQLite 3
- Modern web browser (Chrome, Firefox, Safari, or Edge)

## Installation Steps

### 1. Download the Application

Download the Business Tracker application package from the provided source.

### 2. Extract the Files

Extract the downloaded package to a directory of your choice.

### 3. Install Python Dependencies

Open a terminal or command prompt, navigate to the application directory, and run:

```bash
pip install -r requirements.txt
```

This will install all the required Python packages:
- Flask
- Flask-WTF
- WTForms
- ReportLab
- python-dotenv

### 4. Initialize the Database

Run the database initialization script:

```bash
python init_db.py
```

This will create the database structure and load sample data for testing.

### 5. Start the Application

Run the application:

```bash
python app.py
```

The application will start and be accessible at http://localhost:5000 in your web browser.

## Directory Structure

- `/data` - Contains the SQLite database file
- `/static` - Static assets (CSS, JavaScript, images)
- `/templates` - HTML templates for the web interface
- `/data/exports` - Generated export files (PDFs, CSVs)

## Configuration

The application uses default settings that should work for most users. If you need to customize the configuration:

1. Create a `.env` file in the application directory
2. Add configuration variables as needed:
   ```
   SECRET_KEY=your_custom_secret_key
   DATABASE_PATH=custom/path/to/database.db
   ```

## Backup Recommendations

It's recommended to regularly back up your database file:

1. Stop the application
2. Copy the `data/business_tracker.db` file to a secure location
3. Restart the application

## Upgrading

When upgrading to a new version:

1. Back up your database file
2. Download and extract the new version
3. Copy your database file to the new version's data directory
4. Install any new dependencies
5. Run the application

## Troubleshooting

### Common Installation Issues

1. **Missing dependencies**: Ensure all required packages are installed using the requirements.txt file.

2. **Database initialization fails**: Check that you have write permissions in the data directory.

3. **Application won't start**: Verify that port 5000 is not in use by another application.

### Getting Help

If you encounter any issues during installation, please refer to the documentation or contact support for assistance.
