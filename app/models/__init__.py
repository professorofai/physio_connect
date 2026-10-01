from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.UniqueConstraint("email", name="uq_user_email"),
        db.UniqueConstraint("phone_number", name="uq_user_phone_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient", index=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    physio_profile = db.relationship(
        "PhysioProfile",
        back_populates="user",
        uselist=False,
    )
    patient_appointments = db.relationship(
        "Appointment",
        foreign_keys="Appointment.patient_id",
        back_populates="patient",
    )


class OTPVerification(db.Model):
    __tablename__ = "otp_verifications"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)


class PhysioProfile(db.Model):
    __tablename__ = "physio_profiles"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_physio_profile_user"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )
    clinic_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    experience = db.Column(db.Integer, nullable=True)
    profile_picture = db.Column(db.String(200))
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="physio_profile")
    appointments = db.relationship(
        "Appointment",
        back_populates="physiotherapist",
    )


class Appointment(db.Model):
    __tablename__ = "appointments"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_appointments_status",
        ),
        db.UniqueConstraint(
            "physio_id",
            "appointment_date",
            "appointment_time",
            name="uq_appointments_physio_slot",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    physio_id = db.Column(
        db.Integer,
        db.ForeignKey("physio_profiles.id"),
        nullable=False,
        index=True,
    )

    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    patient = db.relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="patient_appointments",
    )

    physiotherapist = db.relationship(
        "PhysioProfile",
        back_populates="appointments",
    )

    @property
    def physio(self):
        return self.physiotherapist

    @physio.setter
    def physio(self, value):
        self.physiotherapist = value

    def __repr__(self):
        return (
            f"<Appointment "
            f"{self.appointment_date} "
            f"{self.appointment_time}>"
        )


__all__ = ["User", "OTPVerification", "PhysioProfile", "Appointment"]