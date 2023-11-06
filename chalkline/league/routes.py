from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
league = Blueprint('league', __name__)

@league.route('/master-schedule', methods=['GET', 'POST'])
def master_schedule():
    user = srv.getUser()
    
    eventFilter = get_events.EventFilter()
    allTeams = db.getTeams()
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)

    eventList = get_events.getEventList(eventFilter)
    
    return render_template('league/master-schedule.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, allTeams=allTeams)