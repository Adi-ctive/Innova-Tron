from flask import Flask, render_template, redirect, url_for, request, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Simulated user database (replace with a real database in production)
users = {
    'admin': 'pass'  # Example user: admin / password
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the user exists and the password matches
        if username in users and users[username] == password:
            return redirect(url_for('main_site'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the username already exists
        if username in users:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            users[username] = password
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/main_site')
def main_site():
    return render_template('main_site.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
