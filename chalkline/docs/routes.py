from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
docs = Blueprint('docs', __name__)

@docs.route("/")
def home():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/home.html", user=user, sobj=sobj)

@docs.route("/account-creation")
def account_creation():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/account-creation.html", user=user, sobj=sobj)

@docs.route("/profile")
def profile():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/profile.html", user=user, sobj=sobj)

@docs.route("/team-schedule")
def team_schedule():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/team-schedule.html", user=user, sobj=sobj)

@docs.route("/team-info")
def team_info():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/team-info.html", user=user, sobj=sobj)

@docs.route("/umpire-schedule")
def umpire_schedule():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/umpire-schedule.html", user=user, sobj=sobj)

@docs.route("/umpire-assignments")
def umpire_assignments():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/umpire-assignments.html", user=user, sobj=sobj)

@docs.route("/umpire-substitutions")
def umpire_substitutions():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/umpire-substitutions.html", user=user, sobj=sobj)

@docs.route("/master-schedule")
def master_schedule():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/master-schedule.html", user=user, sobj=sobj)

@docs.route("/league")
def league():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/league.html", user=user, sobj=sobj)


@docs.route("/lost-id")
def lost_id():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/lost-id.html", user=user, sobj=sobj)

@docs.route("/security")
def security():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)

    return render_template("docs/security.html", user=user, sobj=sobj)