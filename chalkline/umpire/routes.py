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
                Event.add_umpire(eventId, res['user'], pos)
            except (ValueError, PermissionError) as e:
                res['msg'] = e

    events = Event.get(res['league'])
    league = League.get(res['league'])
    return render_template("umpire/schedule.html", res=res, events=events, league=league)

@umpire.route('/assignments', methods=['GET', 'POST'])
def assignments():
    pass