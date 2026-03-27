from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"

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
        return render_template(
            "physio_dashboard.html",
            email=session["user_email"]
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

        profile = PhysioProfile(
    clinic_name=clinic_name,
    location=location,
    specialization=specialization,
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

        return "Appointment Booked Successfully 🎉"

    return render_template("book.html")

@app.route("/physio_appointments")
def physio_appointments():

    if "user_id" not in session:
        return redirect("/login")

    if session["user_role"] != "physiotherapist":
        return "Access Denied ❌"

    # find physio profile
    physio = PhysioProfile.query.filter_by(user_id=session["user_id"]).first()

    # find appointments for this physio
    appointments = Appointment.query.filter_by(physio_id=physio.id).all()

    data = []

    for appt in appointments:
     patient = User.query.get(appt.patient_id)

     data.append({
    "id": appt.id,
    "name": patient.name,
    "email": patient.email,
    "date": appt.appointment_date,
    "status": appt.status
})

    return render_template(
    "physio_appointments.html",
    appointments = data
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