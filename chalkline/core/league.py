from chalkline.collections import leagueData

class League:
    col = leagueData

    @staticmethod
    def get_league(leagueId):
        return League.col.find_one({'leagueId': leagueId})
    
    @staticmethod
    def create(form):
        league = {
            'leagueId': form['leagueId'],
            'name': form['name'],
            'abbr': form['abbr'],
            'venues': [],
            'auth': {
                'umpire_code': form['umpire_code'],
                'coach_code': form['coach_code'],
                'director_code': form['director_code']
            }
        }
        _id = League.col.insert_one(league).inserted_id
        league['_id'] = _id
        return league