import sqlite3
from datetime import datetime
from pushbullet import Pushbullet

teamLink = "http://www.bucs.org.uk/bucscore/TeamProfile.aspx?id={0}"

def run(dbName):
    conn = sqlite3.connect(dbName)
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    allUsers = c.fetchall()

    for user in allUsers:

        #Has push api key
        if user[1] != None:

            pb = Pushbullet(user[1])

            #Find relevant teams
            c.execute("SELECT team_id FROM alert_prefs WHERE user_email = ?", (user[2], ))
            selectedTeams = c.fetchall()
            for team in selectedTeams:
                #Find all team details
                team_id = team[0]
                c.execute("SELECT * FROM teams WHERE id = ?", (team_id, ) )
                teamRow = c.fetchone()

                #Find new, relevant changes
                c.execute("SELECT * FROM changes WHERE (team1 = ? or team2 = ?) AND  unixdateChanged > ?", (team_id, team_id, user[3]))
                relevantChanges = c.fetchall()
                for change in relevantChanges:

                    #Find opposing team
                    if teamRow[0] == change[0]:
                        c.execute("SELECT * FROM teams WHERE id = ?", (change[1], ))
                    else:
                        c.execute("SELECT * FROM teams WHERE id = ?", (change[0], ))
                    teamOpp = c.fetchone()

                    #Push notification
                    pb.push_link("BUCS Change", teamLink.format(teamRow[0]), change[2] + " for " + teamRow[2] + " " + teamRow[3] + " " + teamRow[4] + " against " + teamOpp[1] + " " + teamOpp[4])

            #Update last pushed time
            currentUnix = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
            c.execute("UPDATE users SET last_pushed = ? WHERE email = ?", (currentUnix, user[2]))

    conn.commit()
    c.close()
