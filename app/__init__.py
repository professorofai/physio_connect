import os

from flask import Flask

from config import Config
from app.extensions import db
from app.routes import auth_bp, patient_bp, physio_bp, appointments_bp, main_bp
from app.models import User, OTPVerification, PhysioProfile, Appointment
from app.utils.schema_migration import ensure_database_schema


def create_app():
    app = Flask(__name__, instance_relative_config=True, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    db.init_app(app)

    upload_dir = os.path.join(os.getcwd(), app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_dir, exist_ok=True)

    with app.app_context():
        ensure_database_schema()

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(physio_bp)
    app.register_blueprint(appointments_bp)

    aliases = {
        "home": ("/", app.view_functions["main.home"]),
        "service_detail": ("/services/<slug>", app.view_functions["main.service_detail"]),
        "register": ("/register", app.view_functions["auth.register"]),
        "login": ("/login", app.view_functions["auth.login"]),
        "logout": ("/logout", app.view_functions["auth.logout"]),
        "dashboard": ("/dashboard", app.view_functions["patient.dashboard"]),
        "physios": ("/physios", app.view_functions["patient.physios"]),
        "create_profile": ("/create_profile", app.view_functions["physio.create_profile"]),
        "physio_appointments": ("/physio_appointments", app.view_functions["physio.physio_appointments"]),
        "approve": ("/approve/<int:id>", app.view_functions["physio.approve"]),
        "reject": ("/reject/<int:id>", app.view_functions["physio.reject"]),
        "book": ("/book/<int:physio_id>", app.view_functions["appointments.book"]),
    }

    for endpoint, (rule, view_func) in aliases.items():
        app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)

    return app


app = create_app()
