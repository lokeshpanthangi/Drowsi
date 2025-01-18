from flask import Flask, render_template, flash, request, redirect, url_for, session
from flask_session import Session
from pymongo import MongoClient
import bcrypt
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
# Initialize session
app.config['SECRET_KEY'] = 'your_secret_key'  # Set your own secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)  # Initialize session

# Initialize MongoDB
client = MongoClient("mongodb+srv://nikhathmahammad12:AN2bMxZTXGndN4or@cluster0.asogv.mongodb.net/?retryWrites=true&w=majority")
db = client["Drowsi"]  # Replace with your database name
users_collection = db["Drowsi"]  # Replace with your collection name

# Placeholder for hash_password function
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

@app.route('/')
def home():
    return render_template('home.html')  # Home page with login and signup buttons

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        license_number = request.form['license_number']
        vehicle_number = request.form['vehicle_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        today_date = time.strftime("%Y-%m-%d")
        
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('signup'))
        
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for('login'))
        
        hashed_password = hash_password(password)
        user = {
            "name": name,
            "email": email,
            "phone_number": phone_number,
            "license_number": license_number,
            "vehicle_number": vehicle_number,
            "password": hashed_password,
            "day": [today_date],
            "count": [0]
        }
        users_collection.insert_one(user)
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Function to check passwords
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8') if isinstance(hashed, str) else hashed)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users_collection.find_one({"email": email})
        
        if user and check_password(password, user['password']):
            session['email'] = email  # Store email in session
            
            # Generate and send OTP
            otp = generate_otp()
            session["otp"] = otp  # Store OTP in session
            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please check.", "success")
                return redirect(url_for('otp_verification'))
            else:
                flash("Failed to send OTP. Try again.", "danger")
                return redirect(url_for('login'))
        else:
            flash("Invalid email or password", "danger")
    
    return render_template('login.html')

# Function to generate OTP
def generate_otp():
    otp = random.randint(1000, 9999)
    return otp

# Function to send OTP email
def send_otp_email(email, otp):
    sender_email = "nikhathmahammad12@gmail.com"
    sender_password = "yhos ywhn elzt rucx"
    receiver_email = email
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    return True

@app.route('/otp_verification', methods=['POST', 'GET'])
def otp_verification():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        actual_otp = session.get("otp")  # Get stored OTP from session

        if actual_otp and entered_otp == str(actual_otp):  # Compare as string
            session.pop("otp")  # Remove OTP from session after verification
            return redirect(url_for('index'))
        else:
            flash("Invalid OTP, try again.", "danger")

    return render_template('otp_verification.html')

@app.route('/index')  # Index page route
def index():
    if 'email' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    return render_template('index.html')  # This will render the index page

@app.route('/profile')
def profile():
    if 'email' not in session:  
        return redirect(url_for('login'))
    email = session.get('email')  # Get email from session
    user = users_collection.find_one({"email": email})
    if user:
        return render_template('profile.html', user=user)  # Pass user data to the template
    return redirect(url_for('login'))  # Redirect to login if email is not provided

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    email = session['email']  # Get email from session
    user = users_collection.find_one({"email": email})  # Fetch user data from the database

    if request.method == 'POST':
        # Update user details
        updated_name = request.form['name']
        updated_phone = request.form['phone_number']
        updated_license = request.form['license_number']
        updated_vehicle = request.form['vehicle_number']

        users_collection.update_one(
            {"email": email},
            {"$set": {
                "name": updated_name,
                "phone_number": updated_phone,
                "license_number": updated_license,
                "vehicle_number": updated_vehicle
            }}
        )

        # Redirect back to profile with updated details
        return redirect(url_for('profile'))

    # Render the edit profile page
    return render_template('edit_profile.html', user=user)

@app.route('/logout')  
def logout():
    session.pop('email', None)  
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
