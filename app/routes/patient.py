import os
import time
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import ChangePasswordForm, PatientProfileForm, PhysioProfileForm
from app.models import Appointment, PhysioProfile, User

patient_bp = Blueprint("patient", __name__)


@patient_bp.route("/dashboard", endpoint="dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect("/login")

    if session["user_role"] == "physiotherapist":
        physio_profile = PhysioProfile.query.filter_by(user_id=session["user_id"]).first()
        return render_template(
            "physio_dashboard.html",
            email=session["user_email"],
            physio_profile=physio_profile,
        )

    elif session["user_role"] == "patient":
        return render_template(
            "patient_dashboard.html",
            email=session["user_email"],
        )

    return redirect("/login")


@patient_bp.route("/physios", endpoint="physios")
def physios():
    physio_list = PhysioProfile.query.all()
    return render_template("physios.html", physios=physio_list)


@patient_bp.route("/profile/manage", methods=["GET", "POST"], endpoint="profile_management")
def profile_management():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    if not user:
        return redirect("/login")

    patient_form = PatientProfileForm(obj=user)
    password_form = ChangePasswordForm()
    physio_form = PhysioProfileForm()
    profile = PhysioProfile.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        if patient_form.submit.data and patient_form.validate_on_submit():
            user.name = patient_form.name.data
            user.phone_number = patient_form.phone_number.data
            user.city = patient_form.city.data

            if patient_form.profile_picture.data:
                filename = secure_filename(patient_form.profile_picture.data.filename)
                filename = f"{int(time.time())}_{filename}"
                upload_dir = os.path.join(os.getcwd(), current_app.config["UPLOAD_FOLDER"])
                os.makedirs(upload_dir, exist_ok=True)
                patient_form.profile_picture.data.save(os.path.join(upload_dir, filename))
                user.profile_picture = filename

            db.session.commit()
            flash("Your profile was updated successfully.", "success")
            return redirect("/profile/manage")

        if password_form.submit.data and password_form.validate_on_submit():
            if not check_password_hash(user.password, password_form.current_password.data):
                flash("Current password is incorrect.", "danger")
            else:
                user.password = generate_password_hash(password_form.new_password.data)
                db.session.commit()
                flash("Your password was changed successfully.", "success")
            return redirect("/profile/manage")

        if physio_form.submit.data and physio_form.validate_on_submit() and user.role == "physiotherapist":
            if not profile:
                profile = PhysioProfile(user_id=user.id)
                db.session.add(profile)

            profile.clinic_name = physio_form.clinic_name.data
            profile.location = physio_form.location.data
            profile.specialization = physio_form.specialization.data
            profile.experience = physio_form.experience.data

            if physio_form.profile_picture.data:
                filename = secure_filename(physio_form.profile_picture.data.filename)
                filename = f"{int(time.time())}_profile_{filename}"
                upload_dir = os.path.join(os.getcwd(), current_app.config["UPLOAD_FOLDER"])
                os.makedirs(upload_dir, exist_ok=True)
                physio_form.profile_picture.data.save(os.path.join(upload_dir, filename))
                profile.profile_picture = filename

            if physio_form.certificates.data:
                cert_filename = secure_filename(physio_form.certificates.data.filename)
                cert_filename = f"{int(time.time())}_cert_{cert_filename}"
                upload_dir = os.path.join(os.getcwd(), current_app.config["UPLOAD_FOLDER"])
                os.makedirs(upload_dir, exist_ok=True)
                physio_form.certificates.data.save(os.path.join(upload_dir, cert_filename))
                existing = profile.certificates or ""
                profile.certificates = f"{existing};{cert_filename}".strip(";") if existing else cert_filename

            db.session.commit()
            flash("Physiotherapist profile updated successfully.", "success")
            return redirect("/profile/manage")

    return render_template(
        "profile_management.html",
        user=user,
        patient_form=patient_form,
        password_form=password_form,
        physio_form=physio_form,
        profile=profile,
        role=user.role,
    )
