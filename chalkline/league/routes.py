from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event, Filter
from chalkline.core.league import League


league = Blueprint('league', __name__)

@league.route('/master-schedule', methods=['GET', 'POST'])
def master_schedule():
    mw = svr.authorized_only()
    if mw: return mw

    res = svr.obj()

    events = Event.get(res['league'])
    league = League.get(res['league'])
    return render_template("league/master-schedule.html", res=res, events=events, league=league)

@league.route("/info", methods=['GET', 'POST'])
def info():
    pass

@league.route("/status")
def status():
    pass