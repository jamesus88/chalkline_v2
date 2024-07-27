from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.team import Team
from chalkline.core.events import Event

teams = Blueprint('teams', __name__)


@teams.route('/schedule', methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only(['coach', 'parent'])
    if mw: return mw

    res = svr.obj()
    Team.load_teams(res['user'], res['league'])

    if len(res['user']['teams']) < 1:
        return redirect(url_for('main.profile'))
    
    team = res['user']['teams'][0]
    
    if request.method == 'POST':
        if request.form.get('request'):
            pos, eventId = request.form['request'].split('_')
            Event.request_umpire(eventId, pos, res['user'])
            res['msg'] = "Umpire requested!"

        elif request.form.get('remove'):
            pos, eventId = request.form['remove'].split('_')
            try:
                Event.remove_request(eventId, pos)
            except ValueError as e:
                res['msg'] = e
            else:
                res['msg'] = 'Umpire request removed.'

        elif request.form.get('team'):
            team = request.form['team']

    events = Event.get(res['league'], team=team)
    Event.label_umpire_duties(events, team)

    return render_template("teams/schedule.html", res=res, events=events, team=team)

@teams.route("/info", methods=['GET', 'POST'])
def info():
    pass
    
@teams.route("/rentals", methods=['GET', 'POST'])
def rentals():
    pass