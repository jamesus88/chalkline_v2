from chalkline.collections import leagueData, venueData, directorData
from chalkline.core import now, _safe
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
            'active': True,
            'umpire_add': False,
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

class Venue:
    col = venueData

    @staticmethod
    def safe(venue):
        return _safe(venue)

    @staticmethod
    def create(form):
        venue = {
            'venueId': form['venueId'],
            'name': form['name'],
            'street': form['street'],
            'city': form['city'],
            'zipcode': form['zipcode'],
            'state': form['state'],
            'field_count': int(form['field_count'])
        }
        _id = Venue.col.insert_one(venue).inserted_id
        venue['_id'] = _id
        return Venue.safe(venue)
    
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