from flask import Blueprint, abort, render_template

main_bp = Blueprint("main", __name__)

SERVICE_SLUGS = {
    "pain-relief": "Pain Relief Physiotherapy",
    "sports-injury": "Sports Injury Rehab",
    "online-consultation": "Online Consultation",
    "home-visit": "Home Visit Physio",
    "posture-correction": "Posture Correction",
    "ai-assessment": "AI Physio Assessment",
}


@main_bp.route("/", endpoint="home")
def home():
    return render_template("home.html")


@main_bp.route("/services/<slug>", endpoint="service_detail")
def service_detail(slug):
    title = SERVICE_SLUGS.get(slug)
    if not title:
        abort(404)
    return render_template(
        "service_placeholder.html",
        service_title=title,
        service_slug=slug,
    )
