from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, get_events
from chalkline import server as srv
view_info = Blueprint('view_info', __name__)

@view_info.route("/event/<eventId>", methods=['GET', 'POST'])
def event(eventId):
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.login'))
    
    msg = ''
    userList = db.getUserList()
    teamsList = db.getTeams()
    
    if request.method == 'POST':
        if request.form.get('updateEvent'):
            msg = db.updateEvent(eventId, request.form, userList)
            print(f"Event: {eventId} updated by {user['userId']}")
    
    event = db.getEventInfo(eventId)
    
    if not event:
        return redirect(url_for('league.master_schedule'))
    else:
        event = srv.safeEvent(event, userList)
    
    return render_template("view_info/event.html", user=user, event=event, teamsList=teamsList, userList=userList, msg=msg)

@view_info.route("/user/<user_id>")
def user(user_id):
    return "user"