from chalkline.collections import userData
from werkzeug.security import check_password_hash, generate_password_hash
from chalkline.core import now, check_unique, _safe
from uuid import uuid4

class User:
    col = userData

    @staticmethod
    def safe(user):
        user = _safe(user)
        user['firstLast'] = user['firstName'][0] + '. ' + user['lastName']
        return user

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

        if 'role-coach' in form:
            assert league['auth']['coach_code'] == form.get('coach_code'), "Error: League Coach Code is invalid."
            user['groups'].append('coach')
        if 'role-parent' in form:
            user['groups'].append('parent')
        if 'role-umpire' in form:
            assert league['auth']['umpire_code'] == form.get('umpire_code'), "Error: League Umpire Code is invalid."
            user['groups'].append('umpire')
        if 'role-director' in form:
            assert league['auth']['director_code'] == form.get('director_code'), "Error: League Director Code is invalid."
            user['groups'].append('director')

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
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$push': {'teams': teamId}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def update_profile(user, form):
        user = User.col.find_one_and_update(
            {'userId': user['userId']}, 
            {'$set': {
                'firstName': form['firstName'].strip().title(),
                'lastName': form['lastName'].strip().title(),
                'phone': User.clean_phone(form['phone']),
                'preferences.hide_email': form.get('hide_email', False),
                'preferences.hide_phone': form.get('hide_phone', False),
                'preferences.email_nots': form.get('email_nots', False)
            }}, return_document=True
        )
        return User.safe(user)
    
    @staticmethod
    def add_league(user, leagueId):
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$push': {'leagues': leagueId}}, return_document=True)
        return User.safe(user)
    
    @staticmethod
    def remove_league(user, leagueId):
        user = User.col.find_one_and_update({'userId': user['userId']}, {'$pull': {'leagues': leagueId}}, return_document=True)
        return User.safe(user)

