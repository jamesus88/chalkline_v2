from chalkline.collections import userData
from werkzeug.security import check_password_hash, generate_password_hash
from chalkline.core import now, check_unique, _safe

class User:
    col = userData

    @staticmethod
    def safe(user):
        user = _safe(user)
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
    def authenticate(email, pword):
        user = User.get_user(email=email)
        if user:
            if check_password_hash(user['pword'], pword):
                User.col.update_one({'email': email}, {'$set': {'last_login': now()}})
                return user
        return None
    
    @staticmethod
    def create_pword(pword):
        return generate_password_hash(pword)
    
    @staticmethod
    def clean_phone(n):
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
        