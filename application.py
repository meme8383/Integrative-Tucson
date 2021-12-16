import csv
import psycopg2
import os

from flask import Flask, render_template, request
from flask_session import Session
from flask_mail import Mail, Message

from tempfile import mkdtemp

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Config email
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
    cur.execute("SELECT * FROM practices ORDER BY id")
    practices = cur.fetchall()

    # Split practices into rows
    rows = split_rows(practices, 2)

    return render_template("index.html", rows=rows)

@app.route("/patients")
def patients():
    return render_template("patients.html")

@app.route("/practice/<int:practice_id>")
def practice(practice_id):
    
    # Get providers
    cur.execute("SELECT * FROM providers WHERE practice_id = %s", [practice_id])
    providers = cur.fetchall()

    # Replace None with empty string
    conv = lambda i : i or ''
    providers = [[conv(j) for j in i] for i in providers]

    return render_template("practice.html", providers=providers)

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

        message = Message(f"New message from: {name}", body=message_body, recipients=[DEFAULT_EMAIL])
        mail.send(message)

        return render_template("success.html")

    else:
        return render_template("contact.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

def split_rows(query, columns):
    return [query[i:i + columns] for i in range(0, len(query), columns)]

# Custom filter
def phone(number):
    number = str(number)
    return f"({number[0:3]}) {number[3:6]}-{number[6:10]}"
app.jinja_env.filters["phone"] = phone