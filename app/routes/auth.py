from flask import Blueprint, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.services.email_service import send_email_otp, send_registration_email
from app.services.otp_service import create_otp_verification, verify_otp

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")
def register():
    if request.method == "POST":
        step = request.form.get("step", "1")

        if step == "1":
            name = request.form.get("name")
            email = request.form.get("email")
            phone_number = request.form.get("phone_number")
            city = request.form.get("city")
            password = request.form.get("password")
            role = request.form.get("role")

            if not all([name, email, phone_number, city, password, role]):
                flash("All fields are required.", "danger")
                return render_template("register.html")

            existing_user = User.query.filter(
                (User.email == email) | (User.phone_number == phone_number)
            ).first()
            if existing_user:
                flash("User with this email or phone number already exists.", "danger")
                return render_template("register.html")

            session["reg_data"] = {
                "name": name,
                "email": email,
                "phone_number": phone_number,
                "city": city,
                "password": password,
                "role": role,
            }

            otp_code = create_otp_verification(email)
            email_sent = send_email_otp(email, otp_code)

            if not email_sent:
                print(f"[DEBUG OTP]: {otp_code}")
            flash("Email failed, but OTP printed in terminal (dev mode).", "warning")

            flash("Verification code sent to your email. Please enter it below.", "info")
            return render_template("verify_otp.html", email=email, action="register")

        elif step == "2":
            email = request.form.get("email")
            otp_code = request.form.get("otp_code")

            if not verify_otp(email, otp_code):
                flash("Invalid or expired verification code.", "danger")
                return render_template("verify_otp.html", email=email, action="register")

            reg_data = session.get("reg_data")

            if not reg_data:
                flash("Session expired. Please register again.", "danger")
                return redirect("/register")

            new_user = User(
                name=reg_data["name"],
                email=reg_data["email"],
                phone_number=reg_data["phone_number"],
                city=reg_data["city"],
                password=generate_password_hash(reg_data["password"]),
                role=reg_data["role"],
                is_verified=True,
            )

            db.session.add(new_user)
            db.session.commit()

            session.pop("reg_data", None)

            email_sent = send_registration_email(reg_data["email"], reg_data["name"])
            if not email_sent:
                flash("Registration successful, but confirmation email was not sent.", "warning")
            else:
                flash("Registration successful! Welcome to Physio Connect.", "success")

            session["user_id"] = new_user.id
            session["user_email"] = new_user.email
            session["user_role"] = new_user.role

            return redirect("/dashboard")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()

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
        return redirect("/dashboard")

    return render_template("login.html")


@auth_bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    return redirect("/login")
