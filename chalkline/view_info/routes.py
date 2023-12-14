from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db
from chalkline import server as srv
view_info = Blueprint('view_info', __name__)

@view_info.route("/event/<eventId>", methods=['GET', 'POST'])
def event(eventId):
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    
    msg = ''
    userList = db.getUserList()
    teamsList = db.getTeams()
    
    if request.method == 'POST':
        if request.form.get('updateEvent'):
            print(f"Event: {eventId} updated by {user['userId']}")
            this_event = db.getEventInfo(eventId)
            msg = db.updateEvent(this_event, request.form, userList, editRules=True, editContacts=True)
    
    event = db.getEventInfo(eventId)
    
    if not event:
        return redirect(url_for('league.master_schedule'))
    else:
        event = srv.safeEvent(event, userList)
    
    return render_template("view_info/event.html", user=user, event=event, teamsList=teamsList, userList=userList, msg=msg)

@view_info.route("/user/<user_id>")
def user(user_id=None):
    user = srv.getUser()
    if user is None:
        session['next-url'] = request.path
        return redirect(url_for('main.login'))
    elif user_id is None:
        return redirect(url_for('main.home'))
    
    view_user = srv.safeUser(db.getUser(_id=user_id))
    
    return render_template("view_info/user.html", user=user, view_user=view_user)