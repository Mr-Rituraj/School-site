import os
import base64
import sqlite3
from datetime import datetime
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, g, session

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "school.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme123")

# Email notifications for new contact-form submissions, sent through the
# Gmail API (not raw SMTP, which Render's free tier blocks, and not a
# third-party relay, which Gmail's spam filters distrust when the "From"
# address is @gmail.com). Sending through Google's own API means the
# message is authenticated as coming from Google itself. See README for
# the one-time OAuth setup that produces these three values.
GMAIL_CLIENT_ID = os.environ.get("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN", "")
NOTIFY_EMAIL = "tetelisarasankardev@gmail.com"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Email notifications
# ---------------------------------------------------------------------------

def _get_gmail_access_token():
    """Exchange the long-lived refresh token for a short-lived access token.
    Refresh tokens don't expire under normal use, so this runs on every
    send rather than trying to cache the access token across requests."""
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "refresh_token": GMAIL_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_notification_email(name, email, reason, message):
    """Email the front office whenever the contact form is submitted, sent
    through the Gmail API so it's authenticated as coming from Google
    itself. Fails silently (but logs to console) so a broken email setup
    never blocks someone's message from being saved."""
    if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
        print("Email notification skipped: Gmail API credentials not set.", flush=True)
        return

    try:
        access_token = _get_gmail_access_token()

        mime_lines = [
            f"From: {NOTIFY_EMAIL}",
            f"To: {NOTIFY_EMAIL}",
            f"Reply-To: {email}",
            f"Subject: New website enquiry: {reason}",
            "Content-Type: text/plain; charset=utf-8",
            "",
            "New message submitted through the school website contact form.",
            "",
            f"Name: {name}",
            f"Email: {email}",
            f"Reason: {reason}",
            "",
            "Message:",
            message,
        ]
        raw_mime = "\r\n".join(mime_lines).encode("utf-8")
        raw_b64 = base64.urlsafe_b64encode(raw_mime).decode("utf-8")

        resp = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw_b64},
            timeout=10,
        )
        if resp.status_code >= 300:
            print(f"Email notification failed: {resp.status_code} {resp.text}", flush=True)
        else:
            print(f"Email notification sent: {resp.status_code} {resp.text}", flush=True)
    except Exception as exc:
        print(f"Email notification failed: {exc}", flush=True)


