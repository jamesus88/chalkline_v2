from flask import redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
invite = Blueprint('invite', __name__)

@invite.route('/add-team/<teamId>')
def add_team(teamId=None):
    if not teamId:
        return redirect(url_for('main.home'))
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'invite.add_team'
        return redirect(url_for('main.login'))
    if 'coach' in user['role'] or 'parent' in user['role']:
        db.addTeamToUser(user, teamId)
        
    return redirect(url_for('main.profile'))