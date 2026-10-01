import os
import time
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.extensions import db
from app.forms import ChangePasswordForm, PatientProfileForm, PhysioProfileForm
from app.models import Appointment, PhysioProfile, User

patient_bp = Blueprint("patient", __name__)


@patient_bp.route("/dashboard", endpoint="dashboard")
@patient_bp.route("/dashboard/<int:user_id>", endpoint="personal_dashboard")
def dashboard(user_id=None):
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])
    if not user:
        session.clear()
        return redirect("/login")

    if user_id is None:
        return redirect(f"/dashboard/{user.id}")
    if user_id != user.id:
        abort(403)

    if user.role == "physiotherapist":
        physio_profile = PhysioProfile.query.filter_by(user_id=user.id).first()
        pending_appointments = []
        upcoming_appointments = []
        if physio_profile:
            pending_appointments = (
                Appointment.query.filter_by(
                    physio_id=physio_profile.id,
                    status="pending",
                )
                .order_by(Appointment.appointment_date, Appointment.appointment_time)
                .limit(5)
                .all()
            )
            upcoming_appointments = (
                Appointment.query.filter_by(
                    physio_id=physio_profile.id,
                    status="approved",
                )
                .filter(Appointment.appointment_date >= date.today())
                .order_by(Appointment.appointment_date, Appointment.appointment_time)
                .limit(5)
                .all()
            )
        return render_template(
            "physio_dashboard.html",
            email=user.email,
            physio_profile=physio_profile,
            pending_appointments=pending_appointments,
            upcoming_appointments=upcoming_appointments,
        )

    elif user.role == "patient":
        upcoming_appointments = (
            Appointment.query.filter_by(patient_id=user.id)
            .filter(Appointment.appointment_date >= date.today())
            .order_by(Appointment.appointment_date, Appointment.appointment_time)
            .limit(3)
            .all()
        )
        appointment_counts = {
            status: Appointment.query.filter_by(
                patient_id=user.id,
                status=status,
            ).count()
            for status in ("pending", "approved", "rejected")
        }
        return render_template(
            "patient_dashboard.html",
            email=user.email,
            user=user,
            upcoming_appointments=upcoming_appointments,
            appointment_counts=appointment_counts,
        )

    return redirect("/login")


@patient_bp.route("/physios", endpoint="physios")
def physios():
    physio_list = PhysioProfile.query.join(PhysioProfile.user).order_by(PhysioProfile.clinic_name).all()
    return render_template("physios.html", physios=physio_list)


@patient_bp.route("/patient_appointments", endpoint="patient_appointments")
def patient_appointments():
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])
    if not user or user.role != "patient":
        abort(403)

    appointments = (
        Appointment.query.filter_by(patient_id=user.id)
        .order_by(Appointment.appointment_date, Appointment.appointment_time)
        .all()
    )
    return render_template("patient_appointments.html", appointments=appointments)


@patient_bp.route("/profile/manage", methods=["GET", "POST"], endpoint="profile_management")
def profile_management():
    if "user_id" not in session:
        return redirect("/login")

    user = db.session.get(User, session["user_id"])
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

            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Unable to update your profile. Please try again.", "danger")
            else:
                flash("Your profile was updated successfully.", "success")
            return redirect("/profile/manage")

        if password_form.submit.data and password_form.validate_on_submit():
            if not check_password_hash(user.password, password_form.current_password.data):
                flash("Current password is incorrect.", "danger")
            else:
                user.password = generate_password_hash(password_form.new_password.data)
                try:
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    flash("Unable to change your password. Please try again.", "danger")
                else:
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

            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Unable to save your physiotherapist profile. Please try again.", "danger")
            else:
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
