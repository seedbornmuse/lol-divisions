import urllib, urllib2
from time import sleep
import json
import mysql.connector
from mysql.connector import errorcode
from mysql.connector.errors import DatabaseError

#https://na.api.pvp.net/api/lol/na/v2.4/league/by-summoner/19570433/entry?api_key=2bbcc5f9-6a16-4a08-b126-89b12f391343
#/api/lol/{region}/v2.5/league/by-summoner/{summonerIds}/entry
ENTRIES_PER_REQ = 10
#REQ_PER_SEC = .8
REQ_PERIOD = 1.5
API_KEY = '2bbcc5f9-6a16-4a08-b126-89b12f391343'
VERSION = 2.5
MODES = {'RANKED_SOLO_5x5':1, 'RANKED_TEAM_3x3':2, 'RANKED_TEAM_5x5':3}
TIERS = {'BRONZE':1, 'SILVER':2, 'GOLD':3 ,'PLATINUM':4 , 'DIAMOND':5}

json_decoder = None

'''
Table Name = Regions
	-na
	-eu
	
Schema:
	mode
		1-RANKED_SOLO_5x5
		2-RANKED_TEAM_3x3
		3-RANKED_TEAM_5x5
	tier
		1-bronze
		2-silver
		3-gold
		4-plat
		5-diamond
	champion
		-max 25 chars
	suffix
		-max 25 chars
	players
		-csv
		-max 84 chars
		-max 5 players
		-players should cap at 16 chars each
		-EX:
			player1,player2,player3,player4,player5
'''

#/api/lol/{region}/v2.5/league/by-summoner/{summonerIds}/entry
#will request the first ENTRIES_PER_REQ entries in numerical order
#region = a region from list of regions 
#idlist = list of id numbers to request
#start = start a range of ids to request
#size = number of ids to request, beginning at start. defaults to 1
'''
Errors:
400	Bad request
401	Unauthorized
404	League not found
429	Rate limit exceeded
500	Internal server error
503	Service unavailable
'''
def getLeagueEntryByID(region, start = None, size = 1, idlist = None):

	if idlist is None:
		idlist = []
		
	if start is not None:
		#idlist.add(i) for i in range(start, end + 1) if i not in idlist
		for i in range(start, start + size):
			if i not in idlist:
				idlist.append(i)
		
	url = 'https://na.api.pvp.net/api/lol/' + region + '/v' + str(VERSION) + '/league/by-summoner/' 
	url += ','.join( str(x) for x in idlist[:10] ) + '/entry?api_key=' + API_KEY
	
	#Error codes listed above are thrown on this line
	resp = urllib2.urlopen(url)
	
	data = resp.read()		
	
	return data
	

def populateDivisions(region, start, end):

	json_decoder = json.JSONDecoder()
	
	log = open('divlog.txt', 'a')
	
	while start <= end:
		data = None
		try:
			data = getLeagueEntryByID(region, start, min(ENTRIES_PER_REQ, end - start + 1))
		except urllib2.URLError as err:
			if err.code in [429, 500, 503]:	
				sleep(REQ_PERIOD)
				continue
			elif err.code != 404:
				print str(start) + ' - ' + str(start + ENTRIES_PER_REQ)
				print err
				
		if data:
			try:
				data = json_decoder.decode(data) 
			except Exception as e:
				print e
			
			#id : list of dicts containing queue info
			for playerID in data:
				print playerID
				try:
					for mode in data[playerID]:
						queue = mode['queue']
						divname = mode['name']
						tier = mode['tier']
						member = mode['entries'][0]['playerOrTeamName']

						dbinsert(region, queue, tier, divname, member)
						
				except KeyError:
					log.write('Error:' + playerID + '\n')
				except DatabaseError:
					log.write('DBError:' + playerID + '\n')

		start += ENTRIES_PER_REQ
		sleep(REQ_PERIOD)
		
	log.close()
	
'''
{"79": [
   {
      "queue": "RANKED_SOLO_5x5",
      "name": "Swain's Villains",
      "entries": [{
         "leaguePoints": 70,
         "isFreshBlood": false,
         "isHotStreak": true,
         "division": "V",
         "isInactive": false,
         "isVeteran": true,
         "playerOrTeamName": "Xelnath",
         "playerOrTeamId": "79",
         "wins": 66
      }],
      "tier": "GOLD"
   },
   {
      "queue": "RANKED_TEAM_5x5",
      "name": "Nocturne's Giants",
      "entries": [{
         "leaguePoints": 58,
         "isFreshBlood": false,
         "isHotStreak": false,
         "division": "V",
         "isInactive": false,
         "isVeteran": false,
         "playerOrTeamName": "Wizardlock Warbringers",
         "playerOrTeamId": "TEAM-6395aff0-21e1-11e4-bd54-782bcb4d0bb2",
         "wins": 15
      }],
      "tier": "GOLD"
   }
]}
'''	
	


#SHOULD TAKE LIST INSTEAD	
def dbinsert(region, mode, tier, divname, member):
	try:
		cnx = mysql.connector.connect(user='root', password='mysql',
									  host='localhost',
									  database='divisions')
	except mysql.connector.Error as err:
	  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
		print("Something is wrong with your user name or password")
	  elif err.errno == errorcode.ER_BAD_DB_ERROR:
		print("Database does not exist")
	  else:
		print(err)
	else:		
		if mode in MODES.keys() and tier in TIERS.keys():	
		
			champion = divname[0:divname.find("'s ")]
			suffix = divname[divname.find("'s ") + 3:]
		
			query = 'SELECT * FROM ' + region + ' WHERE mode=' + str(MODES[mode]) + ' AND tier=' + str(TIERS[tier])
			query += ' AND champion="' + champion + '" AND suffix="' + suffix + '"'
			
			#print query
			
			cursor = cnx.cursor(buffered=True)
			cursor.execute(query)

			rows = cursor.fetchall()
			
			#assume only one entry
			if len(rows) != 0:
				members = rows[0][4].split(',')
				if member not in members:
					if len(members) < 5: #UPDATE
						update = 'UPDATE %s SET members=CONCAT(members,",%s") WHERE mode=%d AND tier=%d AND champion="%s" AND suffix="%s"' % (region, member, MODES[mode], TIERS[tier], champion, suffix)
						'''update = ("UPDATE %s SET members=CONCAT(members,',%s') WHERE "
									"mode=%d AND "
									"tier=%d AND "
									"champion='%s' AND "
									"suffix='%s'") % (region, member, MODES[mode], TIERS[tier], champion, suffix)'''
						#print update
						cursor.execute(update)
						cnx.commit()
			else: #INSERT
				insert = 'INSERT INTO %s VALUES(%d,%d,"%s","%s","%s")' % (region, MODES[mode], TIERS[tier], champion, suffix, member)
				#print insert
				cursor.execute(insert)
				cnx.commit()

			cursor.close()
			cnx.close()	
		

if __name__ == '__main__':
	#populateDivisions('na', 19107299, 19107299)
	populateDivisions('na', 0, 1000000)
	
	#getLeagueEntryByID('na', [20, 5,100,19570433], 2000, 2100)
