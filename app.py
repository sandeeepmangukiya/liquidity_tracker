from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from datetime import date

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for session management

# Function to filter entries based on criteria
def filter_entries(entries, month=None, entry_type=None, editor=None):
    filtered_entries = []
    for entry in entries:
        if (not month or entry['date'].split('-')[1] == month) and \
           (not entry_type or entry['entry_type'] == entry_type) and \
           (not editor or entry['editor'] == editor):
            filtered_entries.append(entry)
    return filtered_entries

# Function to calculate total income and expenses
def calculate_total():
    total_income = 0
    total_expense = 0
    with open('entries.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['entry_type'] in ['income', 'capital_credit']:
                total_income += float(row['amount'])
            else:
                total_expense += float(row['amount'])
    return total_income - total_expense, total_income, total_expense

# Function to calculate total income and expenses
def calculate_total_filtered(filtered_entries):
    total_income = 0
    total_expenses = 0
    for entry in filtered_entries:
        if entry['entry_type'] in ['income', 'capital_credit']:
            total_income += float(entry['amount'])
        else:
            total_expenses += float(entry['amount'])
    return total_income - total_expenses, total_income, total_expenses

# Function to read entries from CSV file
def read_csv():
    entries = []
    with open('entries.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entries.append(row)
    return entries

# Function to save entry to CSV file
def save_entry(entry):
    with open('entries.csv', 'a', newline='') as csvfile:
        fieldnames = ['date', 'entry_type', 'description', 'amount', 'editor']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        
        # Write entry data to CSV file
        writer.writerow(entry)

# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        # If user is already logged in, redirect to index page
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get username and password from the login form
        username = request.form['username']
        password = request.form['password']
        
        # Check if the provided username and password are valid
        if validate_user(username, password):
            # If valid, set the 'username' key in the session to mark the user as logged in
            session['username'] = username
            return redirect(url_for('index'))  # Redirect to the index page or any other desired page
        else:
            # If invalid credentials, render the login page again with an error message
            return render_template('login.html', error='Invalid username or password')
    
    # If the request method is GET or the user hasn't logged in yet, render the login page
    return render_template('login.html')

# Function to validate user credentials
def validate_user(username, password):
    with open('users.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username and row['password'] == password:
                return True
    return False

# Route for the registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data from the registration form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        if username_exists(username):
            return render_template('register.html', error='Username already exists')
        
        # Save user data to CSV file
        save_user_to_csv(first_name, last_name, username, password)
        
        # Redirect to the login page after successful registration
        return redirect(url_for('login'))
    
    # If the request method is GET or the registration form hasn't been submitted yet, render the registration page
    return render_template('register.html')

# Function to check if username already exists
def username_exists(username):
    with open('users.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                return True
    return False

# Function to save user data to CSV file
def save_user_to_csv(first_name, last_name, username, password):
    with open('users.csv', 'a', newline='') as csvfile:
        fieldnames = ['first_name', 'last_name', 'username', 'password']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        
        # Write user data to CSV file
        writer.writerow({'first_name': first_name, 'last_name': last_name, 'username': username, 'password': password})

# Route for the index page (protected route)
@app.route('/index')
def index():
    if 'username' not in session:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))
    
    # Get username from current session
    username = session['username']
    
    # If user is logged in, render the index page
    total_amount = calculate_total()
    entries = read_csv()
    today = date.today().isoformat()
    return render_template('index.html', entries=entries, total_amount=total_amount, today=today, username=username)

# Route for the entries page
@app.route('/entries')
def entries():
    if 'username' not in session:
        # If user is not logged in, redirect to login page
        return redirect(url_for('login'))
    
    # Get all entries from the CSV file
    entries = read_csv()
    
    # Extract unique values for filters
    months = set(entry['date'].split('-')[1] for entry in entries)
    entry_types = set(entry['entry_type'] for entry in entries)
    editors = set(entry['editor'] for entry in entries)

    # Get filter parameters from the query string
    month = request.args.get('month')
    entry_type = request.args.get('entry_type')
    editor = request.args.get('editor')

    # Apply filters
    filtered_entries = filter_entries(entries, month, entry_type, editor)
    
    # Calculate total amount of filtered entries
    total_amount = calculate_total_filtered(filtered_entries)
    
    return render_template('entries.html', 
                           filtered_entries=filtered_entries,
                           months=months, 
                           entry_types=entry_types, 
                           editors=editors,
                           total_amount=total_amount)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    date = request.form['date']
    description = request.form['description']
    amount = float(request.form['amount'])
    entry_type = request.form['entry_type']
    editor = request.form['editor']

    entry = {'date': date, 'entry_type': entry_type, 'description': description, 'amount': amount, 'editor': editor}
    save_entry(entry)

    return redirect(url_for('index'))

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove 'username' key from session
    return redirect(url_for('login'))  # Redirect to the login page after logout

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)
