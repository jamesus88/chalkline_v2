from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.team import Team
from chalkline.core.user import User
from chalkline.core.events import Event

teams = Blueprint('teams', __name__)


@teams.route('/schedule', methods=['GET', 'POST'])
def schedule():
    mw = svr.authorized_only(['coach', 'parent'])
    if mw: return mw

    res = svr.obj()
    print(res['user']['teams'])
    Team.load_teams(res['user'], res['league'])
    print(res['user']['teams'])

    if len(res['user']['teams']) < 1:
        return redirect(url_for('main.profile'))

    events = Event.get(res['league'], user=res['user'])
    print(res['user']['teams'])

    return render_template("teams/schedule.html", res=res, events=events)

@teams.route("/info", methods=['GET', 'POST'])
def info():
    pass
    
@teams.route("/rentals", methods=['GET', 'POST'])
def rentals():
    pass