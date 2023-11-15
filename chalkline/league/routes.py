from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
league = Blueprint('league', __name__)

@league.route('/master-schedule', methods=['GET', 'POST'])
def master_schedule():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.master_schedule'
        return redirect(url_for('main.login'))
    
    eventFilter = get_events.EventFilter()
    allTeams = db.getTeams()
    
    if request.method == 'POST':
        if request.form.get('updateFilter'):
            eventFilter.update(request.form)

    eventList = get_events.getEventList(eventFilter)
    
    return render_template('league/master-schedule.html', user=srv.safeUser(user),eventFilter=eventFilter.asdict(), eventList=eventList, allTeams=allTeams)

@league.route("/info", methods=['GET', 'POST'])
def info():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.info'
        return redirect(url_for('main.login'))
    
    return render_template("league/info.html", user=user)

@league.route("/status")
def status():
    user = srv.getUser()
    if user is None:
        session['next-page'] = 'league.status'
        return redirect(url_for('main.login'))
    
    venues = db.getVenues("Sarasota")
    return render_template("league/status.html", user=user, venues=venues)