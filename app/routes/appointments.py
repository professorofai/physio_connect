from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session

from app.extensions import db
from app.models import Appointment, PhysioProfile

appointments_bp = Blueprint("appointments", __name__)


@appointments_bp.route("/book/<int:physio_id>", methods=["GET", "POST"], endpoint="book")
def book(physio_id):
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        date = request.form.get("date")
        appointment = Appointment(
            patient_id=session["user_id"],
            physio_id=physio_id,
            appointment_date=date,
        )

        db.session.add(appointment)
        db.session.commit()

        physio = PhysioProfile.query.get(physio_id)
        return render_template(
            "booking_confirmation.html",
            date=date,
            physio_name=physio.clinic_name if physio else "Unknown",
            status="Pending",
        )

    return render_template(
        "book.html",
        physio=PhysioProfile.query.get(physio_id),
        today=datetime.now().strftime("%Y-%m-%d"),
    )
