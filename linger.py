#!/usr/bin/env python

import argparse, threading, time, os, sys
from argparse import RawTextHelpFormatter
import sqlite3 as lite
from scapy.all import *
from random import random

#===========================================================
# Handle arguments
#===========================================================
PARSER = argparse.ArgumentParser(prog='linger', description=
'''Linger listens for, and saves, probe requests coming from other
WIFI enabled devices. When these devices leave the area (determined
by the time since their last probe request) it will start resending
the saved probe request, tricking other listeners into thinking the
device is still around.

For more info on what Linger does see README.md''',
formatter_class=RawTextHelpFormatter)

PARSER.add_argument('-db', default='probes.db', dest='db_name', metavar='filename',\
help='Database name. Defaults to probes.', action='store')

PARSER.add_argument('-f', default='', dest='local_file', metavar='filename',\
help='Use a .pcap file as input instead of a live capture.', action='store')

PARSER.add_argument('-d', dest='drop_database', action='store_true',\
help='Overwrite the database.')

PARSER.add_argument('-t', default='mon0', dest='iface_transmit', metavar='interface',\
help='Transmitter interface. Defaults to mon0.', action='store')

PARSER.add_argument('-r', default='mon1', dest='iface_receive', metavar='interface',\
help='Receiver interface. Defaults to mon1.', action='store')

PARSER.add_argument('-mode', default='3', dest='mode', metavar='number', type=int, \
choices=[1, 2, 3], help='Mode: 1 = scan, 2 = transmit, 3 = both. Defaults to 3.', action='store')

PARSER.add_argument('-v', dest='verbose', action='count',\
help='Verbose; can be used up to 3 times to set the verbose level.')

PARSER.add_argument('--version', action='version', version='%(prog)s version 0.1',\
help='Show program\'s version number and exit.')


ARGS = PARSER.parse_args()
if ARGS.db_name[-3:] != ".db": ARGS.db_name += ".db"

# Stop script if not running as root. Doing this after the argparse so you can still
# read the help info without sudo (using -h / --help flag)
if not os.geteuid() == 0:
    sys.exit('Script must be run as root')

MAX_SN = 4096 # Max value for the 802.11 sequence number field
MAX_FGNUM = 16 # Max value for the 802.11 fragment number field

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
    if ARGS.verbose > 2: print "use sn/sc: %i/%i" % (sn, sc)
    return sc

def randomSN():
    return int(random()*MAX_SN)

#===========================================================
# The packet transmitter class
#===========================================================
class PacketTransmitter(threading.Thread):
    """ Class to transmit probe requests """

    def __init__(self):
        super(PacketTransmitter, self).__init__()
        self.stoprequest = threading.Event()
        #self.local_list = []

        """
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.daemon = True
        self.stoprequest = threading.Event()
        self.con = None
        """

    #=======================================================
    # Get a user
    def send_existing_packets(self):
        con = lite.connect('%s' % ARGS.db_name)
        with con:
            cur = con.cursor()
            cur.execute("SELECT id, command FROM entries \
                WHERE mac = (SELECT mac \
                FROM entries \
                WHERE strftime('%s', last_used) - strftime('%s','now') < -10 \
                ORDER BY last_used ASC LIMIT 1)")

            rows = cur.fetchall()
            if len(rows) != 0:
                SN = randomSN()
                packets = []
                for row in rows:
                    id = int(row[0])
                    command = row[1]
                    p = eval(command)
                    p.SC = calculateSC(SN)
                    packets.append(p)
                    SN+=1
                    cur.execute("UPDATE entries SET last_used=CURRENT_TIMESTAMP WHERE id = ?", (id,))
                    con.commit()

                sendp(packets, iface=ARGS.iface_transmit, verbose=ARGS.verbose>2)

    #=========================================================
    # Keep checking the packages for probe requests
    def run(self):
        if ARGS.verbose > 0: print "Starting PacketTransmitter"
        while not self.stoprequest.isSet():
            self.send_existing_packets()

    #=========================================================
    # Kill the thread when requested
    def die(self, timeout=None):
        self.stoprequest.set()
        #super(WorkerThread, self).join(timeout)

