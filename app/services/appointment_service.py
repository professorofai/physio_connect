from datetime import datetime, timedelta

from app.models import Appointment


class AppointmentService:
    """
    Handles all appointment scheduling business logic.
    """

    START_HOUR = 9
    END_HOUR = 18
    SLOT_DURATION = 30

    @classmethod
    def generate_time_slots(cls):
        """
        Generate all available clinic slots.

        Returns:
            ['09:00', '09:30', ..., '17:30']
        """

        slots = []

        current = datetime.strptime(
            f"{cls.START_HOUR:02d}:00",
            "%H:%M"
        )

        end = datetime.strptime(
            f"{cls.END_HOUR:02d}:00",
            "%H:%M"
        )

        while current < end:

            slots.append(current.strftime("%H:%M"))

            current += timedelta(
                minutes=cls.SLOT_DURATION
            )

        return slots

    @staticmethod
    def get_booked_slots(physio_id, appointment_date):
        """
        Return booked slots for a physiotherapist
        on a particular date.
        """

        appointments = Appointment.query.filter_by(
            physio_id=physio_id,
            appointment_date=appointment_date,
        ).all()

        booked = []

        for appointment in appointments:

            if appointment.appointment_time:

                booked.append(
                    appointment.appointment_time.strftime("%H:%M")
                )

        return booked

    @classmethod
    def get_available_slots(cls, physio_id, appointment_date):
        """
        Return slots still available.
        """

        all_slots = cls.generate_time_slots()

        booked = cls.get_booked_slots(
            physio_id,
            appointment_date,
        )

        return [
            slot
            for slot in all_slots
            if slot not in booked
        ]

    @staticmethod
    def is_slot_available(
        physio_id,
        appointment_date,
        appointment_time,
    ):
        """
        Backend duplicate booking protection.
        """

        appointment = Appointment.query.filter_by(
            physio_id=physio_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).first()

        return appointment is None