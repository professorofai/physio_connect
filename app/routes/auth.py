import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.services.email_service import send_email_otp, send_registration_email
from app.services.otp_service import create_otp_verification, verify_otp

auth_bp = Blueprint("auth", __name__)


def render_otp_page(email):
    expires_at = session.get("otp_expires_at", 0)
    remaining_seconds = max(
        0,
        int(expires_at - datetime.now(timezone.utc).timestamp()),
    )
    return render_template(
        "verify_otp.html",
        email=email,
        action="register",
        otp_remaining_seconds=remaining_seconds,
    )


@auth_bp.post("/resend-otp")
def resend_otp():
    reg_data = session.get("reg_data")
    if not reg_data:
        return jsonify({"ok": False, "message": "Registration session expired."}), 400

    try:
        otp_code = create_otp_verification(reg_data["email"])
        if not send_email_otp(reg_data["email"], otp_code):
            return jsonify({"ok": False, "message": "Unable to send the verification email."}), 502
    except SQLAlchemyError:
        return jsonify({"ok": False, "message": "Unable to create a verification code."}), 500

    expiration_seconds = current_app.config.get("OTP_EXPIRATION_SECONDS", 150)
    session["otp_expires_at"] = datetime.now(timezone.utc).timestamp() + expiration_seconds
    return jsonify({
        "ok": True,
        "message": "A new verification code was sent.",
        "expires_in": expiration_seconds,
    })


@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        step = request.form.get("step", "1")

        if step == "1":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "patient")

            if not all([name, email, password]) or role not in {"patient", "physiotherapist"}:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            try:
                existing_user = User.query.filter(
                    User.email == email
                ).first()
            except SQLAlchemyError:
                db.session.rollback()
                flash("Unable to check account availability. Please try again.", "danger")
                return render_template("register.html")
            if existing_user:
                flash("User with this email or phone number already exists.", "danger")
                return render_template("register.html")

            session["reg_data"] = {
                "name": name,
                "email": email,
                "phone_number": None,
                "city": None,
                "age": None,
                "password": password,
                "role": role,
            }

            try:
                otp_code = create_otp_verification(email)
            except SQLAlchemyError:
                flash("Unable to create a verification code. Please try again.", "danger")
                return render_template("register.html")
            email_sent = send_email_otp(email, otp_code)
            expiration_seconds = current_app.config.get("OTP_EXPIRATION_SECONDS", 150)
            session["otp_expires_at"] = datetime.now(timezone.utc).timestamp() + expiration_seconds

            if not email_sent:
                print(f"[DEBUG OTP]: {otp_code}")
                flash("Email failed, but OTP printed in terminal (dev mode).", "warning")
            else:
                flash("Verification code sent to your email. Please enter it below.", "info")

            return render_otp_page(email)

        elif step == "2":
            email = request.form.get("email", "").strip().lower()
            otp_code = re.sub(r"\D", "", request.form.get("otp_code", ""))

            reg_data = session.get("reg_data")
            if not reg_data:
                flash("Session expired. Please register again.", "danger")
                return redirect("/register")

            try:
                otp_valid = verify_otp(email, otp_code, commit=False)
            except SQLAlchemyError:
                flash("Unable to verify the code. Please try again.", "danger")
                return render_otp_page(email)

            if not otp_valid:
                flash("Invalid or expired verification code.", "danger")
                return render_otp_page(email)

            new_user = User(
                name=reg_data["name"],
                email=reg_data["email"],
                phone_number=reg_data["phone_number"],
                city=reg_data["city"],
                age=reg_data["age"],
                password=generate_password_hash(reg_data["password"]),
                role=reg_data["role"],
                is_verified=True,
            )

            try:
                db.session.add(new_user)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                flash("An account with this email or phone number already exists.", "danger")
                return render_otp_page(email)

            session.pop("reg_data", None)
            session.pop("otp_expires_at", None)

            email_sent = send_registration_email(reg_data["email"], reg_data["name"])
            if not email_sent:
                flash("Registration successful, but confirmation email was not sent.", "warning")
            else:
                flash("Registration successful! Welcome to Physio Connect.", "success")

            session["user_id"] = new_user.id
            session["user_email"] = new_user.email
            session["user_role"] = new_user.role

            return redirect(f"/dashboard/{new_user.id}")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        try:
            user = User.query.filter_by(email=email).first()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Unable to access your account. Please try again.", "danger")
            return render_template("login.html")

        if not user or not user.password:
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        if not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_role"] = user.role

        flash("Login successful! Welcome back.", "success")
        return redirect(f"/dashboard/{user.id}")

    return render_template("login.html")


@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    return redirect("/login")
