#!/bin/bash
# /etc/init.d/linger_rx

### BEGIN INIT INFO
# Provides:          linger_rx
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: linger_rx
# Description:       This service is used to capture probe requests
### END INIT INFO

case "$1" in
    start)
        # Wait 5 seconds for tty1 to become ready. Must be a cleaner way?
        sleep 5
        echo "Starting linger_rx" > /dev/tty1
        sudo airmon-ng start wlan1 1>/dev/null 2>/home/pi/linger/log
        sudo /home/pi/linger/linger_rx.py -i mon0 -v 1> /dev/tty1 2>/home/pi/linger/log
        ;;
    stop)
        echo "Stopping linger_rx" > /dev/tty1
        sudo kill `ps -eo pid,command | grep "linger_rx.py" | grep -v grep | head -1 | awk '{print $1}'`1>/dev/null 2>/home/pi/linger/log
        sudo airmon-ng stop mon0 1>/dev/null
        echo "Done" > /dev/tty1
        ;;
    *)
        echo "Usage: /etc/init.d/linger_rx start|stop"
        exit 1
        ;;
esac

exit 0
