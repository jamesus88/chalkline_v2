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
    
    userList = master_db.getUserList(session['location'])
    eventList = get_events.getEventList(session['location'], eventFilter, userList=userList, add_criteria={'eventType': 'Game', 'eventDate': {'$lte': srv.todaysDate(padding_hrs=7*24)}})
    
    sobj=srv.getSessionObj(session, msg=msg)
    
    return render_template('director/week.html', user=srv.safeUser(user), eventList=eventList, eventFilter=eventFilter.asdict(), sobj=sobj)

@director.route("/schedule", methods=['GET', 'POST'])
def schedule():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'director.schedule'
        return redirect(url_for('main.login'))
    elif 'board' not in user['role']:
        return redirect(url_for('main.home'))
    
    userList = master_db.getUserList(session['location'])
    hidePast = True
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['hidePast'] == 'False':
                hidePast = False
                
        if request.form.get('addDirector'):
            shiftId = request.form['addDirector']
            msg = db.addDirector(shiftId, user)
    
    
    shiftList = db.getShiftList(session['location'], userList, hidePast=hidePast)
    sobj=srv.getSessionObj(session, msg=msg)
    
    return render_template("director/schedule.html", user=user, shiftList=shiftList, hidePast=hidePast, sobj=sobj)

@director.route("/shifts", methods=['GET', 'POST'])
def shifts():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'director.shifts'
        return redirect(url_for('main.login'))
    elif 'board' not in user['role']:
        return redirect(url_for('main.home'))
    
    userList = master_db.getUserList(session['location'])
    
    hidePast = True
    msg = ''
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            if request.form['hidePast'] == 'False':
                hidePast = False
                
        if request.form.get('removeDirector'):
            shiftId = request.form['removeDirector']
            msg = db.removeDirector(shiftId, user)
    
    
    shiftList = db.getShiftList(session['location'], userList, add_criteria={'director': user['userId']}, hidePast=hidePast)
    sobj=srv.getSessionObj(session, msg=msg)
    
    return render_template("director/shifts.html", user=user, shiftList=shiftList, hidePast=hidePast, sobj=sobj)