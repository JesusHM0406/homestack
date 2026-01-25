from models import User, Category, Transaction, TypeEnum
from extensions import db
from werkzeug.security import generate_password_hash
from flask_login import login_user