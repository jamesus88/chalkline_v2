from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, send_mail
from chalkline import server as srv
from chalkline.core import server as svr
from chalkline.core.user import User
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    res = svr.obj()
    return render_template("main/home.html", res=res)

@main.route("/signup", methods=["GET", "POST"])
def signup():
    svr.unauthorized_only()
    res = svr.obj()

    if request.method == 'POST':
        try:
            user = User.create(request.form)
            svr.login(user, request.form['league'])
        except ValueError as e:
            res['msg'] = e
    
    return render_template("main/create-account.html", res=res)
            
@main.route("/profile", methods=['GET', 'POST'])
def profile():
    svr.authorized_only()
    res = svr.obj()
                
    return render_template('main/profile.html', res=res)
    

@main.route("/login", methods=['GET', 'POST'])
def login():
    svr.unauthorized_only()
    res = svr.obj()

    if request.method == 'POST':
        email = request.form['email']
        pword = request.form['pword']
        league = request.form['league']

        user = User.authenticate(email, pword)
        if user:
            try:
                svr.login(user, league)
            except ValueError as e:
                res['msg'] = e
        else:
            res['msg'] = "Email or password is invalid. Please try again."
    
    return render_template("main/login.html", res=res)

@main.route("/send-reset", methods=['GET', 'POST'])
def send_reset():
    svr.unauthorized_only()
    res = svr.obj()
    
    return render_template("main/send-reset.html", res=res)

@main.route("/logout")
def logout():
    svr.logout()
    return redirect(url_for('main.home'))

@main.route("/about")
def about():
    return redirect(url_for('main.home', _anchor='about'))