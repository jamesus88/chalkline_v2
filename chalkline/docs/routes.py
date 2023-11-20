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

@docs.route("/profile")
def profile():
    user = srv.getUser()
    return render_template("docs/profile.html", user=user)

@docs.route("/team-schedule")
def team_schedule():
    user = srv.getUser()
    return render_template("docs/team-schedule.html", user=user)

@docs.route("/team-info")
def team_info():
    user = srv.getUser()
    return render_template("docs/team-info.html", user=user)

@docs.route("/umpire-schedule")
def umpire_schedule():
    user = srv.getUser()
    return render_template("docs/umpire-schedule.html", user=user)

@docs.route("/umpire-assignments")
def umpire_assignments():
    user = srv.getUser()
    return render_template("docs/umpire-assignments.html", user=user)

@docs.route("/master-schedule")
def master_schedule():
    user = srv.getUser()
    return render_template("docs/master-schedule.html", user=user)

@docs.route("/league")
def league():
    user = srv.getUser()
    return render_template("docs/league.html", user=user)


@docs.route("/lost-id")
def lost_id():
    user = srv.getUser()
    return render_template("docs/lost-id.html", user=user)

@docs.route("/security")
def security():
    user = srv.getUser()
    return render_template("docs/security.html", user=user)