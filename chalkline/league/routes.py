from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
from chalkline.director import director_db
league = Blueprint('league', __name__)

@league.route('/master-schedule', methods=['GET', 'POST'])
def master_schedule():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.master_schedule'
        return redirect(url_for('main.login'))
    
    eventFilter = get_events.EventFilter()
    allTeams = db.getTeams(session['location'])
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)

    eventList = get_events.getEventList(session['location'], eventFilter)

    sobj=srv.getSessionObj(session)
    
    return render_template('league/master-schedule.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, allTeams=allTeams, sobj=sobj)

@league.route("/info", methods=['GET', 'POST'])
def info():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.info'
        return redirect(url_for('main.login'))
    
    sobj=srv.getSessionObj(session)
    return render_template("league/info.html", user=user, sobj=sobj)

@league.route("/status")
def status():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.status'
        return redirect(url_for('main.login'))
    
    venues = db.getVenues(session['location'])
    userList = db.getUserList(session['location'])
    currentDirector = director_db.getDirector(userList)
    sobj=srv.getSessionObj(session)
    return render_template("league/status.html", user=user, venues=venues, currentDirector=currentDirector, sobj=sobj)