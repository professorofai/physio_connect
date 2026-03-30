#!/Users/akshatjauhari/Desktop/Coding/PHYSIOTHERAPIST/physio_connect/venv/bin/python3
import sys
import os
from datetime import datetime, timedelta
import random
import string
sys.path.insert(0, '/Users/akshatjauhari/Desktop/Coding/PHYSIOTHERAPIST/physio_connect/venv/lib/python3.14/site-packages')

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy

import smtplib
from email.message import EmailMessage

app = Flask(__name__, instance_relative_config=True)
app.secret_key = "supersecretkey"

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
import os
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

# Email config
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'jauhariakshat21@gmail.com'
EMAIL_HOST_PASSWORD = 'oqsy puen xbwz pqlw'
EMAIL_FROM = 'jauhariakshat21@gmail.com'


def send_registration_email(to_email, username):
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        app.logger.warning('Email credentials not configured; skipping email send.')
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Your Physio Connect Registration is Complete'
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg.set_content(f"Dear {username},\n\nThank you for registering with Physio Connect! Your account is now active and you can access your dashboard at http://localhost:5000/dashboard\n\nBest regards,\nPhysio Connect Team")

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Failed to send registration email: {e}")
        return False

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_email_otp(email, otp_code):
    """Send OTP via email"""
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        app.logger.warning('Email credentials not configured; skipping email send.')
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Your Physio Connect Verification Code'
    msg['From'] = EMAIL_FROM
    msg['To'] = email
    msg.set_content(f"Your Physio Connect verification code is: {otp_code}. This code will expire in 10 minutes.")

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
        return False

def create_otp_verification(email):
    """Create and store OTP verification"""
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Clean up expired OTPs for this email
    OTPVerification.query.filter_by(email=email, is_used=False).delete()

    otp_verification = OTPVerification(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at
    )

    db.session.add(otp_verification)
    db.session.commit()

    return otp_code

def verify_otp(email, otp_code):
    """Verify OTP code"""
    otp_verification = OTPVerification.query.filter_by(
        email=email,
        otp_code=otp_code,
        is_used=False
    ).first()

    if not otp_verification:
        return False

    if datetime.utcnow() > otp_verification.expires_at:
        return False

    # Mark OTP as used
    otp_verification.is_used = True
    db.session.commit()

    return True


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone_number = db.Column(db.String(15))  # Phone number for contact
    city = db.Column(db.String(100))  # User's city
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # patient or physiotherapist
    is_verified = db.Column(db.Boolean, default=False)  # Email verification status

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    otp_code = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)

class PhysioProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_name = db.Column(db.String(200))
    location = db.Column(db.String(200))
    specialization = db.Column(db.String(200))
    experience = db.Column(db.Integer)
    profile_picture = db.Column(db.String(200))  # filename of uploaded image

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    physio_id = db.Column(db.Integer, db.ForeignKey('physio_profile.id'))
    appointment_date = db.Column(db.String(50))
    status = db.Column(db.String(20), default="pending")

# Home route
@app.route("/")
def home():
    return render_template("home.html")

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        step = request.form.get("step", "1")

        if step == "1":  # Initial registration
            name = request.form.get("name")
            email = request.form.get("email")
            phone_number = request.form.get("phone_number")
            city = request.form.get("city")
            password = request.form.get("password")
            role = request.form.get("role")

            # Basic validation
            if not all([name, email, phone_number, city, password, role]):
                flash('All fields are required.', 'danger')
                return render_template("register.html")

            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == email) | (User.phone_number == phone_number)
            ).first()
            if existing_user:
                flash('User with this email or phone number already exists.', 'danger')
                return render_template("register.html")

            # Store registration data in session temporarily
            session['reg_data'] = {
                'name': name,
                'email': email,
                'phone_number': phone_number,
                'city': city,
                'password': password,
                'role': role
            }

            # Generate and send OTP
            otp_code = create_otp_verification(email)
            email_sent = send_email_otp(email, otp_code)

            if not email_sent:
                flash('Failed to send verification email. Please try again.', 'danger')
                return render_template("register.html")

            flash('Verification code sent to your email. Please enter it below.', 'info')
            return render_template("verify_otp.html", email=email, action="register")

        elif step == "2":  # OTP verification
            email = request.form.get("email")
            otp_code = request.form.get("otp_code")

            if not verify_otp(email, otp_code):
                flash('Invalid or expired verification code.', 'danger')
                return render_template("verify_otp.html", email=email, action="register")

            # Get registration data from session
            reg_data = session.get('reg_data')
            if not reg_data:
                flash('Registration session expired. Please start over.', 'danger')
                return redirect("/register")

            # Create user account
            hashed_password = generate_password_hash(reg_data['password'])

            new_user = User(
                name=reg_data['name'],
                email=reg_data['email'],
                phone_number=reg_data['phone_number'],
                city=reg_data['city'],
                password=hashed_password,
                role=reg_data['role'],
                is_verified=True
            )

            db.session.add(new_user)
            db.session.commit()

            # Clear session data
            session.pop('reg_data', None)

            # Send confirmation email
            email_sent = send_registration_email(reg_data['email'], reg_data['name'])
            if not email_sent:
                flash('Registration successful, but confirmation email was not sent.', 'warning')
            else:
                flash('Registration successful! Welcome to Physio Connect.', 'success')

            # Auto-login after registration
            session["user_id"] = new_user.id
            session["user_email"] = new_user.email
            session["user_role"] = new_user.role

            return redirect("/dashboard")

    return render_template("register.html")

