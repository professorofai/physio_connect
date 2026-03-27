#!/Users/akshatjauhari/Desktop/Coding/PHYSIOTHERAPIST/physio_connect/venv/bin/python3
import sys
import os
sys.path.insert(0, '/Users/akshatjauhari/Desktop/Coding/PHYSIOTHERAPIST/physio_connect/venv/lib/python3.14/site-packages')

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, instance_relative_config=True)
app.secret_key = "supersecretkey"

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
import os
os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER), exist_ok=True)

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
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # patient or physiotherapist

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
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return "Registration Successful 🎉"

    return render_template("register.html")

# ✅ LOGIN ROUTE 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Find user by email only
        user = User.query.filter_by(email=email).first()

        # Check if user exists AND password matches hash
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_role"] = user.role
            return redirect("/dashboard")
        else:
            return "Invalid Credentials ❌"

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

    return render_template("book.html")

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