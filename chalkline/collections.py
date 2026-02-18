import pymongo, os, certifi

client = pymongo.MongoClient(os.environ.get('PYMONGO_CLIENT'), connect=False,  tlsCAFile=certifi.where())
db = client['chalkline']

eventData = db['events']
userData = db['users']
# permissions = db['permissions']
# reportData = db['reports']
teamData = db['teams']
# playerData = db['players']
leagueData = db['leagues']
venueData = db['venues']
directorData = db['directors']
requestData = db['requests']
messageData = db['messages']
# rentalData = db['rentals']
# logsData = db['logs']