from chalkline.collections import teamData
from chalkline.core import _safe

class Team:
    col = teamData

    @staticmethod
    def safe(team):
        return _safe(team)

    @staticmethod
    def load_teams(user, leagueId):
        teams = list(Team.col.find({'league': leagueId, 'teamId': {'$in': user['teams']}}))
        user['team_info'] = [Team.safe(t) for t in teams]
        return user
    
    @staticmethod
    def get_teams(leagueId):
        return [Team.safe(t) for t in Team.col.find({'league': leagueId})]
    
    @staticmethod
    def create(form):
        team = {
            'league': form.get('league'),
            'teamId': form.get('teamId'),
            'name': form.get('name'),
            'seasons': {
                'Fall 2024': {'record': [0,0,0], 'coaches': ['ahurwitz']}
            },
            'age': form.get('age'),
            'active': True
        }