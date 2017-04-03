#!/usr/bin/env python
import argparse, os, platform, sys, time, signal
from argparse import RawTextHelpFormatter
import sqlite3 as lite

#==============================================================================
import logging
logging_config = {
    'filename': '/var/log/linger_counter.log',
    'format': '%(asctime)s [%(levelname)s] %(message)s',
    'level': logging.WARNING
}
logging.basicConfig(**logging_config)

#==============================================================================
try:
    from lingerSettings import *
except:
    # if no alternative path has been set, use the RPi path
    lingerPath = "/home/pi/linger"


#==============================================================================
# Handle arguments
#==============================================================================
PARSER = argparse.ArgumentParser(prog='linger', description=
'''This script checks the amount of devives saved in the
database and displays the number on a 7 segment display.
For more info on what Linger
does see README.md''',
formatter_class=RawTextHelpFormatter)

PARSER.add_argument('-db', default='probes', dest='db_name', metavar='filename',\
help='Database name. Defaults to probes.', action='store')

PARSER.add_argument('-v', dest='verbose', action='count',\
help='Verbose; can be used up to 3 times to set the verbose level.')

PARSER.add_argument('--version', action='version', version='%(prog)s version 0.1.0',\
help='Show program\'s version number and exit.')

ARGS = PARSER.parse_args()

#==============================================================================
# To be able to run this script for testing on a non-RPi device,
# we check if we're on RPi hardware and skip some code if not
onPi = True
if platform.machine() != "armv7l" and platform.machine() != "armv6l":
    onPi = False
    if ARGS.verbose > 2: print "onPi: False"
    logging.info('Not a RPi, so running in limited mode')
else:
    if ARGS.verbose > 2: print "onPi: True"
    import tm1637

#==============================================================================
# Stop script if not running as root. Doing this after the argparse so you can still
# read the help info without sudo (using -h / --help flag)
if onPi and not os.geteuid() == 0:
    sys.exit('Script must be run as root because of GPIO access')


#==============================================================================
# Add .sqlite to our database name if needed
if ARGS.db_name[-7:] != ".sqlite": ARGS.db_name += ".sqlite"
db_path = '/'.join([lingerPath, ARGS.db_name])

if onPi:
    # Load our display so we can use it globally
    Display = tm1637.TM1637(23,24,tm1637.BRIGHT_TYPICAL)

# Functions used to catch a kill signal so we can cleanly
# exit (like storing a database)
def set_exit_handler(func):
    signal.signal(signal.SIGTERM, func)

def on_exit(sig, func=None):
    if ARGS.verbose > 0: print "Received kill signal. Stop"
    Display.Clear()
    Display.SetBrightness(0)
    sys.exit(1)

#=======================================================
# Get a user
def get_device_amount(con):
    with con:
        cur = con.cursor()
        try:
            cur.execute("SELECT COUNT(DISTINCT mac) AS amount FROM entries")
            return cur.fetchone()[0]
        except: # simply return 0 if there was a problem
            if ARGS.verbose > 0: print "Encountered a problem getting the device amount"
            logging.warning('Problem getting amount of devices from database')
            return 0

#===========================================================
# Main program
#===========================================================
def main():
    set_exit_handler(on_exit)

    global Display
    if onPi:
        if ARGS.verbose > 2: print "On Pi: initiate display"
        #Display = tm1637.TM1637(23,24,tm1637.BRIGHT_TYPICAL)
        Display.Clear()
        Display.SetBrightness(3)
        Display.ShowInt(0)

    #=========================================================
    if ARGS.verbose > 1: print "Using database {}".format(db_path)
    logging.info('Using database: {}'.format(db_path))
    # Check if the database file exists, if not, retry every 10
    # seconds, as the other scripts might need some time to
    # create the file
    firstError = True
    while not os.path.isfile(db_path):
        if firstError:
            firstError = False;
            logging.warning('Database file does not exist: {}'.format(db_path))
            if ARGS.verbose > 0: print "Database {} does not exist".format(db_path)
        logging.info('Retry in 10 seconds...')
        if ARGS.verbose > 0: print "Retry in 10 seconds...".format(db_path)
        time.sleep(10)

    # Create a database connection, catch any trouble while connecting
    try:
        con = lite.connect("{}/{}".format(lingerPath, ARGS.db_name))
        cur = con.cursor()
    except:
        logging.error('Error connecting to database')
        if ARGS.verbose > 0: print "Error connecting to database..."

    while True:
        amount = get_device_amount(con)
        if onPi:
            Display.ShowInt(amount)
        time.sleep(5)

if __name__ == "__main__":
    main()
