from flask import render_template, redirect, url_for, session, request, Blueprint
from chalkline import db, send_mail
from chalkline import server as srv
main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)
    print(srv.todaysDate())
    return render_template("main/home.html", user=user, sobj=sobj)

@main.route("/signup", methods=["GET", "POST"])
def signup():
    user = srv.getUser()
    msg = ''
    
    if user is not None:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        response = db.createUser(request.form)
        if response['error']:
            msg = response['error']
        else:
            user = db.saveUser(response['newUser'])
            user = db.appendPermissions(user)
            session['user'] = user
            session['location'] = user['location'][0]
            
            html = render_template("emails/account-created.html", user=user)
            msg = send_mail.ChalklineEmail(subject="Chalkline Account Created!", html=html, recipients=[user['email']])
            send_mail.sendMail(msg)
            print(f"New User: {user['userId']}")
            return redirect(url_for('main.profile'))
    sobj=srv.getSessionObj(session, msg=msg)
    return render_template("main/create-account.html", user=user, sobj=sobj)
            
@main.route("/profile", methods=['GET', 'POST'])
def profile():
    user = srv.getUser()
    if user is None:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        
        if request.form.get('updateProfile'):
            user = db.updateProfile(user['userId'], request.form)
            session['user'] = user
            msg = 'Profile Updated'

        elif request.form.get('getCalendar'):
            user = db.addCalendarCode(user['userId'])
            session['user'] = user
            msg = 'Calendar Link Created!'
        
        elif request.form.get('logout'):
            srv.logout()
            return redirect(url_for('main.home'))
        
        elif request.form.get('removeTeam'):
            teamCode = request.form['removeTeam']
            user = db.removeTeamFromUser(user, teamCode)
            session['user'] = user
            msg = f'Removed {teamCode} from your teams'
        
        elif request.form.get('addTeam'):
            teamCode = request.form['newTeam'].upper()
            response = db.addTeamToUser(user, teamCode)
            if type(response) == str:
                msg = response
            else:
                user = response
                session['user'] = user
                msg = f'Added {teamCode} to your teams'
        
        elif request.form.get('admin-features'):
            if not session['admin']: 
                raise PermissionError('PermissionError: Admin features required')
            
            if request.form['admin-features'] == 'True':
                if 'admin' not in session['user']['role']:
                    user['role'].append('admin')
                    user.pop('msg', None)
                    session['user'] = user
                    msg = "Admin features are now on"
            else:
                user['role'].remove('admin')
                user['msg'] = "Admin features are currently disabled..."
                session['user'] = user
                msg = "Admin features are turned off" 
                
    teamsList = db.getTeamsFromUser(user['teams'])
    allTeams = db.getTeams(session['location'])
    
    if session['admin']:
        admin_features = 'admin' in session['user']['role']
    else:
        admin_features = None

    sobj=srv.getSessionObj(session, msg=msg)
    return render_template('main/profile.html', user=user, teamsList=list(teamsList), allTeams=allTeams, sobj=sobj, admin_features=admin_features)
    

@main.route("/login", methods=['GET', 'POST'])
def login():
    user = srv.getUser()
    if user is not None:
        return redirect(url_for('main.home'))
    
    msg = ''
    if request.method == 'POST':
        email = request.form['email'].lower()
        pword = request.form['pword']
        league = request.form['league'].strip().title()
        user = db.authenticate(email, pword)
        
        if user is None:
            msg = 'Invalid email and/or password.'
        else:
            session['user'] = user
            
            session['admin'] = 'admin' in user['role']

            if league in user['locations']:
                session['location'] = league
            elif len(user['locations']) > 0:
                session['location'] = user['locations'][0]
            else:
                session['location'] = None
            
            if 'next-page' in session:
                page = session['next-page']
            elif 'next-url' in session:
                return redirect(session['next-url'])
            else: page = 'main.home'
            return redirect(url_for(page))
    
    sobj=srv.getSessionObj(session, msg=msg)
    return render_template("main/login.html",user=user, sobj=sobj)

@main.route("/send-reset", methods=['GET', 'POST'])
def send_reset():
    user = srv.getUser()
    if user is not None:
        return redirect(url_for('main.home'))
    
    msg = ''
    
    if request.method == 'POST':
        email = request.form['email'].lower()
        if db.verifyEmail(email):
            msg = db.sendPasswordReset(email)
        else:
            msg = 'Invalid Email. Contact Administrator.'
    
    sobj=srv.getSessionObj(session, msg=msg)
    return render_template("main/send-reset.html", user=user, sobj=sobj)

@main.route("/logout")
def logout():
    srv.logout()
    return redirect(url_for('main.home'))

@main.route("/about")
def about():
    return redirect(url_for('main.home', _anchor='about'))

@main.get("/april-fools")
def april():
    user = srv.getUser()
    sobj=srv.getSessionObj(session)
    return render_template("main/april-fools.html", user=user, sobj=sobj)