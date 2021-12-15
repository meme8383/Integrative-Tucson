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

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

def split_rows(query, columns):
    return [query[i:i + columns] for i in range(0, len(query), columns)]