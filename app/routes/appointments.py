from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)

from app.extensions import db
from app.models import Appointment, PhysioProfile
from app.services.appointment_service import AppointmentService

appointments_bp = Blueprint("appointments", __name__)


@appointments_bp.route("/book/<int:physio_id>", methods=["GET", "POST"])
def book(physio_id):

    if "user_id" not in session:
        return redirect("/login")

    physio = PhysioProfile.query.get_or_404(physio_id)

    if request.method == "POST":

        appointment_date = request.form.get("date")
        appointment_time = request.form.get("time")

        if not appointment_date:
            flash("Please select an appointment date.", "danger")
            return redirect(request.url)

        if not appointment_time:
            flash("Please select an appointment time.", "danger")
            return redirect(request.url)

        try:
            selected_date = datetime.strptime(
                appointment_date,
                "%Y-%m-%d",
            ).date()
            selected_time = datetime.strptime(
                appointment_time,
                "%H:%M",
            ).time()

        except ValueError:

            flash("Invalid appointment date or time.", "danger")
            return redirect(request.url)

        # Backend duplicate protection
        if not AppointmentService.is_slot_available(
            physio.id,
            selected_date,
            selected_time,
        ):

            flash(
                "This appointment slot has already been booked. Please choose another slot.",
                "danger",
            )

            return redirect(request.url)

        appointment = Appointment(
            patient_id=session["user_id"],
            physio_id=physio.id,
            appointment_date=selected_date,
            appointment_time=selected_time,
        )

        db.session.add(appointment)
        db.session.commit()

        return render_template(
            "booking_confirmation.html",
            physio_name=physio.clinic_name,
            date=selected_date.strftime("%Y-%m-%d"),
            time=selected_time.strftime("%I:%M %p"),
            status="Pending",
        )

    return render_template(
        "book.html",
        physio=physio,
        today=datetime.today().strftime("%Y-%m-%d"),
        time_slots=AppointmentService.generate_time_slots(),
    )


@appointments_bp.route(
    "/api/appointments/available-slots",
    methods=["GET"],
)
def available_slots():

    physio_id = request.args.get("physio_id", type=int)
    appointment_date = request.args.get("date")

    if not physio_id or not appointment_date:
        return jsonify([])

    slots = AppointmentService.get_available_slots(
        physio_id,
        appointment_date,
    )

    return jsonify(slots)