def init_db():
    """Create tables and seed a few notices the first time the app runs."""
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            posted_on TEXT NOT NULL
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            reason TEXT NOT NULL,
            message TEXT NOT NULL,
            submitted_on TEXT NOT NULL
        )
        """
    )
    count = db.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    if count == 0:
        seed = [
            ("New Session Begins", "Classes resume on Monday. Homeroom teachers will hand out updated timetables in period 1.", "2026-07-14"),
            ("Science Exhibition — Call for Entries", "Grades 6-10 can register a project with Mr. Saikia by Friday. Group entries welcome, max 3 students.", "2026-07-10"),
            ("Library Extended Hours", "The library now stays open until 5:30pm on weekdays for exam revision.", "2026-07-07"),
            ("Inter-House Football Trials", "Trials for the U-15 team are after school on the main field. Bring your own boots.", "2026-07-03"),
        ]
        db.executemany(
            "INSERT INTO notices (title, body, posted_on) VALUES (?, ?, ?)", seed
        )
        db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Static content (kept in code, not DB, since it changes rarely)
# ---------------------------------------------------------------------------

SCHOOL_NAME = "Sankardev Sishu Niketan, Tetelisara"
SCHOOL_SHORT = "SSN Tetelisara"
SCHOOL_MOTTO = "Swayameva Mrigendrata"  # from the school crest

ACHIEVEMENTS = [
    {"year": "2026", "title": "State-Level Bihu Utsav — 1st Place", "detail": "Our senior Bihu troupe represented the district and won first place at the state cultural meet."},
    {"year": "2025", "title": "District Science Exhibition — Best Innovation", "detail": "Grade 9 students won Best Innovation for a working model on solar-powered irrigation."},
    {"year": "2025", "title": "Inter-School Debate Championship", "detail": "Our senior team took the winner's trophy at the zonal inter-school debate competition."},
    {"year": "2024", "title": "State Athletics Meet — 3 Gold Medals", "detail": "Students brought home three gold medals across the 100m, long jump, and relay events."},
    {"year": "2024", "title": "Sishu Siksha Samiti Academic Excellence Award", "detail": "Recognised for the highest Class X board result improvement in the Umrongso education zone."},
]

GALLERY = [
    {"file": "annualday.svg", "caption": "Annual Day assembly in front of the school building"},
    {"file": "culturalday.svg", "caption": "Bihu performance at the cultural evening"},
    {"file": "sportsday.svg", "caption": "Track events on Sports Day"},
    {"file": "classroom.svg", "caption": "A regular classroom session"},
    {"file": "sciencelab.svg", "caption": "Students at work in the science lab"},
]

DEPARTMENTS = [
    {"name": "Sciences", "color": "#2F6F4E", "subjects": ["Biology", "Chemistry", "Physics", "Environmental Science"]},
    {"name": "Mathematics", "color": "#E8A33D", "subjects": ["Algebra", "Geometry", "Statistics", "Calculus (Grade 12)"]},
    {"name": "Humanities", "color": "#7A5C8E", "subjects": ["History", "Geography", "Civics", "Economics"]},
    {"name": "Languages", "color": "#C1573A", "subjects": ["Assamese", "English", "Hindi", "Sanskrit"]},
    {"name": "Arts & Design", "color": "#2E6E8E", "subjects": ["Studio Art", "Music", "Drama", "Digital Design"]},
    {"name": "Physical Education", "color": "#4B7B3F", "subjects": ["Team Sports", "Athletics", "Health Education"]},
]

FACULTY = [
    {"name": "Dr. Ranjit Bora", "role": "Principal", "dept": "Administration", "initials": "RB"},
    {"name": "Mrs. Minakshi Deka", "role": "Vice Principal, Academics", "dept": "Administration", "initials": "MD"},
    {"name": "Mr. Bhaskar Saikia", "role": "Head of Sciences", "dept": "Sciences", "initials": "BS"},
    {"name": "Mrs. Rupali Gogoi", "role": "Mathematics Teacher", "dept": "Mathematics", "initials": "RG"},
    {"name": "Mr. Dipankar Baruah", "role": "Biology Teacher", "dept": "Sciences", "initials": "DB"},
    {"name": "Mrs. Junmoni Das", "role": "History & Civics Teacher", "dept": "Humanities", "initials": "JD"},
    {"name": "Mr. Probin Hazarika", "role": "Head of Languages", "dept": "Languages", "initials": "PH"},
    {"name": "Mrs. Lakhi Kalita", "role": "Art & Cultural Studies Teacher", "dept": "Arts & Design", "initials": "LK"},
]

ADMISSIONS_STEPS = [
    {"step": 1, "title": "Submit the enquiry form", "detail": "Tell us about your child and preferred grade level. We reply within 3 working days."},
    {"step": 2, "title": "School tour & assessment", "detail": "Visit the campus and your child takes a short, friendly placement assessment — no heavy prep needed."},
    {"step": 3, "title": "Family interview", "detail": "A short conversation with our admissions team so we can understand what you're looking for."},
    {"step": 4, "title": "Offer & enrollment", "detail": "Successful applicants receive an offer letter and enrollment pack within a week."},
]

# A simplified bell schedule used to power the "live period" indicator.
# (hour, minute, label) marking when each period/break starts.
BELL_SCHEDULE = [
    (8, 0, "Period 1"),
    (8, 45, "Period 2"),
    (9, 30, "Break"),
    (9, 45, "Period 3"),
    (10, 30, "Period 4"),
    (11, 15, "Lunch"),
    (12, 0, "Period 5"),
    (12, 45, "Period 6"),
    (13, 30, "Day ends"),
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.context_processor
def inject_school_info():
    return {"school_name": SCHOOL_NAME, "school_short": SCHOOL_SHORT, "school_motto": SCHOOL_MOTTO}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    db = get_db()
    notices = db.execute(
        "SELECT * FROM notices ORDER BY posted_on DESC LIMIT 4"
    ).fetchall()
    return render_template(
        "index.html",
        notices=notices,
        bell_schedule=BELL_SCHEDULE,
        achievements=ACHIEVEMENTS,
        gallery=GALLERY,
    )


@app.route("/academics")
def academics():
    return render_template("academics.html", departments=DEPARTMENTS)


@app.route("/admissions")
def admissions():
    return render_template("admissions.html", steps=ADMISSIONS_STEPS)


@app.route("/faculty")
def faculty():
    return render_template("faculty.html", faculty=FACULTY)


@app.route("/notices")
def notices_page():
    db = get_db()
    notices = db.execute("SELECT * FROM notices ORDER BY posted_on DESC").fetchall()
    return render_template("notices.html", notices=notices)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        reason = request.form.get("reason", "General enquiry")
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in your name, email and message before sending.", "error")
            return redirect(url_for("contact"))

        db = get_db()
        db.execute(
            "INSERT INTO messages (name, email, reason, message, submitted_on) VALUES (?, ?, ?, ?, ?)",
            (name, email, reason, message, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        db.commit()
        send_notification_email(name, email, reason, message)
        flash("Thanks — your message has been sent to the front office. We'll reply within two working days.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["is_admin"] = True
            next_url = request.args.get("next") or url_for("admin_messages")
            return redirect(next_url)
        flash("Incorrect password.", "error")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    db = get_db()
    messages = db.execute(
        "SELECT * FROM messages ORDER BY submitted_on DESC"
    ).fetchall()
    return render_template("admin_messages.html", messages=messages)


# Initialize the database on import so it works both with `python app.py`
# and with a production server like `gunicorn app:app` (which never hits
# the __main__ block below).
init_db()

if __name__ == "__main__":
    app.run(debug=True)
