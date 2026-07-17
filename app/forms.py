from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import IntegerField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, Optional


class PatientProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=8, max=15)])
    city = StringField("City", validators=[DataRequired(), Length(min=2, max=100)])
    profile_picture = FileField("Profile Picture", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")])
    submit = SubmitField("Save Profile")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=6, max=80)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo("new_password", "Passwords must match")])
    submit = SubmitField("Change Password")


class PhysioProfileForm(FlaskForm):
    clinic_name = StringField("Clinic Name", validators=[DataRequired(), Length(min=2, max=200)])
    location = StringField("Clinic Location", validators=[DataRequired(), Length(min=2, max=200)])
    specialization = StringField("Specialization", validators=[DataRequired(), Length(min=2, max=200)])
    experience = IntegerField("Experience (years)", validators=[DataRequired(), NumberRange(min=0, max=60)])
    profile_picture = FileField("Profile Image", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png"], "Images only!")])
    certificates = FileField("Certificates", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "pdf", "doc", "docx"], "Allowed certificate files")])
    submit = SubmitField("Save Clinic Profile")
