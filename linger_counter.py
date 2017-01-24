#!/usr/bin/env python

try:
    from lingerSettings import *
except:
    # if we can't find alternative settings, use the RPi path
    lingerPath = "/home/pi/linger"

import argparse, time, os, platform, sys
from argparse import RawTextHelpFormatter
import sqlite3 as lite

onPi = True
if platform.machine() != "armv7l":
    onPi = False

if onPi:
    import RPi.GPIO as GPIO
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
if not os.geteuid() == 0:
    sys.exit('Script must be run as root')

# Add .sqlite to our database name if needed
if ARGS.db_name[-7:] != ".sqlite": ARGS.db_name += ".sqlite"

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
        cur.execute("SELECT COUNT(DISTINCT mac) AS amount FROM entries")
        return cur.fetchone()[0]

#===========================================================
# Main program
#===========================================================
def main():
    if onPi:
        Display = tm1637.TM1637(23,24,tm1637.BRIGHT_TYPICAL)
        Display.Clear()
        Display.SetBrightnes(3)

    #=========================================================
    # Create a database connection
    if ARGS.verbose > 1: print "Using database {}/{}".format(lingerPath, ARGS.db_name)
    con = lite.connect("{}/{}".format(lingerPath, ARGS.db_name))
    cur = con.cursor()
    while True:
        amount = get_device_amount(con)
        if onPi:
            Display.ShowInt(amount)
        time.sleep(5)

if __name__ == "__main__":
    main()
