import csv
import psycopg2
import os

from flask import Flask, render_template, request
from flask_session import Session

from tempfile import mkdtemp

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect database
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

@app.route("/")
def index():

    # Get practices
    practices = list(cur.execute("SELECT name, description, image FROM practices"))

    # Split practices into rows
    rows = [practices[i: i + 2] for i in range(0, len(practices), 2)]

    return render_template("index.html", rows=rows)

@app.route("/patients")
def patients():
    return render_template("patients.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404