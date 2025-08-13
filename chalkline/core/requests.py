from chalkline.collections import requestData
from chalkline.core import _safe, now, ObjectId
from datetime import datetime
from chalkline.core.league import League

class Request:
    col = requestData

    @staticmethod
    def create(res, r_type, date, **kwargs):
        req = {
            'leagueId': res['league']['leagueId'],
            'type': r_type,
            'next_update': datetime.strptime(date, '%Y-%m-%dT%H:%M'),
            'last_performed': None,
            'created': now(),
            'author': res['user']['userId'],
            'action': {}
        }

        # types of requests go here
        match req['type']:
            case "update_permissions":
                req['action']['group'] = kwargs['group']
                req['action']['perms'] = kwargs['perms']

                _id = Request.col.insert_one(req).inserted_id
                req['_id'] = _id
                League.update_group_later(res['league'], kwargs['group'], req)

        
        return _safe(req)

    @staticmethod
    def get(date=None):
        if date:
            reqs = Request.col.find({'next_update': {'$gte': now()}})
        else:
            reqs = Request.col.find({})

        return [_safe(r) for r in reqs]
    
    @staticmethod
    def perform(req):
        match req['type']:
            case "update_permissions":
                league = League.get(req['leagueId'])
                League.update_group(league, req['action']['group'], req['action']['perms'])

        Request.col.update_one({'_id': ObjectId(req['_id'])}, {'$set': {'last_performed': now(), 'next_update': None}})
        print(f"{req['type']} for {req['leagueId']} completed.")

    @staticmethod
    def cancel(req_id):
        req = Request.col.find_one({'_id': ObjectId(req_id)})
        if not req: return
        league = League.get(req['leagueId'])
        
        if req['type'] == "update_permissions":
            League.cancel_group_update(league, req['action']['group'])
                
        Request.col.delete_one({"_id": ObjectId(req_id)})
        