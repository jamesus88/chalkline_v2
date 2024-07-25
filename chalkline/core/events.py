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
    def user_in_event(event, user) -> bool:
        # check umpires
        for ump in event['umpires'].values():
            if ump['user']:
                if ump['user']['userId'] == user['userId']:
                    return True
            
        # check teams
        for team in user['teams']:
            if event['away'] == team or event['home'] == team:
                return True
            
        return False
    
    @staticmethod
    def team_in_event(event, team) -> bool:
        if team in (event['away'], event['home']):
            return True
        
        return False
    
    @staticmethod
    def get(league, user=None, team=None, filters=Filter.default()):
        criteria = [{'leagueId': league}]

        all_events = [Event.safe(e) for e in Event.col.find({'$and': criteria})]
        events = []

        # filter
        for e in all_events:
            if user:
                if not Event.user_in_event(e, user):
                    continue
            if team:
                if not Event.team_in_event(e, team):
                    continue
    
            events.append(e)

        return events
    
    @staticmethod
    def safe(event):
        event = _safe(event)
        umpires = [User.safe(u) for u in User.col.find({'leagues': {'$in': [event['leagueId']]}, 'groups': {'$in': ['umpire']}})]

        # fill in umpire data
        full = True
        for u in event['umpires'].values():
            if u['user']:
                u['user'] = User.filter_for(umpires, userId=u['user'])
            elif u['team_duty'] and not u['coach_req']:
                continue
            else:
                full = False
        
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
    
    @staticmethod
    def remove_umpire(eventId, pos, user):
        Event.col.update_one({'_id': ObjectId(eventId), f'umpires.{pos}.user': user['userId']}, {'$set': {f'umpires.{pos}.user': None}})