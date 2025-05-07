from flask import Blueprint, request, abort, render_template, url_for, jsonify, redirect

from chalkline.core.user import User
from chalkline.core.calendar import Calendar
from chalkline.core.events import Event
from chalkline.core.league import League
from chalkline.core import now
from chalkline.core import server as svr
from chalkline.core import mailer
from chalkline import CHALKLINE_AUTH

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
    mw = svr.authorized_only("umpire", set_next_url=request.url)
    if mw: return mw

    res = svr.obj()

    req_user = User.col.find_one({f'auth.sub_{eventId}': auth})
    event = Event.find(eventId)

    if not (req_user and event): abort(404)

    req_user = User.safe(req_user)

    # we have the req user, current user, and event
    pos = None
    for p, ump in event['umpires'].items():
        if ump['user']:
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
            except (PermissionError, ValueError) as e:
                res['msg'] = e
            else:
                return redirect(url_for('main.home'))
            
        elif request.form.get('decline'):
            User.remove_sub_req(req_user, event)
            return redirect(url_for('main.home'))

    return render_template("umpire/substitute.html", res=res, req_user=req_user, event=event, pos=pos)

@invite.post("/daily-reminders")
def daily_reminders(chalkline_auth=None):
    if chalkline_auth != CHALKLINE_AUTH:
        raise PermissionError("Credentials failed")
    
    all_leagues = League.get_all()
    day_of_week = now().weekday()
    msgs = []

    for l in all_leagues:
        users = User.find_groups(l, ['umpire', 'coach', 'director', 'parent', 'admin'])

        for i in range(len(users)):
            if (i % 7) == day_of_week:
                if users[i]['preferences']['email_nots']:
                    msg = Event.create_reminder(l, users[i])
                    if msg: msgs.append(msg)

    mailer.sendBulkMail(msgs)

    print("Daily reminders sent!")
    print(f"({len(msgs)} sent)")

    User.col.update_many({'auth.pword_reset': {'$exists': True}}, {'$unset': {'auth.pword_reset': 0}})
    print("Password reset links marked invalid.")
    
    return jsonify("Success!")

@invite.route("/add-league/<leagueId>", methods=['GET', 'POST'])
def add_league(leagueId):
    mid = svr.authorized_only(set_next_url=request.url)
    if mid: return mid
    res = svr.obj()

    league = League.get(leagueId)

    if request.method == 'POST':
        user = User.add_league(res['user'], league, request.form)
        svr.login(user, league['leagueId'])
        return redirect(url_for('main.home'))

    res['loaded_codes'] = {}
    res['loaded_codes']['umpire'] = request.args.get('umpire-code', '')
    res['loaded_codes']['coach'] = request.args.get('coach-code', '')
    res['loaded_codes']['director'] = request.args.get('director-code', '')

    return render_template("main/add-league.html", res=res, league=league)