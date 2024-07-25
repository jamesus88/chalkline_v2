from chalkline.collections import eventData
from datetime import datetime
from chalkline.core import now, _safe, ObjectId
from chalkline.core.user import User

class Filter:
    @staticmethod
    def default():
        return {
            'hide_past': True,
            'age': None
        }

    @staticmethod
    def parse(form) -> dict:
        filters = {
            'hide_past': form.get('hide_past', 'True') == 'True',
        }
        if form.get('age', 'None') != 'None':
            filters['age'] = form['age']

        return filters

class Event:
    col = eventData

    @staticmethod
    def create(league, form):
        event = {
            'date': datetime.strptime(form.get('date'), 'format'),
            'season': form.get('season'),
            'leagueId': league,
            'venueId': form.get('venue'),
            'field': form.get('field'),
            'type': form.get('type', 'Game'),
            'age': form.get('age'),
            'away': form.get('away'),
            'home': form.get('home'),
            'score': form.get('score', [0,0]),
            'status': form.get('status'),
            'umpires': {
                'Plate': {
                    'user': None,
                    'team_duty': False,
                    'permissions': ['plate']
                },
                '1B': {
                    'user': None,
                    'team_duty': False,
                    'permissions': ['field']
                }
            },
            'created': now()
        }
        _id = Event.col.insert_one(event).inserted_id
        event['_id'] = _id
        return Event.safe(event)
    
    @staticmethod
    def get(league):
        events = list(Event.col.find({'leagueId': league}))
        return [Event.safe(e) for e in events]
    
    @staticmethod
    def safe(event):
        event = _safe(event)

        # fill in umpire data
        full = True
        for u in event['umpires'].values():
            if u['user'] is None and not u['team_duty']:
                full = False
                break
            elif u['user'] and not u['team_duty']:
                u['user'] = User.get_user(userId=u['user'])
        
        event['umpire_full'] = full

        return event
    
    @staticmethod
    def add_umpire(eventId, user, pos):
        event = Event.col.find_one({'_id': ObjectId(eventId)})
        umpire = event['umpires'][pos]
        # check empty (safety catch)
        if umpire['user'] is not None:
            raise ValueError('Position is not empty!')
        
        # check permissions
        for perm in umpire['permissions']:
            if perm not in user['permissions']:
                raise PermissionError('You are not authorized to take this game!')
        
        # ADD
        Event.col.update_one({'_id': ObjectId(eventId)}, {'$set': {f'umpires.{pos}.user': user['userId']}})
        return "Game added!"