from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
docs = Blueprint('docs', __name__)

@docs.route("/")
def home():
    user = srv.getUser()
    return render_template("docs/home.html", user=user)

@docs.route("/account-creation")
def account_creation():
    user = srv.getUser()
    return render_template("docs/account-creation.html", user=user)
