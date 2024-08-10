from chalkline.collections import teamData
from chalkline.core import _safe
from chalkline.core.user import User

class Team:
    col = teamData

    @staticmethod
    def safe(team):
        return _safe(team)
    
    @staticmethod
    def get(teamId):
        t = Team.col.find_one({'teamId': teamId})
        if t:
            return Team.safe(t)
        else:
            return None
        
    @staticmethod
    def load_contacts(team):
        users = User.col.find({'teams': {'$in': [team['teamId']]}})
        users = [User.view(u) for u in users]
        team['contacts'] = users

    @staticmethod
    def load_teams(user, leagueId):
        teams = list(Team.col.find({'league': leagueId, 'teamId': {'$in': user['teams']}}))
        user['team_info'] = [Team.safe(t) for t in teams]
        return user
    
    @staticmethod
    def get_league_teams(leagueId):
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