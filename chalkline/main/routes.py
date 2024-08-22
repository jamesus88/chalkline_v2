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

    # Welcome back!
    if res['user']:
        if not res['user']['active']:
            league = League.get(res['league'])
            user = User.mark_active(res['user'])
            svr.login(user)
            res = svr.obj()
            res['popup'] = f"Welcome back {res['user']['firstName']}! Your account has been marked active for the {league['current_season']} season!"

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
            svr.login(user, request.form['league'])
            return redirect(url_for('main.home'))
        except (ValueError, AssertionError) as e:
            res['msg'] = e
    
    return render_template("main/create-account.html", res=res)
            
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
            league = request.form['removeLoc']
            user = User.remove_league(res['user']['userId'], league)
            svr.login(user)

        elif request.form.get('addLeague'):
            league = League.get(request.form['new_league'])
            user = User.add_league(res['user'], league, request.form)
            svr.login(user)

        elif request.form.get('admin-features'):
            assert 'admin' in res['user']['groups'], "You do not have permission to access these features."
            admin = request.form.get('admin-features') == "True"
            if not admin:
                session['flash'] = "Admin features turned OFF."
            else:
                session['flash'] = None
            svr.login(res['user'], admin=admin)

        elif request.form.get('location'):
            league = request.form.get('location')
            svr.login(res['user'], league=league)

        res = svr.obj()
        res['msg'] = msg

    res['user'] = Team.load_teams(res['user'], res['league'])
    all_teams = Team.get_league_teams(res['league'])
    all_leagues = League.get_all()
    return render_template('main/profile.html', res=res, all_teams=all_teams, all_leagues=all_leagues)
    

@main.route("/login", methods=['GET', 'POST'])
@main.route("/login/<next>", methods=['GET', 'POST'])
def login(next=None):
    mid = svr.unauthorized_only()
    if mid: return mid

    res = svr.obj()

    if request.method == 'POST':
        email = request.form['email']
        pword = request.form['pword']
        league = request.form['league']

        session['league'] = league
        user = User.authenticate(email, pword)
        if user:
            try:
                svr.login(user, league, 'admin' in user['groups'])
                User.set_last_login(user)
            except ValueError as e:
                res['msg'] = e
            else:
                if next:
                    return redirect(url_for(next))
                else:
                    return redirect(url_for('main.home'))
        else:
            res['msg'] = "Email or password is invalid. Please try again."
            del session['league']
    
    all_leagues = League.get_all()
    return render_template("main/login.html", res=res, all_leagues=all_leagues)

@main.route("/send-reset", methods=['GET', 'POST'])
def send_reset():
    mid = svr.unauthorized_only()
    if mid: return mid
    res = svr.obj()

    if request.method == 'POST':
        email = request.form['email']
        user = User.get_user(email=email)
        if user:
            try: 
                token = User.reset_password(user)
                html = render_template('emails/password-reset.html', res=res, email=user['email'], token=token)
                msg = mailer.ChalklineEmail(
                    subject="Password Reset: Chalkline Baseball",
                    recipients=[user['email']],
                    html=html
                )
                mailer.sendMail(msg)
            except PermissionError as e:
                res['msg'] = e
    
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
        User.set_password(user, request.form['pword'])
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