from chalkline.collections import userData, leagueData
from werkzeug.security import check_password_hash, generate_password_hash
from chalkline.core import now, check_unique, _safe
from uuid import uuid4
from flask import session, render_template
from chalkline.core import mailer

class User:
    col = userData

    class Filter:
        @staticmethod
        def default():
            return {
                'group': None,
                'active': True
            }

        @staticmethod
        def parse(form) -> dict:
            filters = User.Filter.default()

            if form.get('filter_reset'):
                return filters

            if form.get('filter_group', 'None') != 'None':
                filters['group'] = form['filter_group']

            filters['active'] = form.get('filter_active', 'True') == 'True'
            
            return filters

    @staticmethod
    def safe(user):
        user = _safe(user)
        user['firstLast'] = user['firstName'][0] + '. ' + user['lastName']
        user['fullName'] = user['firstName'] + ' ' + user['lastName']
        
        return user
    
    @staticmethod
    def view(user):
        user = User.safe(user)
        if user['preferences']['hide_email']:
            user['email'] = None
        if user['preferences']['hide_phone']:
            user['phone'] = None

        return user
    
    @staticmethod
    def get(res, add_criteria, filters=Filter.default()):
        criteria = [add_criteria]

        if filters.get('group') is not None:
            criteria.append({f'groups.{res['league']['leagueId']}': {'$in': [filters['group']]}})

        if filters['active']:
            criteria.append({'active': True})

        users = User.col.find({'$and': criteria}).sort('lastName', 1)
        return [User.safe(u) for u in users]

    @staticmethod
    def get_user(userId=None, email=None, view=False):
        if not(userId or email):
            raise ValueError('UserId or Email must be provided')
        elif userId:
            user = User.col.find_one({'userId': userId})
        else:
            user = User.col.find_one({'email': email})

        if user:
            if view:
                return User.view(user)
            else:
                return User.safe(user)
        else:
            return None
    
    @staticmethod
    def authenticate(email_or_userId, pword):
        user = User.get_user(email=email_or_userId) or User.get_user(userId=email_or_userId)
        if user:
            if check_password_hash(user['pword'], pword):
                return user
        return None
    
    @staticmethod
    def mark_active(user):
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$set': {'active': True}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def create_pword(pword):
        return generate_password_hash(pword)
    
    @staticmethod
    def set_password(user, pword):
        new_pword = User.create_pword(pword)
        User.col.update_one({'userId': user['userId']}, {'$set': {'pword': new_pword}, '$unset': {'auth.pword_reset': 0}})
    
    @staticmethod
    def reset_password(user):
        uuid = str(uuid4())
        user = User.col.find_one_and_update({'userId': user['userId'], 'auth.pword_reset': None}, {'$set': {'auth.pword_reset': uuid}})
        if user:
            return uuid
        else:
            raise PermissionError('Password reset has already been sent. Check your email.')

    @staticmethod
    def get_calendar(user):
        uuid = str(uuid4())
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$set': {'auth.calendar': uuid}}, return_document=True)
        return User.safe(user)

    @staticmethod
    def clean_phone(n: str):
        n = n.replace('-', '').replace('(', '').replace(')', '').replace('+', '')
        return format(int(n[:-1]), ",").replace(",", "-") + n[-1]
    
    @staticmethod
    def create(form, league):
        user = {
            'userId': check_unique(User, 'userId', form['userId']),
            'email': check_unique(User, 'email', form['email']),
            'phone': check_unique(User, 'phone', User.clean_phone(form['phone'])),
            'pword': User.create_pword(form['pword']),
            'firstName': form['firstName'],
            'lastName': form['lastName'],
            'leagues': [form['league']],
            'groups': {},
            'permissions': {
                form['league']: []
            },
            'teams': [],
            'auth': {},
            'preferences': {
                'hide_email': False,
                'hide_phone': False,
                'email_nots': True
            },
            'active': True,
            'approved': False,
            'created': now(),
            'last_login': None
        }
        User.authorize_groups(user, league, form)

        _id = User.col.insert_one(user).inserted_id
        user['_id'] = _id

        return User.safe(user, abbr=league['abbr'])

    @staticmethod
    def set_last_login(user, dt=None):
        if not dt:
            dt = now()
        User.col.update_one({'userId': user['userId']}, {'$set': {'last_login': dt}})

    @staticmethod
    def remove_team(user, teamId):
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$pull': {'teams': teamId}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def add_team(user, teamId):
        user = User.col.find_one_and_update({'userId': user['userId'], 'teams': {'$nin': [teamId]}}, {'$push': {'teams': teamId}}, return_document=True)
        if not user:
            raise ValueError('Team already added.')
        
        return User.safe(user)
    
    @staticmethod
    def update_profile(user, form):
        user = User.col.find_one_and_update(
            {'userId': user['userId']}, 
            {'$set': {
                'firstName': form['firstName'].strip().title(),
                'lastName': form['lastName'].strip().title(),
                'phone': User.clean_phone(form['phone']),
                'preferences.hide_email': form.get('hide_email', False) == 'on',
                'preferences.hide_phone': form.get('hide_phone', False) == 'on',
                'preferences.email_nots': form.get('email_nots', False) == 'on'
            }}, return_document=True
        )
        return User.safe(user)
    
    @staticmethod
    def authorize_groups(user, league, form):
        if 'role-coach' in form:
            assert league['auth']['coach_code'] == form.get('coach_code'), "Error: League Coach Code is invalid."
            user['groups'][league['leagueId']].append('coach')
        if 'role-parent' in form:
            user['groups'][league['leagueId']].append('parent')
        if 'role-umpire' in form:
            assert league['auth']['umpire_code'] == form.get('umpire_code'), "Error: League Umpire Code is invalid."
            user['groups'][league['leagueId']].append('umpire')
        if 'role-director' in form:
            assert league['auth']['director_code'] == form.get('director_code'), "Error: League Director Code is invalid."
            user['groups'][league['leagueId']].append('director')

        return user['groups']
    
    @staticmethod
    def add_league(user, league, form):
        groups = User.authorize_groups(user, league, form)
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$push': {'leagues': league['leagueId']}, '$set': {'groups': groups}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def remove_league(userId, leagueId):
        user = User.col.find_one_and_update({'userId': userId}, {'$pull': {'leagues': leagueId}}, return_document=True)
        return User.safe(user)

    @staticmethod
    def filter_for(user_list, userId):
        for u in user_list:
            if u['userId'] == userId:
                return u
        return None
    
    @staticmethod
    def find_groups(league, groups: list):
        users = User.col.find({'leagues': {'$in': [league['leagueId']]}, f'groups.{league['leagueId']}': {'$in': groups}, 'active': True})
        return [User.safe(u) for u in users]
    
    @staticmethod
    def generate_permissions(league):
        perms = [
            'umpire_add',
            'umpire_remove',
            'coach_add',
            'coach_remove',
        ]

        for age in league['age_groups']:
            perms.append(f"umpire_Plate_{age}")
            perms.append(f"umpire_Field_{age}")

        return perms
    
    @staticmethod
    def get_all_groups():
        return [
            'umpire',
            'coach',
            'parent',
            'director',
            'admin'
        ]
    
    @staticmethod
    def check_permissions_to_add(position, user):
        leagueId = session['league']['leagueId']
        for perm in position['permissions']:
                    if perm not in user['permissions'][leagueId]:
                        print(perm)
                        return False
        return True

    @staticmethod
    def request_sub(user, event, pos, subId):
        substitute = User.get_user(userId=subId)

        if not User.check_permissions_to_add(event['umpires'][pos], substitute):
            return "This user does not have permission to take this position."
        
        h = str(uuid4())
        User.col.update_one({'userId': user['userId']}, {"$set": {f"auth.sub_{event['_id']}": h}})
        
        msg = mailer.ChalklineEmail(
            subject=f"Substitue Request from {user['firstLast']}",
            recipients=[substitute['email']],
            html=render_template("emails/substitute-req.html", user=user, event=event, pos=pos, auth=h)
        )
        mailer.sendMail(msg)
        return f"Substitute request sent to {substitute['firstLast']}"