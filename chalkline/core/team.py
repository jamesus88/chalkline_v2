from chalkline.collections import teamData

class Team:
    col = teamData

    @staticmethod
    def load_teams(user, leagueId):
        teams = list(Team.col.find({'leagueId': leagueId, 'teamId': {'$in': user['teams']}}))
        user['teams'] = teams
        return user
    
    @staticmethod
    def get_teams(leagueId):
        return list(Team.col.find({'leagueId': leagueId}))