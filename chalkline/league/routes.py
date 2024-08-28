from flask import render_template, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event, Filter
from chalkline.core.league import League, Venue


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
    return render_template("league/master-schedule.html", res=res, events=events, filters=filters)

@league.route("/status", methods=['GET', 'POST'])
def status():
    mw = svr.authorized_only()
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('updateStatus'):
            Venue.update_status(request.form['updateStatus'], request.form['status'])

    league = League.load_venues(res['league'])

    for v in league['venue_info']:
        v['director'] = Venue.find_director(v)

    return render_template("league/status.html", res=res)