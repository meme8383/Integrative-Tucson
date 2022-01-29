import psycopg2
import os
import datetime

from flask import Flask, render_template, request
from flask_session import Session
from flask_mail import Mail, Message

from tempfile import mkdtemp

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Config email
CONTACT_EMAIL = "integrativetucson@gmail.com"
DEFAULT_EMAIL = os.environ["MAIL_DEFAULT_SENDER"]
app.config["MAIL_DEFAULT_SENDER"] = DEFAULT_EMAIL
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]
mail = Mail(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = mkdtemp()
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

# Connect database
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

@app.route("/")
def index():

    # Get practices
    cur.execute("""SELECT * FROM practices
                WHERE practices.id IN (SELECT practice_id FROM providers)
                ORDER BY id""")
    practices = cur.fetchall()

    # Split practices into rows
    rows = split_rows(practices, 2)

    return render_template("index.html", rows=rows)

@app.route("/patients")
def patients():
    return render_template("patients.html")

@app.route("/search")
def search():

    # Get filter, return all if none
    practice_id = request.args.get("practice")
    if practice_id:
        cur.execute("SELECT * FROM providers WHERE practice_id = %s", [practice_id])
        providers = cur.fetchall()
        cur.execute("SELECT name from practices WHERE id = %s", [practice_id])
        practice = cur.fetchone()[0]
    else:
        cur.execute("SELECT * FROM providers")
        providers = cur.fetchall()
        practice = None

    # Replace None with empty string
    conv = lambda i : i or ''
    providers = [[conv(j) for j in i] for i in providers]

    rows = split_rows(providers, 3)

    return render_template("practice.html", rows=rows, practice = practice)

@app.route("/providers")
def providers():
    return render_template("providers.html")
    
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        body = request.form.get("message")
        if not name or not email or not subject or not body:
            return render_template("contact.html"), 403
        

        message_body = f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {body}"
        message = Message("Your message has been sent!", body=message_body, recipients=[email])
        mail.send(message)

        message = Message(f"New message from: {name}", body=message_body, recipients=[CONTACT_EMAIL])
        mail.send(message)

        return render_template("success.html", message="Your response has been recorded!")

    else:
        return render_template("contact.html")

@app.route("/providers/request", methods=["GET", "POST"])
def request_submit():
    if request.method == "POST":
        print(request.form)
        # if len(request.form) == 8:
        #     email, practice_id, name, provider, address, phone, website, note = request.form.items()
        #     custom_practice = (None, None)
        # else:
        #     email, practice_id, custom_practice, name, provider, address, phone, website, note = request.form

        values = [int(request.form.get("practice")), request.form.get("name"), request.form.get("provider"), request.form.get("address"), 
        int(request.form.get("phone")) if request.form.get("phone") else None, request.form.get("website"), request.form.get("custom_practice"),
        request.form.get("email"), request.form.get("note"), datetime.datetime.now()]

        conv = lambda i : i or None
        clean_values = [conv(i) for i in values]

        try:
            cur.execute("""INSERT INTO requests (practice_id, name, provider, address, phone, website, custom_practice, email, note, submitted_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", clean_values)
            conn.commit()
        except:
            conn.rollback()
            raise

        message = Message("Request Received", body="We have received your request to be added. We will be in contact with you soon. Thank you for your interest.\n\nFrom AIHM Tucson Chapter Team",
                          recipients=[request.form.get("email")])
        mail.send(message)

        message = Message("New Request", body=str(clean_values), recipients=[CONTACT_EMAIL])
        mail.send(message)

        return render_template("success.html", message="Your request has been sent!")
    else:
        cur.execute("SELECT id, name FROM practices")
        practices = cur.fetchall()

        return render_template("request.html", practices=practices)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(503)
def page_unavailable(e):
    return render_template("503.html"), 503

def split_rows(query, columns):
    return [query[i:i + columns] for i in range(0, len(query), columns)]

# Custom filter
def phone(number):
    number = str(number)
    return f"({number[0:3]}) {number[3:6]}-{number[6:10]}"
app.jinja_env.filters["phone"] = phone