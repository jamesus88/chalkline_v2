from flask import redirect, url_for, session, Blueprint, render_template, request
from chalkline import db, get_events
from chalkline import server as srv
from werkzeug.security import generate_password_hash
import os
invite = Blueprint('invite', __name__)

@invite.route('/add-team/<teamId>')
def add_team(teamId=None):
    print(teamId)
    if not teamId:
        return redirect(url_for('main.home'))
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    if 'coach' in user['role'] or 'parent' in user['role']:
        response = db.addTeamToUser(user, teamId)
        if type(response) != str:
            user = response
            session['user'] = user
        
    return redirect(url_for('main.profile'))

@invite.route("/reset/<email>/<token>", methods=['GET', 'POST'])
def password_reset(email=None, token=None):
    if email is None or token is None:
        return redirect(url_for('main.home'))
    
    user = db.userData.find_one({'email': email})
    if user is None:
        return redirect(url_for('main.home'))
    elif 'reset_token' not in user:
        return redirect(url_for('main.home'))
    elif token != user['reset_token']:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        pword = generate_password_hash(request.form['pword'])
        db.userData.update_one({'email': email}, {'$set': {'pword': pword}, '$unset': {'reset_token': ''}})
        msg = "Your password has been updated."
    
    return render_template("main/reset-password.html", email=user['email'], msg=msg, user=None)
    
@invite.route('/daily-reminders', methods=['GET', 'POST'])
def daily_reminders():
    print('Daily Reminder Job Attempted...')
    
    if request.args.get('chalkline_auth') == os.environ.get('CHALKLINE_AUTH') and request.method == 'POST':
        today = srv.todaysDate
        eventFilter = get_events.EventFilter()
        eventList = get_events.getEventList(eventFilter, {'eventDate': {'$gte': today(), '$lte': today(17)}}, safe=False)
        userList = db.getUserList()
        
        msg, code = srv.sendReminders(eventList, userList)
        
        print('Daily Reminder Job executed.')
        return msg, code
    else:
        raise PermissionError('PermissionError: Resource is Forbidden.')