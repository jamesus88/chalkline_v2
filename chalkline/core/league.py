from chalkline.collections import leagueData, teamData, venueData
from chalkline.core import now
from chalkline import SEASON

class League:
    col = leagueData

    @staticmethod
    def get(leagueId):
        league = League.col.find_one({'leagueId': leagueId})
        league['teams'] = list(teamData.find({'leagueId': league['leagueId']}))
        return league
    
    @staticmethod
    def create(form):
        league = {
            'leagueId': form['leagueId'],
            'name': form['name'],
            'current_season': SEASON,
            'abbr': form['abbr'],
            'venues': [],
            'age_groups': [],
            'auth': {
                'umpire_code': form['umpire_code'],
                'coach_code': form['coach_code'],
                'director_code': form['director_code']
            },
            'active': True,
            'created': now()
        }
        _id = League.col.insert_one(league).inserted_id
        league['_id'] = _id
        return league