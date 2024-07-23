from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline.core import server as svr
from chalkline.core.user import User
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
            league = League.get_league(request.form['league'])
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
        if request.form.get('logout'):
            svr.logout()
            return redirect(url_for('main.home'))
        

    return render_template('main/profile.html', res=res)
    

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

        user = User.authenticate(email, pword)
        if user:
            try:
                svr.login(user, league)
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
    
    return render_template("main/login.html", res=res)

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