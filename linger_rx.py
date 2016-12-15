#!/usr/bin/env python

try:
    from lingerSettings import *
except:
    lingerPath = "/home/pi/linger"

import os, sys, signal, argparse, subprocess, re
from argparse import RawTextHelpFormatter
import sqlite3 as lite
from scapy.all import *
from random import random

#path = "/home/pi/linger"
#path = "/home/javl/Projects/linger"
#===========================================================
# Handle arguments
#===========================================================
PARSER = argparse.ArgumentParser(prog='linger', description=
'''This is the receiver part of Linger, which listens for,
and saves, probe requests coming from other WIFI enabled devices,
and will replay them after the original device has left the area.
For more info see README.md''',
formatter_class=RawTextHelpFormatter)

PARSER.add_argument('-db', default='probes.sqlite', dest='db_name', metavar='filename',\
help='Name of database to use. Defaults to "probes".', action='store')

PARSER.add_argument('-d', dest='drop_database', action='store_true',\
help='Drop the database before starting. Will ask for confirmation.')

PARSER.add_argument('-i', default='wlan1', dest='iface_receive', metavar='interface',\
help='Interface to use for receiving packets. Defaults to wlan1.', action='store')

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

# Creating this here so we can use it globally later
monitorIface = None

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
# Extract a sequence number
#=======================================================
def extractSN(sc):
    hexSC = '0' * (4 - len(hex(sc)[2:])) + hex(sc)[2:] # "normalize" to four digit hexadecimal number
    sn = int(hexSC[:-1], 16)
    return sn

#=======================================================
# Handle incoming packets
#=======================================================
def pkt_callback(pkt):
    if ARGS.verbose > 2: print "Packet coming in"
    mac = pkt.addr2
    essid = pkt[Dot11Elt].info.decode('utf-8', 'ignore')
    SN = extractSN(pkt.SC)
    if essid != '':
        con = lite.connect('{}/{}'.format(lingerPath, ARGS.db_name))
        with con:
            cur = con.cursor()

            # TODO: combine these two statements into a single one:
            # check if combination of mac and essid exists, if so, only update 'last_used'
            cur.execute("SELECT id from entries WHERE mac=? and essid=?", (mac, essid))
            if not cur.fetchone():
                if ARGS.verbose > 0: print "New entry -> {}, {}".format(mac, essid)
                cur.execute("INSERT INTO entries ('mac', 'essid', 'command', 'sequencenumber', 'added', last_used) \
                    VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (mac, essid, pkt.command(), SN))
                con.commit()
            else:
                if ARGS.verbose > 1: print "Entry already exists -> {}, {}".format(mac, essid)
                cur.execute("UPDATE entries SET last_used=CURRENT_TIMESTAMP WHERE mac=? and essid=?", (mac, essid))

#===========================================================
# Main loop
#===========================================================
def main():
    global monitorIface
    # Start monitor mode
    print "start monitor mode on: ", ARGS.iface_receive
    result = subprocess.check_output("sudo airmon-ng start {}".format(ARGS.iface_receive), shell=True)
    print "Result: ", result
    m = re.search("\(monitor mode enabled on (.+?)\)", result)
    if m:
        monitorIface = m.groups()[0]
    else:
        print "Something went wrong enabling monitor mode."
        sys.exit(0)
    #=========================================================
    # Create a database connection
    if ARGS.verbose > 1: print "Using database {}".format(ARGS.db_name)
    con = lite.connect('{}/{}'.format(lingerPath, ARGS.db_name))
    with con:
        cur = con.cursor()
        #=======================================================
        # Delete database if requested
        if ARGS.drop_database:
            if raw_input("Drop the database? (y/n) [n] ") == 'y':
                cur.execute('DROP TABLE IF EXISTS entries')

        #=======================================================
        # Create the database if it doesn't exist yet
        cur.execute('CREATE TABLE IF NOT EXISTS "main"."entries" \
            ("id" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL , \
            "mac" TEXT, \
            "essid" TEXT, \
            "command" TEXT, \
            "sequencenumber" INT, \
            "added" DATETIME DEFAULT CURRENT_TIMESTAMP, \
            "last_used" DATETIME DEFAULT CURRENT_TIMESTAMP)')

    # Start looking for packets
    if ARGS.verbose > 0: print "Starting linger_rx on {} with database {}".format(monitorIface, ARGS.db_name)
    sniff(iface=monitorIface, prn=pkt_callback, store=0, lfilter = lambda x: x.haslayer(Dot11ProbeReq))


if __name__ == "__main__":
    # Set our handler for kill signals
    set_exit_handler(on_exit)
    main()
