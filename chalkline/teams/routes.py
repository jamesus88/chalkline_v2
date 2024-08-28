from flask import render_template, redirect, url_for, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.team import Team
from chalkline.core.events import Event, Filter
from chalkline.core.league import League

teams = Blueprint('teams', __name__)

@teams.route('/schedule', methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only(['coach', 'parent'])
    if mw: return mw

    res = svr.obj()
    Team.load_teams(res['user'], res['league'])
    filters = Filter.default()

    if len(res['user']['teams']) < 1:
        return redirect(url_for('main.profile'))
    
    team = res['user']['teams'][0]
    
    if request.method == 'POST':
        filters = Filter.parse(request.form)

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

    events = Event.get(res['league'], team=team, filters=filters)
    Event.label_umpire_duties(events, team)

    return render_template("teams/schedule.html", res=res, events=events, team=team, filters=filters)

@teams.route("/info", methods=['GET', 'POST'])
def info():
    mw = svr.authorized_only(['coach', 'parent'])
    if mw: return mw

    res = svr.obj()

    try: teamId = res['user']['teams'][0]
    except IndexError: return redirect(url_for('main.profile'))

    if request.method == 'POST':
        teamId = request.form['teamId']

    team = Team.get(teamId)
    Team.load_contacts(team)

    return render_template("teams/info.html", res=res, team=team)
    
@teams.route("/rentals", methods=['GET', 'POST'])
def rentals():
    pass