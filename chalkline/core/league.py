from chalkline.collections import leagueData, venueData, directorData
from chalkline.core import now, _safe, check_unique
from chalkline.core.user import User
from chalkline.core.team import Team

class League:
    col = leagueData

    @staticmethod
    def safe(league):
        league['teams'] = Team.get_league_teams(league)
        return _safe(league)

    @staticmethod
    def get(leagueId):
        league = League.col.find_one({'leagueId': leagueId})
        if not league: raise ValueError("Error: League does not exist")
        return League.safe(league)
    
    @staticmethod
    def get_all():
        return [League.safe(l) for l in League.col.find()]
    
    @staticmethod
    def create(form):
        league = {
            'leagueId': form['leagueId'],
            'name': form['name'],
            'current_season': form['current_season'],
            'abbr': form['abbr'],
            'venues': [],
            'age_groups': [],
            'auth': {
                'umpire_code': form['umpire_code'],
                'coach_code': form['coach_code'],
                'director_code': form['director_code']
            },
            'perm_groups': [{
                'name': 'Default',
                'users': None,
                'perms': []
            }],
            'active': True,
            'umpire_add': False,
            'require_perm': True,
            'coach_add': True,
            'created': now()
        }
        _id = League.col.insert_one(league).inserted_id
        league['_id'] = _id
        return league
    
    @staticmethod
    def delete_age(league, age):
        League.col.update_one({'leagueId': league['leagueId']}, {'$pull': {'age_groups': age}})

    @staticmethod
    def add_age(league, age):
        League.col.update_one({'leagueId': league['leagueId'], 'age_groups': {'$nin': [age]}}, {'$push': {'age_groups': age}})

    @staticmethod
    def update_season(league, s):
        League.col.update_one({'leagueId': league['leagueId']}, {'$set': {'current_season': s}})

    @staticmethod
    def update_codes(league, form):
        codes = {
            'umpire_code': form['umpire_code'],
            'coach_code': form['coach_code'],
            'director_code': form['director_code']
        }
        League.col.update_one({'leagueId': league['leagueId']}, {'$set': {'auth': codes}})

    @staticmethod
    def load_venues(league):
        venues = Venue.col.find({'venueId': {'$in': league['venues']}})
        league['venue_info'] = [Venue.safe(v) for v in venues]
        return league
    
    @staticmethod
    def add_venue(league, venueId):
        League.col.update_one({'leagueId': league['leagueId']}, {'$push': {'venues': venueId}})

    @staticmethod
    def remove_venue(league, venueId):
        League.col.update_one({'leagueId': league['leagueId']}, {'$pull': {'venues': venueId}})

    @staticmethod
    def add_group(league, group: dict):
        grp_names = [g['name'] for g in league['perm_groups']]
        if group['name'] in grp_names:
            raise ValueError("Group name must be unique!")
        
        League.col.update_one({'leagueId': league['leagueId']}, {"$push": {"perm_groups": group}})

    @staticmethod
    def delete_group(league, group_name):
        if group_name == "Default":
            raise ValueError("Cannot delete Default group!")
        League.col.update_one(
            {'leagueId': league['leagueId']}, 
            {"$pull": {"perm_groups": {"name": group_name}}}
        )

    @staticmethod
    def update_group(league, group_name, perms):
        League.col.update_one(
            {'leagueId': league['leagueId']}, 
            {"$set": {"perm_groups.$[elem].perms": perms, "perm_groups.$[elem].last_updated": now(), "perm_groups.$[elem].pending_update": None}},
            array_filters=[{'elem.name': group_name}]
        )

    @staticmethod
    def update_group_later(league, group_name, req):
        League.col.update_one(
            {'leagueId': league['leagueId']}, 
            {"$set": {"perm_groups.$[elem].pending_update": req['_id']}},
            array_filters=[{'elem.name': group_name}]
        )

    @staticmethod
    def cancel_group_update(league, group_name):
        League.col.update_one(
            {'leagueId': league['leagueId']}, 
            {"$set": {"perm_groups.$[elem].pending_update": None}},
            array_filters=[{'elem.name': group_name}]
        )

class Venue:
    col = venueData

    @staticmethod
    def safe(venue):
        return _safe(venue)

    @staticmethod
    def create(form):
        venue = {
            'venueId': check_unique(Venue, "venueId", form['venueId']),
            'name': form['name'],
            'street': form['street'],
            'city': form['city'],
            'zipcode': form['zipcode'],
            'state': form['state'],
            'field_count': int(form['field_count']),
            'status': 'Open'
        }
        _id = Venue.col.insert_one(venue).inserted_id
        venue['_id'] = _id
        return Venue.safe(venue)
    
    @staticmethod
    def update(form):
        venue = {
            'name': form['name'],
            'street': form['street'],
            'city': form['city'],
            'zipcode': form['zipcode'],
            'state': form['state'],
            'field_count': int(form['field_count'])
        }
        Venue.col.update_one({'venueId': form['updateVenue']}, {"$set": venue})

    
    @staticmethod
    def get(venueId):
        return Venue.safe(Venue.col.find_one({'venueId': venueId}))
    
    @staticmethod
    def find_director(venue):
        shift = directorData.find_one({'venueId': venue, 'start_date': {'$lte': now()}, 'end_date': {'$gte': now()}})
        if shift:
            if shift['director']:
                user = User.get_user(userId=shift['director'], view = True)
                if user: return user
        return None
    
    @staticmethod
    def update_status(venueId, status):
        Venue.col.update_one({'venueId': venueId}, {'$set': {'status': status}})