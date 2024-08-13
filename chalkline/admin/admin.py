from chalkline.collections import userData, eventData, teamData, leagueData
from chalkline.core import mailer, ObjectId
from pymongo import UpdateOne
from datetime import datetime

class Admin:

    @staticmethod
    def update_all(form, cls):
        updates = {}

        for key, value in form.items():
            if '_' not in key:
                continue

            _id, attr = key.split('_')

            # formatting
            date_attrs = ['date']
            int_attrs = ['field']
            multi_attrs = ['groups', 'permissions']

            if attr in date_attrs:
                value = datetime.strptime(value, "%Y-%m-%dT%H:%M")
            elif attr in int_attrs:
                value = int(value)
            elif attr in multi_attrs:
                value = form.getlist(key)

            # append to updates

            if _id not in updates:
                updates[_id] = {attr: value}
            else:
                updates[_id][attr] = value
        
        writes = []
        for key, map in updates.items():
            writes.append(UpdateOne({'_id': ObjectId(key)}, {'$set': map}))

        cls.col.bulk_write(writes)

            
