from chalkline.collections import userData, leagueData
from werkzeug.security import check_password_hash, generate_password_hash
from chalkline.core import now, check_unique, _safe
from uuid import uuid4
from flask import session

class User:
    col = userData

    @staticmethod
    def safe(user, autopick_gps=True):
        user = _safe(user)
        user['firstLast'] = user['firstName'][0] + '. ' + user['lastName']
        user['fullName'] = user['firstName'] + ' ' + user['lastName']

        if session.get('league') and autopick_gps:
            abbr = leagueData.find_one({'leagueId': session['league']})['abbr']
            user['groups'] = [g.split('.')[1] for g in user['groups'] if abbr == g.split('.')[0]]
            user['permissions'] = [p.split('.')[1] for p in user['permissions'] if abbr == p.split('.')[0]]

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
    def get(criteria, autopick_gps=True):
        users = User.col.find(criteria)
        return [User.safe(u, autopick_gps) for u in users]

    @staticmethod
    def get_user(userId=None, email=None):
        if not(userId or email):
            raise ValueError('UserId or Email must be provided')
        elif userId:
            user = User.col.find_one({'userId': userId})
        else:
            user = User.col.find_one({'email': email})

        if user:
            return User.safe(user)
        else:
            return None
    
    @staticmethod
    def authenticate(email_or_userId, pword):
        user = User.get_user(email=email_or_userId) or User.get_user(userId=email_or_userId)
        if user:
            if check_password_hash(user['pword'], pword):
                User.col.update_one({'email': user['email']}, {'$set': {'last_login': now()}})
                return user
        return None
    
    @staticmethod
    def mark_active(user):
        User.col.update_one({'userId': user['userId']}, {'$set': {'active': True}})
    
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
            'teams': [],
            'permissions': [],
            'groups': [],
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
        abbr = league['abbr']
        if 'role-coach' in form:
            assert league['auth']['coach_code'] == form.get('coach_code'), "Error: League Coach Code is invalid."
            user['groups'].append(f'{abbr}.coach')
        if 'role-parent' in form:
            user['groups'].append(f'{abbr}.parent')
        if 'role-umpire' in form:
            assert league['auth']['umpire_code'] == form.get('umpire_code'), "Error: League Umpire Code is invalid."
            user['groups'].append(f'{abbr}.umpire')
        if 'role-director' in form:
            assert league['auth']['director_code'] == form.get('director_code'), "Error: League Director Code is invalid."
            user['groups'].append(f'{abbr}.director')

        _id = User.col.insert_one(user).inserted_id
        user['_id'] = _id

        return User.safe(user)

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
    def add_league(user, league, code):
        if 'director' in user['groups']:
            if code != league['auth']['director_code']:
                raise PermissionError('You are a director, so you must enter the director code for the new league.')

        user = User.col.find_one_and_update({'userId': user['userId']}, {'$push': {'leagues': league['leagueId']}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def remove_league(user, leagueId):
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$pull': {'leagues': leagueId}}, return_document=True)
        return User.safe(user)

    @staticmethod
    def filter_for(user_list, userId):
        for u in user_list:
            if u['userId'] == userId:
                return u
        return None
    
    @staticmethod
    def find_groups(leagueId, groups: list):
        users = User.col.find({'leagues': {'$in': [leagueId]}, 'groups': {'$in': groups}, 'active': True})
        return [User.safe(u) for u in users]
    
    @staticmethod
    def generate_permissions(league, positions):
        abbr = league['abbr']
        perms = [
            f'{abbr}.umpire_add',
            f'{abbr}.umpire_remove',
            f'{abbr}.coach_add',
            f'{abbr}.coach_remove',
        ]

        for age in league['age_groups']:
            perms.append(f"{abbr}.umpire_Plate_{age}")
            perms.append(f"{abbr}.umpire_Field_{age}")

        return perms
    
    @staticmethod
    def get_all_groups(league):
        abbr = league['abbr']
        return [
            f'{abbr}.umpire',
            f'{abbr}.coach',
            f'{abbr}.parent',
            f'{abbr}.director',
            f'{abbr}.admin'
        ]