# ✅ LOGIN ROUTE 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template("login.html")

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.', 'danger')
            return render_template("login.html")

        # Set login session
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_role"] = user.role

        flash('Login successful! Welcome back.', 'success')
        return redirect("/dashboard")

    return render_template("login.html")
# Dashboard route
@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect("/login")

    if session["user_role"] == "physiotherapist":
        # Get physio profile for dashboard
        physio_profile = PhysioProfile.query.filter_by(user_id=session["user_id"]).first()
        return render_template(
            "physio_dashboard.html",
            email=session["user_email"],
            physio_profile=physio_profile
        )

    elif session["user_role"] == "patient":
        return render_template(
            "patient_dashboard.html",
            email=session["user_email"]
        )
    
@app.route("/create_profile", methods=["GET", "POST"])
def create_profile():
    if request.method == "POST":
        clinic_name = request.form["clinic_name"]
        location = request.form["location"]
        specialization = request.form["specialization"]

        # Handle file upload
        profile_picture_filename = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid filename conflicts
                import time
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                profile_picture_filename = filename

        profile = PhysioProfile(
            clinic_name=clinic_name,
            location=location,
            specialization=specialization,
            profile_picture=profile_picture_filename,
            user_id=session["user_id"]
        )

        db.session.add(profile)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("create_profile.html")

@app.route("/physios")
def physios():

    physio_list = PhysioProfile.query.all()

    return render_template(
        "physios.html",
        physios=physio_list
    )
#bookings
@app.route("/book/<int:physio_id>", methods=["GET","POST"])
def book(physio_id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        date = request.form.get("date")

        appointment = Appointment(
            patient_id=session["user_id"],
            physio_id=physio_id,
            appointment_date=date
        )

        db.session.add(appointment)
        db.session.commit()

        # Get physio details
        physio = PhysioProfile.query.get(physio_id)
        
        return render_template("booking_confirmation.html", 
                             date=date, 
                             physio_name=physio.clinic_name if physio else "Unknown",
                             status="Pending")

    return render_template("book.html", physio=PhysioProfile.query.get(physio_id), today=datetime.now().strftime('%Y-%m-%d'))

@app.route("/physio_appointments")
def physio_appointments():

    if "user_id" not in session:
        return redirect("/login")

    if session["user_role"] != "physiotherapist":
        return "Access Denied ❌"

    physio = PhysioProfile.query.filter_by(user_id=session["user_id"]).first()

    # ✅ ADD THIS FIX
    if not physio:
        return "Please create your profile first ❗"

    appointments = Appointment.query.filter_by(physio_id=physio.id).all()

    data = []

    for appt in appointments:
        patient = User.query.get(appt.patient_id)

        if patient:
            data.append({
                "id": appt.id,
                "name": patient.name,
                "email": patient.email,
                "date": appt.appointment_date,
                "status": appt.status
            })

    return render_template(
        "physio_appointments.html",
        appointments=data
    )
@app.route('/approve/<int:id>')
def approve(id):
    appt = Appointment.query.get(id)
    if appt:
        appt.status = "Approved"
        db.session.commit()
    return redirect('/physio_appointments')


@app.route('/reject/<int:id>')
def reject(id):
    appt = Appointment.query.get(id)
    if appt:
        appt.status = "Rejected"
        db.session.commit()
    return redirect('/physio_appointments')

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)