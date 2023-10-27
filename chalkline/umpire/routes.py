from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
umpire = Blueprint('umpire', __name__)

@umpire.route('/')
def home():
    return "umpire home"

@umpire.route('/schedule', methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    
    eventFilter = get_events.EventFilter()
    
    if request.method == 'POST':
        
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
    
    eventList = get_events.getEventList(eventFilter)
    
    return render_template('umpire/schedule.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict())

@umpire.route('/assignments')
def assignments():
    return "assignments"