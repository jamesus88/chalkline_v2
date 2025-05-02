from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.user import User
from chalkline.core.team import Team
from chalkline.core.league import League
from chalkline.core import mailer

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    res = svr.obj()
    return render_template("main/home.html", res=res)

@main.route("/signup", methods=["GET", "POST"])
def signup():
    mid = svr.unauthorized_only()
    if mid: return mid

    res = svr.obj()

    if request.method == 'POST':
        try:
            league = League.get(request.form['league'])
            user = User.create(request.form, league)
            svr.login(user, league['leagueId'], False)
            print('User created!')
            return redirect(url_for('main.home'))
        except (ValueError, AssertionError) as e:
            print(e)
            res['msg'] = e

    all_leagues = League.get_all()
    
    return render_template("main/create-account.html", res=res, all_leagues=all_leagues)
            
@main.route("/profile", methods=['GET', 'POST'])
def profile():
    mid = svr.authorized_only()
    if mid: return mid
    res = svr.obj()

    if request.method == 'POST':
        msg = ''
        if request.form.get('logout'):
            svr.logout()
            return redirect(url_for('main.home'))
        
        elif request.form.get('getCalendar'):
            user = User.get_calendar(res['user'])
            svr.login(user)

        elif request.form.get('removeTeam'):
            user = User.remove_team(res['user'], request.form['removeTeam'])
            svr.login(user)

        elif request.form.get('addTeam'):
            teamId = request.form['newTeam']
            try: user = User.add_team(res['user'], teamId)
            except ValueError as e: msg = e
            else:
                svr.login(user)

        elif request.form.get('updateProfile'):
            user = User.update_profile(res['user'], request.form)
            svr.login(user)

        elif request.form.get('removeLoc'):
            leagueId = request.form['removeLoc']
            user = User.remove_league(res['user']['userId'], leagueId)
            svr.login(user)

        elif request.form.get('addLeague'):
            league = League.get(request.form['new_league'])
            user = User.add_league(res['user'], league, request.form)
            svr.login(user)

        elif request.form.get('admin-features'):
            assert 'admin' in res['user']['groups'][res['league']['leagueId']], "You do not have permission to access these features."
            admin = request.form.get('admin-features') == "True"
            if not admin:
                session['flash'] = "Admin features turned OFF."
            else:
                session['flash'] = None
            svr.login(res['user'], admin=admin)

        elif request.form.get('location'):
            leagueId = request.form.get('location')
            svr.login(res['user'], leagueId=leagueId)

        res = svr.obj()
        res['msg'] = msg

    res['user'] = Team.load_teams(res['user'], res['league'])
    all_teams = Team.get_league_teams(res['league']['leagueId'])
    all_leagues = League.get_all()
    return render_template('main/profile.html', res=res, all_teams=all_teams, all_leagues=all_leagues)
    

@main.route("/login", methods=['GET', 'POST'])
@main.route("/login/<next>", methods=['GET', 'POST'])
def login(next=None):
    mid = svr.unauthorized_only()
    if mid: return mid

    res = svr.obj()
    ask_league = False

    if request.method == 'POST':
        email = request.form['email'].lower()
        pword = request.form['pword']
        leagueId = request.form.get('league')
        
        try:
            user = User.get_user(email=email) or User.get_user(userId=email)

            if len(user['leagues']) > 1 and not leagueId:
                res['pword_attempt'] = pword
                res['email_attempt'] = email
                ask_league = True
                return render_template("main/login.html", res=res, all_leagues=user['leagues'], ask_league=ask_league)
            elif len(user['leagues']) == 1:
                leagueId = user['leagues'][0]
            elif len(user['leagues']) == 0:
                raise PermissionError("You are not a part of any league. Join a league to login!")

            user = User.authenticate(user, pword, leagueId)
            try:
                svr.login(user, leagueId, 'admin' in user['groups'][leagueId])
                User.set_last_login(user)
            except ValueError as e:
                res['msg'] = e
            else:
                if session.get('next_url'):
                    return redirect(session['next_url'])
                elif next:
                    return redirect(url_for(next))
                else:
                    return redirect(url_for('main.home'))
        except (ValueError, PermissionError) as e:
            res['msg'] = e
    
    return render_template("main/login.html", res=res, ask_league=ask_league)

@main.route("/send-reset", methods=['GET', 'POST'])
def send_reset():
    mid = svr.unauthorized_only()
    if mid: return mid
    res = svr.obj()

    if request.method == 'POST':
        email = request.form['email'].lower()
        user = User.get_user(email=email)
        if user:
            try: 
                token = User.reset_password(user)
                html = render_template('emails/password-reset.html', res=res, email=user['email'], token=token, userId=user['userId'])
                msg = mailer.ChalklineEmail(
                    subject="Password Reset: Chalkline Baseball",
                    recipients=[user['email']],
                    html=html
                )
                mailer.sendMail(msg)
            except PermissionError as e:
                res['msg'] = e
            else:
                res['msg'] = "Sent! Check your email."
    
    return render_template("main/send-reset.html", res=res)

@main.route("/new-password", methods=['GET', 'POST'])
@main.route("/new-password/<userId>/<auth>", methods=['GET', 'POST'])
def new_password(userId=None, auth=None):
    res = svr.obj()
    if not res['user']:
        if not(userId and auth):
            raise PermissionError('Missing credentials.')
        else:
            user = User.get_user(userId=userId)
            if not user:
                raise PermissionError('Invalid credentials.')
            elif user['auth'].get('pword_reset') != auth:
                raise PermissionError('Invalid credentials.')
    else:
        user = res['user']

    if request.method == 'POST':
        if request.form['pword'].strip() != request.form['check'].strip():
            res['msg'] = "Those passwords don't match, try again."
        else:
            User.set_password(user, request.form['pword'].strip())
            svr.logout()
            res['msg'] = "Password reset successfully. Please login again."

    return render_template("main/reset-password.html", res=res, user=user)

@main.route("/logout")
def logout():
    svr.logout()
    return redirect(url_for('main.home'))

@main.route("/about")
def about():
    return redirect(url_for('main.home', _anchor='about'))