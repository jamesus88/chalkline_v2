from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
docs = Blueprint('docs', __name__)

@docs.route("/")
def home():
    res = svr.obj()
    return render_template("docs/home.html", res=res)

@docs.route("/account-creation")
def account_creation():
    res = svr.obj()
    return render_template("docs/account-creation.html", res=res)

@docs.route("/profile")
def profile():
    res = svr.obj()
    return render_template("docs/profile.html", res=res)

@docs.route("/team-schedule")
def team_schedule():
    res = svr.obj()
    return render_template("docs/team-schedule.html", res=res)

@docs.route("/team-info")
def team_info():
    res = svr.obj()
    return render_template("docs/team-info.html", res=res)

@docs.route("/umpire-schedule")
def umpire_schedule():
    res = svr.obj()
    return render_template("docs/umpire-schedule.html", res=res)

@docs.route("/umpire-assignments")
def umpire_assignments():
    res = svr.obj()
    return render_template("docs/umpire-assignments.html", res=res)

@docs.route("/umpire-substitutions")
def umpire_substitutions():
    res = svr.obj()
    return render_template("docs/umpire-substitutions.html", res=res)

@docs.route("/master-schedule")
def master_schedule():
    res = svr.obj()
    return render_template("docs/master-schedule.html", res=res)

@docs.route("/league")
def league():
    res = svr.obj()
    return render_template("docs/league.html", res=res)


@docs.route("/lost-id")
def lost_id():
    res = svr.obj()
    return render_template("docs/lost-id.html", res=res)

@docs.route("/security")
def security():
    res = svr.obj()
    return render_template("docs/security.html", res=res)