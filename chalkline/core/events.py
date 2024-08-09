from chalkline.collections import eventData
from datetime import datetime, timedelta
from chalkline.core import now, _safe, ObjectId
from chalkline.core.user import User

class Filter:
    @staticmethod
    def default():
        return {
            'hide_past': True,
            'age': None,
            'start': now() - timedelta(hours=2),
            'end': None,
            'umpires_only': False
        }

    @staticmethod
    def parse(form) -> dict:
        filters = {
            'hide_past': form.get('hide_past', 'True') == 'True',
            'umpires_only': form.get('umpires_only', 'True') == 'True',
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
            'visible': True,
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
    def user_in_event(event, user, check_user_teams) -> bool:
        # check umpires
        for ump in event['umpires'].values():
            if ump['user']:
                if ump['user']['userId'] == user['userId']:
                    return True
            
        # check teams
        if check_user_teams:
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
    def get(league, user=None, team=None, check_user_teams=True, filters=Filter.default()):
        criteria = [{'leagueId': league}]

        all_events = [Event.safe(e) for e in Event.col.find({'$and': criteria})]
        events = []

        # filter
        for e in all_events:
            if user:
                if not Event.user_in_event(e, user, check_user_teams):
                    continue
            if team:
                if not Event.team_in_event(e, team):
                    continue
    
            events.append(e)

        return events
    
    @staticmethod
    def find(eventId):
        e = Event.col.find_one({"_id": ObjectId(eventId)})
        if e:
            return Event.safe(e)
        else:
            return None
    
    @staticmethod
    def safe(event):
        event = _safe(event)
        umpires = [User.view(u) for u in User.col.find({'leagues': {'$in': [event['leagueId']]}, 'groups': {'$in': ['umpire']}})]

        # fill in umpire data and add team hints
        full = True
        team_umps = []
        for u in event['umpires'].values():
            if u['team_duty']:
                team_umps.append(u['team_duty'])

            if u['user']:
                u['user'] = User.filter_for(umpires, userId=u['user'])
            elif u['team_duty'] and not u['coach_req']:
                continue
            else:
                full = False
        
        event['umpire_full'] = full
        event['team_umps'] = team_umps

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

    @staticmethod
    def request_umpire(eventId, pos, coach):
        Event.col.update_one({'_id': ObjectId(eventId)}, {'$set': {f'umpires.{pos}.coach_req': coach['userId']}})

    @staticmethod
    def delete_ump_pos(event, pos):
        Event.col.update_one({'_id': ObjectId(event['_id'])}, {'$unset': {f'umpires.{pos}': 0}})

    @staticmethod
    def generate_ump_pos(event, pos):
        blank = {
            'user': None,
            'team_duty': None,
            'permissions': [],
            'coach_req': None
        }
        return blank

    @staticmethod
    def add_ump_pos(event, pos):
        blank = Event.generate_ump_pos(event, pos)
        Event.col.update_one({'_id': ObjectId(event['_id'])}, {'$set': {f'umpires.{pos}': blank}})

    @staticmethod
    def remove_request(eventId, pos):
        event = Event.col.find_one_and_update(
            {
                '_id': ObjectId(eventId),
                f'umpires.{pos}.user': None
            }, 
            {'$set': {f'umpires.{pos}.coach_req': None}})
        
        if event is None:
            raise ValueError('An umpire has already accepted this game!')
        
    @staticmethod
    def label_umpire_duties(events, team):
        for e in events:
            for ump in e['umpires'].values():
                if ump['team_duty'] == team:
                    e['type'] = 'Umpire Duty'

    @staticmethod
    def update(event, form):
        event['date'] = datetime.strptime(form['date'], "%Y-%m-%dT%H:%M")
        event['venueId'] = form['venueId']
        event['field'] = int(form['field'])
        event['age'] = form['age']
        event['away'] = form.get('away')
        event['home'] = form['home']
        event['status'] = form['status']
        event['visible'] = form.get('visible') == 'on'
        for pos in event['umpires']:
            event['umpires'][pos]['user'] = form.get(f'{pos}_user')
            if form[f'{pos}_team'] == 'None':
                event['umpires'][pos]['team_duty'] = None
            else:
                event['umpires'][pos]['team_duty'] = form[f'{pos}_team']
        _id = event['_id']
        del event['_id']
        Event.col.replace_one({'_id': ObjectId(_id)}, event)
    