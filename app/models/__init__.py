from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "user"
    __table_args__ = (
        db.UniqueConstraint("email", name="uq_user_email"),
        db.UniqueConstraint("phone_number", name="uq_user_phone_number"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, index=True)
    phone_number = db.Column(db.String(15), nullable=False, index=True)
    city = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="patient")
    profile_picture = db.Column(db.String(200))
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    physio_profile = db.relationship(
        "PhysioProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    patient_appointments = db.relationship(
        "Appointment",
        foreign_keys="Appointment.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class OTPVerification(db.Model):
    __tablename__ = "otp_verification"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)

class PhysioProfile(db.Model):
    __tablename__ = "physio_profile"
    __table_args__ = (db.UniqueConstraint("user_id", name="uq_physio_profile_user"),)

    id = db.Column(db.Integer, primary_key=True)
    clinic_name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    specialization = db.Column(db.String(200), nullable=False)
    experience = db.Column(db.Integer, default=0)
    profile_picture = db.Column(db.String(200))
    certificates = db.Column(db.String(500))
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="physio_profile")
    appointments = db.relationship(
        "Appointment",
        back_populates="physio",
        cascade="all, delete-orphan",
    )


class Appointment(db.Model):
    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    physio_id = db.Column(
        db.Integer,
        db.ForeignKey("physio_profile.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False,
    )

    patient_note = db.Column(db.Text)
    physio_note = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    patient = db.relationship(
        "User",
        foreign_keys=[patient_id],
        back_populates="patient_appointments",
    )

    physio = db.relationship(
        "PhysioProfile",
        back_populates="appointments",
    )

    def __repr__(self):
        return (
            f"<Appointment "
            f"{self.appointment_date} "
            f"{self.appointment_time}>"
        )


__all__ = ["User", "OTPVerification", "PhysioProfile", "Appointment"]