#===========================================================
# The packet retrieval and analyzer class
#===========================================================
class PacketAnalyzer(threading.Thread):
    """ Class to look for probe requests """

    def __init__(self):
        super(PacketAnalyzer, self).__init__()
        self.stoprequest = threading.Event()
        #self.local_list = []

        """
        threading.Thread.__init__(self)
        self.event = threading.Event()
        self.daemon = True
        self.stoprequest = threading.Event()
        self.con = None
        """

    #=======================================================
    # Handle the incoming packet
    def pkt_callback(self, pkt):
        if ARGS.verbose > 2: print "Packet coming in"
        if not self.stoprequest.isSet():
            mac = pkt.addr2
            essid=pkt[Dot11Elt].info.decode('utf-8', 'ignore')
            SN = extractSN(pkt.SC)
            if essid != '':
                con = lite.connect('%s' % ARGS.db_name)
                with con:
                    cur = con.cursor()

                    # TODO: combine these two statements into a single one:
                    # check if combination of mac and essid exists, if so, only update 'last_used'
                    cur.execute("SELECT id from entries WHERE mac=? and essid=?", (mac, essid))
                    if not cur.fetchone():
                        if ARGS.verbose > 0: print "New entry -> %s, %s" % (mac, essid)
                        cur.execute("INSERT INTO entries ('mac', 'essid', 'command', 'sequencenumber', 'added', last_used) \
                            VALUES(?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (mac, essid, pkt.command(), SN))
                        con.commit()
                    else:
                        if ARGS.verbose > 1: print "Entry already exists -> %s, %s" % (mac, essid)
                        cur.execute("UPDATE entries SET last_used=CURRENT_TIMESTAMP WHERE mac=? and essid=?", (mac, essid))


    #=========================================================
    # Keep checking the packages for probe requests
    def run(self):
        if ARGS.verbose > 0: print "Starting PacketAnalyzer"
        if ARGS.local_file != '':
            sniff(offline=ARGS.local_file, prn=pkt_callback, store=0, lfilter = lambda x: x.haslayer(Dot11ProbeReq))
        else:
            while not self.stoprequest.isSet():
                if ARGS.verbose > 2: print "(re)starting sniff()"
                sniff(iface=ARGS.iface_receive, timeout=10, prn=self.pkt_callback, store=0, lfilter = lambda x: x.haslayer(Dot11ProbeReq))

    #=========================================================
    # Kill the thread when requested
    def die(self, timeout=None):
        self.stoprequest.set()
        #super(WorkerThread, self).join(timeout)

#===========================================================
# Main program
#===========================================================
def main():
    """ Main function that starts the packet analyzer and
    the transmitter threads """

    #=========================================================
    # Create a database connection
    if ARGS.verbose > 1: print "Using database %s" % ARGS.db_name
    con = lite.connect('%s' % ARGS.db_name)
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

    #=========================================================
    # Start the packet analyzer thread
    try:
        if ARGS.mode == 1 or ARGS.mode == 3:
            packet_analyzer_thread = PacketAnalyzer()
            packet_analyzer_thread.start()

        if ARGS.mode == 2 or ARGS.mode == 3:
            packet_transmitter_thread = PacketTransmitter()
            packet_transmitter_thread.start()

        while True:#not packet_analyzer.event.isSet():
            time.sleep(100)

    #=========================================================
    # Kill the threads when exiting with ctrl+c
    except (KeyboardInterrupt, SystemExit):
        print ""
        print "Received keyboard interrupt."
        if ARGS.mode == 1 or ARGS.mode == 3:
            print "Please wait for the sniffing thread to end."
            print "This can take up to 10 seconds..."
            packet_analyzer_thread.die()

        if ARGS.mode == 2 or ARGS.mode == 3: packet_transmitter_thread.die()
        exit()

if __name__ == "__main__":
    main()