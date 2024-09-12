from flask import Blueprint, request, abort, render_template, url_for, jsonify

from chalkline.core.user import User
from chalkline.core.calendar import Calendar
from chalkline.core.events import Event
from chalkline.core import server as svr
from chalkline.core import mailer

invite = Blueprint('invite', __name__) 
    
@invite.route("/calendar/<userId>/<code>")
def calendar(userId=None, code=None):
    if not (userId and code): return jsonify("Missing email or code.")
    user = User.get_user(userId=userId)
    if not user: return jsonify("User does not exist.")
    if user['auth'].get('calendar') != code: return jsonify("Invalid calendar code.")

    cal = Calendar.serve_calendar(user)
    return cal

@invite.route("/substitute/<eventId>/<auth>", methods=['GET', 'POST'])
def substitute(eventId, auth):
    mw = svr.authorized_only("umpire", request.url)
    if mw: return mw

    res = svr.obj()

    req_user = User.safe(User.col.find_one({f'auth.sub_{eventId}': auth}))
    event = Event.find(eventId)

    if not (req_user and event): abort(404)

    # we have the req user, current user, and event
    pos = None
    for p, ump in event['umpires'].items():
        if ump['user']['userId'] == req_user['userId']:
            pos = p

    if not pos: abort(404)

    if request.method == "POST":
        if request.form.get('accept'):
            try:
                Event.substitute(event, pos, res['user'])
                User.remove_sub_req(req_user, event)
                msg = mailer.ChalklineEmail(
                    subject="Substitute Request Fulfilled!",
                    html=render_template("emails/shift-fulfilled.html", replaced=res['user']['fullName'], event=event),
                    recipients=[req_user['email']]
                )
                mailer.sendMail(msg)
            except PermissionError as e:
                res['msg'] = e
            else:
                return render_template(url_for('main.home'))
            
        elif request.form.get('decline'):
            User.remove_sub_req(req_user, event)
            return render_template(url_for('main.home'))



    return render_template("umpire/substitute.html", res=res, req_user=req_user, event=event, pos=pos)

    