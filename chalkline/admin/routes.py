from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
admin = Blueprint('admin', __name__)

@admin.route("/events", methods=['GET','POST'])
def event_data():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.event_data'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    eventFilter = get_events.EventFilter()
    teamsList = db.getTeams()
    userList = db.getUserList()
    
    if request.method == 'POST':
        print(request.form)
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
            
        if request.form.get('updateEvent'):
            eventId = request.form['updateEvent']
            this_event = db.getEventInfo(eventId)
            form = {}
            for key, value in request.form.items():
                if f'_{eventId}' in key:
                    form[key.removesuffix(f"_{eventId}")] = value
            
            msg = db.updateEvent(this_event, form, userList)
            print(f"Event: {eventId} updated by {user['userId']}")
            
        elif request.form.get('deleteEvent'):
            eventId = request.form['deleteEvent']
            msg = db.deleteDevent(eventId)
            print(f"Event: {eventId} deleted by {user['userId']}")

    eventList = get_events.getEventList(eventFilter)
    
    return render_template('admin/event-data.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, teamsList=teamsList)

@admin.route("/add-event", methods=['GET', 'POST'])
def add_event():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'admin.add_event'
        return redirect(url_for('main.login'))
    if 'admin' not in user['role']:
        return redirect(url_for('main.home'))
    
    