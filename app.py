import os

from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize flask app
app = Flask(__name__)

# Initialize database
db = SQL("sqlite:///database.db")

@app.route("/")
def index():
  return render_template("login.html")