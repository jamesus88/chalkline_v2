from chalkline.collections import teamData
from chalkline.core import _safe
from chalkline import PROTOCOL, DOMAIN, SEASON
from chalkline.core.user import User

class Team:
    col = teamData

    class Filter:
        @staticmethod
        def default():
            return {
                'age': None,
                'season': SEASON
            }

        @staticmethod
        def parse(form) -> dict:
            filters = Team.Filter.default()

            if form.get('filter_reset'):
                return filters

            if form.get('filter_age', 'None') != 'None':
                filters['age'] = form['filter_age']

            filters['season'] = form.get('filter_season')
            
            return filters

    @staticmethod
    def safe(team):
        team['link'] = Team.get_share_link(team)
        return _safe(team)
    
    @staticmethod
    def get(teamId):
        t = Team.col.find_one({'teamId': teamId})
        if t:
            return Team.safe(t)
        else:
            return None
        
    @staticmethod
    def load_contacts(team, team_is_loaded=True):
        if team_is_loaded:
            users = User.col.find({'teams': {'$in': [team['teamId']]}})
        else:
            users = User.col.find({'teams': {'$in': [team]}})
        users = [User.view(u) for u in users]

        if team_is_loaded: team['contacts'] = users
        return users

    @staticmethod
    def load_teams(user, league):
        teams = list(Team.col.find({'leagueId': league['leagueId'], 'teamId': {'$in': user['teams']}}))
        user['team_info'] = [Team.safe(t) for t in teams]
        return user
    
    @staticmethod
    def get_league_teams(leagueId, filters=Filter.default()):

        criteria = [{'leagueId': leagueId}, {f'seasons.{filters['season']}': {'$exists': True}}]
        
        if filters.get('age') is not None:
            criteria.append({'age': filters['age']})

        return [Team.safe(t) for t in Team.col.find({'$and': criteria}).sort("teamId")]
    
    @staticmethod
    def create(league, form):
        team = {
            'leagueId': league['leagueId'],
            'teamId': league['abbr'] + '-' + form.get('age').upper()[:3] + form.get('teamId'),
            'code': form.get('age').upper()[:3] + form.get('teamId'),
            'name': form.get('name'),
            'seasons': {
                league['current_season']: {'record': [0,0,0], 'coaches': form.getlist('coaches')}
            },
            'age': form.get('age'),
            'active': True
        }

        if Team.col.count_documents({'leagueId': league['leagueId'], 'teamId': team['teamId']}) > 0:
            raise ValueError(f'A team with this code ({team['teamId']}) already exists. Choose a different number.')
        else:
            Team.col.insert_one(team)
            return team
        
    @staticmethod
    def delete(league, teamId):
        Team.col.delete_one({'leagueId': league['leagueId'], 'teamId': teamId})
        User.col.update_many({}, {'$pull': {'teams': teamId}})

    @staticmethod
    def remove_coach(teamId, season, userId):
        Team.col.update_one({'teamId': teamId}, {'$pull': {f'seasons.{season}.coaches': userId}})

    @staticmethod
    def add_coach(teamId, season, userId):
        Team.col.update_one({'teamId': teamId}, {'$push': {f'seasons.{season}.coaches': userId}})
        User.col.update_one({'userId': userId}, {'$push': {'teams': teamId}})

    @staticmethod
    def get_share_link(team):
        link = f"{PROTOCOL}://{DOMAIN}/invite/add-team/{team['teamId']}"
        return link
    

