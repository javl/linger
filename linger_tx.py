#!/usr/bin/env python

# Stop script if not running as root. Doing this after the argparse so you can still
# read the help info without sudo (using -h / --help flag)
import os, sys
if not os.geteuid() == 0:
    sys.exit('Script must be run as root')

try:
    from lingerSettings import *
except:
    lingerPath = "/home/pi/linger"

import argparse, threading, time, subprocess, re, signal
from argparse import RawTextHelpFormatter
import sqlite3 as lite
from scapy.all import *
from random import random

#==============================================================================
import logging
logging_config = {
    'filename': '/var/log/linger_tx.log',
    'format': '%(asctime)s [%(levelname)s] %(message)s',
    'level': logging.WARNING
}
logging.basicConfig(**logging_config)
#===========================================================
# Handle arguments
#===========================================================
PARSER = argparse.ArgumentParser(prog='linger', description=
'''This is the sender part of Linger, which listens for, and saves,
probe requests coming from other WIFI enabled devices, and will
replay them after the original device has left the area.
For more info on what Linger
does see README.md''',
formatter_class=RawTextHelpFormatter)

PARSER.add_argument('-db', default='probes', dest='db_name', metavar='filename',\
help='Database name. Defaults to probes.', action='store')

PARSER.add_argument('-i', default='wlan2', dest='iface_transmit', metavar='interface',\
help='Transmitter interface. Defaults to wlan2.', action='store')

PARSER.add_argument('-v', dest='verbose', action='count',\
help='Verbose; can be used up to 3 times to set the verbose level.')

PARSER.add_argument('--version', action='version', version='%(prog)s version 0.1.0',\
help='Show program\'s version number and exit.')


ARGS = PARSER.parse_args()

# Add .sqlite to our database name if needed
if ARGS.db_name[-7:] != ".sqlite": ARGS.db_name += ".sqlite"

# Creating this here so we can use it globally later
monitorIface = None

MAX_SN = 4096 # Max value for the 802.11 sequence number field
MAX_FGNUM = 16 # Max value for the 802.11 fragment number field

# Functions used to catch a kill signal so we can cleanly
# exit (like storing the database)
def set_exit_handler(func):
    signal.signal(signal.SIGTERM, func)

def on_exit(sig, func=None):
    global monitorIface
    if ARGS.verbose > 0: print "Received kill signal. Stop monitor mode and exit"
    result = subprocess.check_output("sudo airmon-ng stop {}".format(monitorIface), shell=True)
    sys.exit(1)

#=======================================================
# Get the sequence number
def extractSN(sc):
    hexSC = '0' * (4 - len(hex(sc)[2:])) + hex(sc)[2:] # "normalize" to four digit hexadecimal number
    sn = int(hexSC[:-1], 16)
    return sn

#=======================================================
# Generate a sequence number
def calculateSC(sn, fgnum=0):
    if (sn > MAX_SN): sn = sn - MAX_SN
    if fgnum > MAX_FGNUM: fgnum = 0
    hexSN = hex(sn)[2:] + hex(fgnum)[2:]
    sc = int(hexSN, 16)
    if ARGS.verbose > 2: print "use sn/sc: {}/{}".format(sn, sc)
    return sc

def randomSN():
    return int(random()*MAX_SN)

#=======================================================
# Get a user
def send_existing_packets(con):
    global monitorIface
    with con:
        cur = con.cursor()
        cur.execute("SELECT id, mac, essid, command FROM entries \
            WHERE mac = (SELECT mac \
            FROM entries \
            WHERE strftime('%s', last_used) - strftime('%s','now') < -10 \
            ORDER BY last_used ASC LIMIT 1)")

        rows = cur.fetchall()
        if len(rows) != 0:
            SN = randomSN()
            packets = []
            if ARGS.verbose > 1: print "Mac address: ", rows[0][1];
            logging.debug('Mac address: {}'.format(rows[0][1]))
            for row in rows:
                if ARGS.verbose > 1: print "--> ", row[2];
                logging.debug('--> {}'.format(row[2]))
                id = int(row[0])
                command = row[3]
                p = eval(command)
                p.SC = calculateSC(SN)
                packets.append(p)
                SN+=1
                cur.execute("UPDATE entries SET last_used=CURRENT_TIMESTAMP WHERE id = ?", (id,))
                con.commit()
            sendp(packets, iface=monitorIface, verbose=ARGS.verbose>2)

#===========================================================
# Main program
#===========================================================
def main():
    # Start monitor mode
    if ARGS.verbose > 0: print "start monitor mode on: ", ARGS.iface_transmit
    result = subprocess.check_output("sudo airmon-ng start {}".format(ARGS.iface_transmit), shell=True)
    if ARGS.verbose > 2: print "result: ", result
    m = re.search("\(monitor mode enabled on (.+?)\)", result)
    if m:
        monitorIface = m.groups()[0]
    else:
        print "Something went wrong enabling monitor mode."
        sys.exit(0)

    #=========================================================
    # Create a database connection
    if ARGS.verbose > 1: print "Using database {}".format(ARGS.db_name)
    logging.info("Using database {}".format(ARGS.db_name));
    con = lite.connect("{}/{}".format(lingerPath, ARGS.db_name))
    cur = con.cursor()

    while True:
        send_existing_packets(con)

if __name__ == "__main__":
    set_exit_handler(on_exit)
    main()
