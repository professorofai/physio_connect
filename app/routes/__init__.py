from .auth import auth_bp
from .patient import patient_bp
from .physio import physio_bp
from .appointments import appointments_bp
from .main import main_bp

__all__ = [
    "auth_bp",
    "patient_bp",
    "physio_bp",
    "appointments_bp",
    "main_bp",
]