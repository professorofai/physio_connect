import os
import time

from flask import Blueprint, current_app, redirect, render_template, request, session
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Appointment, PhysioProfile, User
from app.utils.helpers import allowed_file

physio_bp = Blueprint("physio", __name__)


@physio_bp.route("/create_profile", methods=["GET", "POST"], endpoint="create_profile")
def create_profile():
    if request.method == "POST":
        clinic_name = request.form["clinic_name"]
        location = request.form["location"]
        specialization = request.form["specialization"]

        profile_picture_filename = None
        if "profile_picture" in request.files:
            file = request.files["profile_picture"]
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                profile_picture_filename = filename

        profile = PhysioProfile(
            clinic_name=clinic_name,
            location=location,
            specialization=specialization,
            profile_picture=profile_picture_filename,
            user_id=session["user_id"],
        )

        db.session.add(profile)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("create_profile.html")


@physio_bp.route("/physio_appointments", endpoint="physio_appointments")
def physio_appointments():
    if "user_id" not in session:
        return redirect("/login")

    if session["user_role"] != "physiotherapist":
        return "Access Denied ❌"

    physio = PhysioProfile.query.filter_by(user_id=session["user_id"]).first()

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
                "status": appt.status,
            })

    return render_template("physio_appointments.html", appointments=data)


@physio_bp.route("/approve/<int:id>", endpoint="approve")
def approve(id):
    appt = Appointment.query.get(id)
    if appt:
        appt.status = "Approved"
        db.session.commit()
    return redirect("/physio_appointments")


@physio_bp.route("/reject/<int:id>", endpoint="reject")
def reject(id):
    appt = Appointment.query.get(id)
    if appt:
        appt.status = "Rejected"
        db.session.commit()
    return redirect("/physio_appointments")
