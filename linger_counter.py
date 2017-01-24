#!/usr/bin/env python

try:
    from lingerSettings import *
except:
    # if we can't find alternative settings, use the RPi path
    lingerPath = "/home/pi/linger"

import argparse, os, platform, sys
from argparse import RawTextHelpFormatter
import sqlite3 as lite
from time import sleep

# To be able to run this script for testing on a non-RPi device,
# we check if we're on RPi hardware and skip some code if not
onPi = True
if platform.machine() != "armv7l":
    onPi = False
else:
    import tm1637

#===========================================================
# Handle arguments
#===========================================================
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
# Stop script if not running as root. Doing this after the argparse so you can still
# read the help info without sudo (using -h / --help flag)
if onPi and not os.geteuid() == 0:
    sys.exit('Script must be run as root because of GPIO access')

# Add .sqlite to our database name if needed
if ARGS.db_name[-7:] != ".sqlite": ARGS.db_name += ".sqlite"
db_path = '/'.join([lingerPath, ARGS.db_name])
# Functions used to catch a kill signal so we can cleanly
# exit (like storing the database)
def set_exit_handler(func):
    signal.signal(signal.SIGTERM, func)

def on_exit(sig, func=None):
    if ARGS.verbose > 0: print "Received kill signal. Stop"
    sys.exit(1)

#=======================================================
# Get a user
def get_device_amount(con):
    with con:
        cur = con.cursor()
        try:
            cur.execute("SELECT COUNT(DISTINCT mac) AS amount FROM entries")
            return cur.fetchone()[0]
        except: # return 0 if there was a problem
            return 0

#===========================================================
# Main program
#===========================================================
def main():
    if onPi:
        Display = tm1637.TM1637(23,24,tm1637.BRIGHT_TYPICAL)
        Display.Clear()
        Display.SetBrightness(3)

    #=========================================================
    if ARGS.verbose > 1: print "Using database {}".format(db_path)

    # Check if the database file exists, if not, retry every 10
    # seconds, as the other scripts might need some time to
    # create the file
    firstError = True
    while not os.path.isfile(db_path):
        if firstError:
            firstError = False;
            print "Database {} does not exist".format(db_path)
        print "Retry in 10 seconds...".format(db_path)
        sleep(10)

    # Create a database connection, catch any trouble while connecting
    try:
        con = lite.connect("{}/{}".format(lingerPath, ARGS.db_name))
        cur = con.cursor()
    except:
        print "Error connecting to database..."

    while True:
        amount = get_device_amount(con)
        if onPi:
            Display.ShowInt(amount)
        sleep(5)

if __name__ == "__main__":
    main()
