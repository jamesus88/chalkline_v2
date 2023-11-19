from flask import render_template, redirect, url_for, session, request, Blueprint
import chalkline.director.director_db as db
import chalkline.get_events as get_events
from chalkline import server as srv
from chalkline import db as master_db
director = Blueprint('director', __name__)

@director.route("/week", methods=['GET', 'POST'])
def week():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'director.schedule'
        return redirect(url_for('main.login'))
    elif 'board' not in user['role']:
        return redirect(url_for('main.home'))
    
    eventFilter = get_events.EventFilter()
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)
    
    userList = master_db.getUserList()
    eventList = get_events.getEventList(eventFilter, userList=userList, add_criteria={'eventType': 'Game', 'eventDate': {'$lte': srv.todaysDate(padding_hrs=7*24)}})
    
    
    return render_template('director/week.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict(), msg=msg)

@director.route("/schedule", methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'director.schedule'
        return redirect(url_for('main.login'))
    elif 'board' not in user['role']:
        return redirect(url_for('main.home'))
    
    userList = master_db.getUserList()
    hidePast = True
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['hidePast'] == 'False':
                hidePast = False
                
        if request.form.get('addDirector'):
            shiftId = request.form['addDirector']
            msg = db.addDirector(shiftId, user)
    
    
    shiftList = db.getShiftList(userList, hidePast=hidePast, user=None)
    
    return render_template("director/schedule.html", user=user, shiftList=shiftList, hidePast=hidePast, msg=msg)

@director.route("/shifts", methods=['GET', 'POST'])
def shifts():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'director.shifts'
        return redirect(url_for('main.login'))
    elif 'board' not in user['role']:
        return redirect(url_for('main.home'))
    
    userList = master_db.getUserList()
    hidePast = True
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['hidePast'] == 'False':
                hidePast = False
                
        if request.form.get('removeDirector'):
            shiftId = request.form['removeDirector']
            msg = db.removeDirector(shiftId, user)
    
    
    shiftList = db.getShiftList(userList, user=user, hidePast=hidePast)
    
    return render_template("director/shifts.html", user=user, shiftList=shiftList, hidePast=hidePast, msg=msg)