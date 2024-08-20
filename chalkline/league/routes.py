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
    filters = Filter.default()

    if request.method == 'POST':
        filters = Filter.parse(request.form)

    events = Event.get(res['league'], filters=filters)
    league = League.get(res['league'])
    return render_template("league/master-schedule.html", res=res, events=events, league=league, filters=filters)

@league.route("/status")
def status():
    pass