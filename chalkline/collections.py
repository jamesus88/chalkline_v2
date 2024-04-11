import pymongo, os, certifi

client = pymongo.MongoClient(os.environ.get('PYMONGO_CLIENT'), connect=False,  tlsCAFile=certifi.where())
db = client['chalkline']

eventData = db['eventData']
userData = db['userData']
permissions = db['permissions']
reportData = db['reportData']
teamData = db['teamData']
playerData = db['playerData']
leagueData = db['leagueData']
venueData = db['venueData']
directorData = db['directorData']
rentalData = db['rentalData']
logsData = db['logs']