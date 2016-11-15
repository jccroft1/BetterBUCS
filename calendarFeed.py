import sqlite3
from datetime import datetime, timedelta
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def run(dbName):
    conn = sqlite3.connect(dbName)
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    allUsers = c.fetchall()

    for user in allUsers:
        f = open("calendar/" + user[0] + '.ics', 'w')
        f.write("\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BUCS-API"]) + "\n")

        c.execute("SELECT team_id FROM alert_prefs WHERE user_email = ?", (user[2], ) )
        selectedTeams = c.fetchall()

        for team_id in selectedTeams:
            c.execute("SELECT * FROM games WHERE awayTeamId = ? or homeTeamId = ?", (team_id[0], team_id[0]))
            teamGames = c.fetchall()
            c.execute("SELECT * FROM teams WHERE id = ?", (team_id[0], ))
            team = c.fetchone()

            for game in teamGames:
                f.write("BEGIN:VEVENT\n")
                if team[0] == game[2]: #Away game
                    c.execute("SELECT * FROM teams WHERE id = ?", (game[3], ))
                    oppTeam = c.fetchone()
                    loc = "Away"
                else: #Home game
                    c.execute("SELECT * FROM teams WHERE id = ?", (game[2], ))
                    oppTeam = c.fetchone()
                    loc = "Home"
                if (oppTeam == None):
                    oppTeam = (0, "Unknown University", team[2], team[3], "Unknown tier")
                f.write("SUMMARY:Lancaster " + team[2] + " " + team[3] + " " + team[4] + " vs " + oppTeam[1] + " " + oppTeam[4] + "\n")
                f.write("DESCRIPTION:Stuff" + " and things" + "\n")
                f.write("LOCATION:" + str(game[0]) + "\n")

                dt = datetime.fromtimestamp(game[4])
                if (dt.hour == 0 and dt.minute == 0):
                    #Full day
                    f.write("DTSTART:" + dt.strftime("%Y%m%d") + "\n")
                    f.write("DTEND:" + dt.strftime("%Y%m%d") + "\n")
                else:
                    f.write("DTSTART:" + dt.strftime("%Y%m%dT%H%M00") + "\n")
                    f.write("DTEND:" + (dt + timedelta(hours = 2)).strftime("%Y%m%dT%H%M00") + "\n" )

                f.write("END:VEVENT\n")
            """End of games"""
        """End of team"""

        f.write("END:VCALENDAR")
        f.close()
    """End of user"""

    conn.commit()
    c.close()
