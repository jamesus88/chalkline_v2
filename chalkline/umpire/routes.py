from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.events import Event
from chalkline.core.league import League

umpire = Blueprint('umpire', __name__)

@umpire.route('/schedule', methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only('umpire')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('add_game'):
            eventId, pos = request.form['add_game'].split('_')
            try:
                res['msg'] = Event.add_umpire(eventId, res['user'], pos)
            except (ValueError, PermissionError) as e:
                res['msg'] = e

    events = Event.get(res['league'])
    league = League.get(res['league'])
    return render_template("umpire/schedule.html", res=res, events=events, league=league)

@umpire.route('/assignments', methods=['GET', 'POST'])
def assignments():
    mw = svr.authorized_only('umpire')
    if mw: return mw

    res = svr.obj()

    if request.method == 'POST':
        if request.form.get('substitute'):
            pos, eventId = request.form['substitute'].split('_')

        elif request.form.get('remove'):
            pos, eventId = request.form['remove'].split('_')
            try: 
                Event.remove_umpire(eventId, pos, res['user'])
            except ValueError as e:
                res['msg'] = e
            else:
                res['msg'] = "Game successfully removed!"


    events = Event.get(res['league'], res['user'], check_user_teams=False)
    league = League.get(res['league'])
    return render_template("umpire/assignments.html", res=res, events=events, league=league)