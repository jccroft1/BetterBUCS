import sqlite3
import urllib
import urllib2
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class BUCS_DB:
    """Class to initialize and update a BUCS DB"""

    def __init__(self, fileName):
        self.conn = sqlite3.connect(fileName)
        self.c = self.conn.cursor()

    def finish(self):
        self.conn.commit()
        self.c.close()

    def updateFixtures(self):
        #Update fixtures for Lancaster teams
        self.c.execute("SELECT id FROM teams WHERE university = 'Lancaster University'")

        for team_id in self.c.fetchall():
            BUCS_DB.__updateFixture__(self, team_id[0])

    def __updateFixture__(self, id):
        url = "http://www.bucs.org.uk/bucscore/FixturesBasic.aspx?id=" + str(id) + "&Type=Team"

        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page, "html.parser")

        table = soup.table
        currentRow = table.tbody.tr

        while (currentRow != None):

            #Date
            em = currentRow.find("em")
            if (em is not None):
                dateString = em.get_text().strip()
                currentRow = currentRow.find_next_sibling("tr")

            currentCell = currentRow.td
            timeString = ''.join([s.strip() for s in currentCell.children if isinstance(s, basestring)])
            competitionString = currentCell.find("a", recursive=False).find("img")['title']
            currentCell = currentCell.find_next_sibling("td")
            homeTeamUrl = currentCell.div.find_next_sibling("div").a['href']
            homeTeamId = re.search('id=([^&]*)', homeTeamUrl).group(1)
            currentCell = currentCell.find_next_sibling("td")
            currentCell = currentCell.find_next_sibling("td")
            awayTeamUrl = currentCell.div.find_next_sibling("div").a['href']
            awayTeamId = re.search('id=([^&]*)', awayTeamUrl).group(1)

            #Location
            currentRow = currentRow.find_next_sibling("tr")
            if currentRow.find("i") != None:
                venueText = currentRow.find("i").get_text()
            else:
                venueText = None

            currentRow = currentRow.find_next_sibling("tr")
            currentRow = currentRow.find_next_sibling("tr")

            #Game time
            try:
                gameTime = datetime.strptime(dateString + " " + timeString, "%A, %d %B %Y %H:%M")
            except:
                gameTime = datetime.strptime(dateString, "%A, %d %B %Y")

            #Season
            if gameTime.month > 6:
                season = str(gameTime.year) + "/" + str(gameTime.year + 1)
            else:
                season = str(gameTime.year - 1)  + "/" + str(gameTime.year)

            unixGameTime = (gameTime - datetime(1970, 1, 1)).total_seconds()

            #Attempt to find match
            self.c.execute("SELECT * FROM games WHERE homeTeamId = ? AND awayTeamId = ? AND competition = ? AND season = ? LIMIT 1;", (homeTeamId, awayTeamId, competitionString, season) )
            oldGame = self.c.fetchone()
            currentUnix = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
            if (oldGame is None):
                #New fixture
                logging.info("New Fixtures")
                self.c.execute("INSERT INTO changes VALUES (?, ?, 'New fixture', ?, ?);", (homeTeamId, awayTeamId, currentUnix, competitionString) )
                self.c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL);", (venueText, competitionString, awayTeamId, homeTeamId, unixGameTime, season) )
            else:
                if oldGame[0] != venueText:
                    #Change in venue
                    logging.info("New venue")
                    self.c.execute("INSERT INTO changes VALUES (?, ?, 'Updated fixture date', ?, ?)", (homeTeamId, awayTeamId, currentUnix, competitionString) )
                    self.c.execute("UPDATE games SET venue = ? WHERE homeTeamId = ? AND awayTeamId = ? AND competition = ? AND season = ?", (venueText, homeTeamId, awayTeamId, competitionString, season))
                if oldGame[4] != unixGameTime:
                    #Change in day/ time
                    logging.info("New game time")
                    self.c.execute("INSERT INTO changes VALUES (?, ?, 'Updated fixture venue', ?, ?)", (homeTeamId, awayTeamId, currentUnix, competitionString) )
                    self.c.execute("UPDATE games SET unixdate = ? WHERE homeTeamId = ? AND awayTeamId = ? AND competition = ? AND season = ?", (unixGameTime, homeTeamId, awayTeamId, competitionString, season))

        """End of updateFixtures"""

    def updateResults(self):
        self.c.execute("SELECT id FROM teams WHERE university = 'Lancaster University'")

        for team_id in self.c.fetchall():
            BUCS_DB.__updateResult__(self, team_id[0])

    def __updateResult__(self, id):
        url = "http://www.bucs.org.uk/bucscore/ResultsBasic.aspx?id=" + str(id) + "&ResultType=team"

        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page, "html.parser")

        table = soup.table
        currentRow = table.tbody.tr

        while (currentRow != None):

            #Date
            em = currentRow.find("em")
            if (em is not None):
                dateString = em.get_text().strip()
                currentRow = currentRow.find_next_sibling("tr")

            #Comp, teams, score
            currentCell = currentRow.td
            competitionString = currentCell.find("a", recursive=False).find("img")['title']
            currentCell = currentCell.find_next_sibling("td")
            homeTeamUrl = currentCell.div.find_next_sibling("div").a['href']
            homeTeamId = re.search('id=([^&]*)', homeTeamUrl).group(1)
            currentCell = currentCell.find_next_sibling("td")
            #score
            scoreText = currentCell.get_text().strip()
            if scoreText == "w/o v":
                homeScore = None
                awayScore = None
                homeResult = "W"
                awayResult = "L"
            elif scoreText == "v w/o":
                homeScore = None
                awayScore = None
                homeResult = "L"
                awayResult = "W"
            elif (scoreText == "-" or scoreText == "V - V" or scoreText == "P - P"):
                homeScore = None
                awayScore = None
                homeResult = None
                awayResult = None
            else:
                try:
                    scoreList = scoreText.split(" ")
                    homeScore = int(scoreList[0])
                    awayScore = int(scoreList[2])
                    if homeScore > awayScore:
                        homeResult = "W"
                        awayResult = "L"
                    elif homeScore < awayScore:
                        homeResult = "L"
                        awayResult = "W"
                    else:
                        homeResult = "D"
                        awayResult = "D"
                except Exception,e:
                    print scoreText
                    print str(e)

            currentCell = currentCell.find_next_sibling("td")
            awayTeamUrl = currentCell.div.find_next_sibling("div").a['href']
            awayTeamId = re.search('id=([^&]*)', awayTeamUrl).group(1)

            #Location
            currentRow = currentRow.find_next_sibling("tr")
            if ("reason" in currentRow.get_text()  or "Additional Notes" in currentRow.get_text() ):
                #Walkover reason
                currentRow = currentRow.find_next_sibling("tr")

            if currentRow.find("i") != None:
                venueText = currentRow.find("i").get_text()
            else:
                venueText = None

            #Spacing
            currentRow = currentRow.find_next_sibling("tr")
            currentRow = currentRow.find_next_sibling("tr")

            #Game time
            gameTime = datetime.strptime(dateString, "%A, %d %B %Y")

            #Season
            if gameTime.month > 6:
                season = str(gameTime.year) + "/" + str(gameTime.year + 1)
            else:
                season = str(gameTime.year - 1)  + "/" + str(gameTime.year)

            unixGameTime = (gameTime - datetime(1970, 1, 1)).total_seconds()
            self.c.execute("SELECT * FROM games WHERE homeTeamId = ? AND awayTeamId = ? AND competition = ? AND season = ? LIMIT 1", (homeTeamId, awayTeamId, competitionString, season) )
            oldGame = self.c.fetchone()
            currentUnix = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
            if (oldGame is None):
                logging.warning("New result unmatched result")
                self.c.execute("INSERT INTO changes VALUES (?, ?, 'New Result', ?, ?);", (homeTeamId, awayTeamId, currentUnix, competitionString) )
                self.c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", (venueText, competitionString, awayTeamId, homeTeamId, unixGameTime, season, homeScore, awayScore, homeResult, awayResult) )
            else:
                if oldGame[6] != homeScore or oldGame[7] != awayScore or str(oldGame[8]) != str(homeResult) or str(oldGame[9]) != str(awayResult):
                    #Change in result
                    logging.info("Updated result " + str(unixGameTime) )
                    self.c.execute("INSERT INTO changes VALUES (?, ?, 'Updated Result', ?, ?)", (homeTeamId, awayTeamId, currentUnix, competitionString) )
                    self.c.execute("UPDATE games SET homeScore = ?, awayScore = ?, homeResult = ?, awayResult = ? WHERE homeTeamId = ? AND awayTeamId = ? AND competition = ? AND season = ?", (homeScore, awayScore, homeResult, awayResult, homeTeamId, awayTeamId, competitionString, season))

        """End of updateResult"""

"""Private methods"""
