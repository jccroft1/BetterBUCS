import dbCreator
import time
import logging
import push
import calendarFeed

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename='output.log',level=logging.INFO)

if __name__ == '__main__':

    dbName = 'bucsLive.db'

    while(True):
        try:

            db = dbCreator.BUCS_DB(dbName)
            logging.info("Connected to db")

            db.updateFixtures()
            logging.info("Fixtures updated")

            db.updateResults()
            logging.info("Results updated")

            db.finish()
            logging.info("Closed db")

            push.run(dbName)
            logging.info("Pushed notifications")

            calendarFeed.run(dbName)
            logging.info("Updated calendars")

            time.sleep(60*30)

        except Exception, e:
            logging.warning(e)
            logging.info("Retrying in 5 minutes")
            print str(e)

            time.sleep(60*5)
