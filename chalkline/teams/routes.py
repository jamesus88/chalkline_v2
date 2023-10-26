from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db
from chalkline import server as srv
teams = Blueprint('teams', __name__)

@teams.route('/', methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.login'))
    elif 'coach' not in user['role'] and 'parent' not in user['role']:
        return redirect(url_for('main.home'))
    
    
    
    return render_template('teams/schedule.html', user=user)