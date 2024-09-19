from chalkline.collections import eventData
from datetime import datetime, timedelta
from chalkline.core import now, _safe, ObjectId
from chalkline.core.user import User
import chalkline.core.mailer as mailer
from flask import session, render_template
from chalkline import SEASON

class Filter:
    @staticmethod
    def default():
        return {
            'age': None,
            'start': now() - timedelta(hours=2),
            'end': now() + timedelta(days=200),
            'umpires_only': False,
            'team': None,
            'season': SEASON
        }

    @staticmethod
    def parse(form) -> dict:
        filters = Filter.default()

        if form.get('filter_reset'):
            return filters

        filters['umpires_only'] = form.get('filter_umpires_only') == 'True'

        if form.get('filter_age', 'None') != 'None':
            filters['age'] = form['filter_age']
        if form.get('filter_start'):
            filters['start'] = datetime.strptime(form['filter_start'], "%Y-%m-%dT%H:%M")
        if form.get('filter_end'):
            filters['end'] = datetime.strptime(form['filter_end'], "%Y-%m-%dT%H:%M")
        if form.get('filter_team', 'None') != 'None':
            filters['team'] = form['filter_team']

        filters['season'] = form.get('filter_season')
        
        return filters

class Event:
    col = eventData

    @staticmethod
    def create(league, form):
        form = dict(form)
        if form.get('home') == "": form['home'] = None
        if form.get('away') == "": form['away'] = None

        event = {
            'date': datetime.strptime(form.get('date'), '%Y-%m-%dT%H:%M'),
            'season': league['current_season'],
            'leagueId': league['leagueId'],
            'venueId': form.get('venueId'),
            'field': int(form.get('field')),
            'type': form.get('type', 'Game'),
            'age': form.get('age'),
            'away': form.get('away'),
            'home': form.get('home'),
            'score': [0,0],
            'status': form.get('status'),
            'visible': True,
            'umpires': {},
            'created': now()
        }

        umps = {}
        for key in form:
            if '_' not in key:
                continue
            
            ump, attr = key.split('_')
            if ump in umps:
                umps[ump][attr] = form[key]
            else:
                umps[ump] = {attr: form[key]}

        for ump in umps:
            umps[ump]['user'] = None
            umps[ump]['team_duty'] = None if umps[ump]['team'] == 'None' else umps[ump]['team']
            umps[ump]['coach_req'] = None
            umps[ump]['permissions'] = Event.generate_ump_permissions(event['age'], umps[ump]['pos'])
            
            pos = umps[ump]['pos']
            del umps[ump]['pos']
            del umps[ump]['team']

            event['umpires'].update({pos: umps[ump]})

        _id = Event.col.insert_one(event).inserted_id
        event['_id'] = _id
        return Event.safe(event)

    @staticmethod
    def generate_ump_permissions(age, pos):
        if pos == 'Plate':
            return [f'umpire_Plate_{age}']
        else:
            return [f'umpire_Field_{age}']
    
    @staticmethod
    def user_in_event(event, user, check_user_teams) -> bool:
        # check umpires
        for ump in event['umpires'].values():
            if ump['user']:
                try:
                    if ump['user']['userId'] == user['userId']:
                        return True
                except TypeError:
                    if ump['user'] == user['userId']:
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
        
        for ump in event['umpires'].values():
            if team == ump['team_duty']:
                return True
        
        return False
    
    @staticmethod
    def get(league, user=None, team=None, check_user_teams=True, filters=Filter.default(), add_criteria = {}, safe=True):
        criteria = [{'leagueId': league['leagueId']}, add_criteria]

        if filters.get('season'):
            criteria.append({'season': filters['season']})
        if filters.get('umpires_only'):
            criteria.append({'umpires': {'$ne': {}}})
        if filters.get('age'):
            criteria.append({'age': filters['age']})
        if filters.get('start'):
            criteria.append({'date': {'$gte': filters['start']}})
        if filters.get('end'):
            criteria.append({'date': {'$lte': filters['end']}})

        all_events = list(Event.col.find({'$and': criteria}).sort(['date', 'field']))

        if safe:
            umps = User.find_groups(league, ["umpire"])
            all_events = [Event.safe(e, umps) for e in all_events]

        events = []

        # filter
        for e in all_events:
            if user:
                if not Event.user_in_event(e, user, check_user_teams):
                    continue
            if team:
                if not Event.team_in_event(e, team):
                    continue
            elif filters.get('team'):
                if not Event.team_in_event(e, filters['team']):
                    continue

            if filters['umpires_only']:
                found = False
                for ump in e['umpires'].values():
                    if not ump['team_duty']:
                        found = True
                    else:
                        if ump['coach_req']:
                            found = True
                
                if not found: continue

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
    def safe(event, user_list=None):
        event = _safe(event)
        league = session['league']
        if user_list is None: umpires = [User.view(u) for u in User.find_groups(league, ['umpire'])]
        else: umpires = user_list

        #if localize_times: event['date'] = localize(event['date'])

        # fill in umpire data and add team hints
        full = True
        team_umps = []
        for u in event['umpires'].values():

            if u['team_duty']:
                team_umps.append(u['team_duty'])
                event["ump_" + u['team_duty']] = u

            if u['user']:
                u['user'] = User.filter_for(umpires, userId=u['user'])
            elif u['team_duty'] and not u['coach_req']:
                continue
            else:
                full = False

        event['umpire_full'] = full

        if len(team_umps) > 0:
            event['team_umps'] = team_umps
        else:
            event['team_umps'] = ['None']

        return event
    
    
    @staticmethod
    def add_umpire(eventId, user, pos):
        event = Event.col.find_one({'_id': ObjectId(eventId)})
        umpire = event['umpires'][pos]
        # check empty (safety catch)
        if umpire['user'] is not None:
            raise ValueError('Position is not empty!')
        
        # check permissions
        if not User.check_permissions_to_add(umpire, user):
            raise PermissionError("You are not authorized to add this game!")
        
        if umpire.get("coach_req") is not None:
            coach = User.get_user(userId=umpire["coach_req"])
            msg = mailer.ChalklineEmail(
                "Umpire Request Fulfilled!",
                recipients=[coach['email']],
                html=render_template("emails/shift-fulfilled.html", event=event, replaced=pos), 
            )

            mailer.sendMail(msg)

        
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
    def generate_blank_ump_pos(event, pos):
        blank = {
            'user': None,
            'team_duty': None,
            'permissions': [],
            'coach_req': None
        }
        if pos == 'Plate':
            blank['permissions'].append(f'umpire_Plate_{event['age']}')
        else:
            blank['permissions'].append(f'umpire_Field_{event['age']}')

        return blank

    @staticmethod
    def add_ump_pos(event, pos):
        blank = Event.generate_blank_ump_pos(event, pos)
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
        form = dict(form)
        if form.get('away') == 'None': form['away'] = None
        if form.get('home') == 'None': form['home'] = None

        event['date'] = datetime.strptime(form['date'], "%Y-%m-%dT%H:%M")
        event['venueId'] = form['venueId']
        event['field'] = int(form['field'])
        event['age'] = form['age']
        event['away'] = form.get('away')
        event['home'] = form['home']
        event['status'] = form['status']
        event['visible'] = form.get('visible') == 'on'
        for pos in event['umpires']:
            if form[f"{pos}_user"] == '':
                event['umpires'][pos]['user'] = None
            else:
                event['umpires'][pos]['user'] = form[f'{pos}_user']
            if form[f'{pos}_team'] == 'None':
                event['umpires'][pos]['team_duty'] = None
            else:
                event['umpires'][pos]['team_duty'] = form[f'{pos}_team']
        _id = event['_id']
        del event['_id']
        event.pop('league_info')
        event.pop('team_umps')
        event.pop('umpire_full')

        Event.col.replace_one({'_id': ObjectId(_id)}, event)
    
    @staticmethod
    def get_all_ump_positions():
        return [
            'Plate',
            '1B',
            '2B',
            '3B',
            'LF',
            'RF',
            'Misc'
        ]
    
    @staticmethod
    def substitute(event, pos, user):
        ump = event['umpires'][pos]
        if User.check_permissions_to_add(ump, user):
            Event.col.update_one({'_id': ObjectId(event['_id'])}, {'$set': {f'umpires.{pos}.user': user['userId']}})
        else:
            raise PermissionError("You do not have permission to add this game!")

    