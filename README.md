# Linger #

## short ##

Most mobile devices are always searching for wifi networks they have 
been connected to in the past. To do this, your phone is basically 
yelling every name of every network it has ever been connected to 
(at home, at the office or at that one hotel on holiday), to see if 
it will get a response from the router.
These messages contain enough unique information* to use them to 
fingerprint and track individuals, something that is being done by 
different parties and for various reasons. Shops for instance, use 
this data to track how many people walk by, how many actually come 
into the store, and how much time you've spend in the candy isle 
before making your choice.

Linger is a small, portable device that allows you to create and 
blend into a virtual crowd by storing these specific wifi signals 
from everyone that comes near you, and rebroadcasting their signals 
infinitely as if they are still there.
As you pass people in the streets and their signals are stored in 
the database, a small display on the device will show the number of
unique individuals in your group.

Their physical body might have left, but their virtual version will 
stay with you forever.

\* This information can be faked (like Linger is doing) and some 
software even allows you to turn these signals off completely, but 
most devices will send these signals by default (including iPhones 
and most Android devices).

## short (tech version) ##
Linger listens for and stores probe requests coming from WIFI enabled
devices within range. When these devices leave the area (determined 
by the time since their last probe request) it will start resending 
the saved probe requests (with updated sequence numbers), tricking 
other listeners into thinking the device is still there.

## long ##
Most WIFI enabled devices remember the names of all wireless
networks they have been connected to in the past. Whenever
your device is on, but not connected to a network (or sometimes
even when connected), it will broadcast the names of these known
networks (so called probe requests). In theory, when a router
notices a device calling out its name, it will respond by saying
it's there and a connection will be set up.

In practice, this broadcasting of networks names is not needed.
Routers often broadcast their own presence anyway (you know, that
list of network names you can select from when you turn on your
wifi). So instead of asking for known networks, your device can
also wait and listen to find out if a known router is nearby.

The problem with actively sending out probe request is that those
messages contain a 'unique' device number and the name of the network
your device wants to connect to. This can act as a fingerprint to
your device, and by using one of many geolocation databases with
network names, it is trivial to find out where a device (and so,
its user) has been before (think of names like "The Hague Airport",
or "some company name")- a tactic uses by shops and other
commercial parties to track people.

Linger listens for, and saves, probe requests coming from all WIFI
enabled devices that are within reach. When these devices leave
the area (determined by the time since their last probe request)
it will start resending the saved probe requests, tricking others
that might be listening into thinking the other device is still there.

The more devices linger sees, the larger its collection of saved probe
requests will become. This way, a virtual crowd of people will linger
and grow around the device.#

## Setup

There are three parts to this script:
* `linger_rx`: receives probe requests and saves them to `probes.sqlite` by default
* `linger_tx`: transmits probe requests found in the database
* `linger_counter`: gets the amount of unique MAC addresses in the database
and shows this on a 7-segment display.

Copy the three `.sh` files to `/etc/init.d/`. Make sure they are executable 
(`chmod +x linger_*`). Then register them so they are started after booting
by running `sudo update-rc.d <filename> defaults` for each of the three files.

## Links:
To create the startup scripts I used [a tutorial by Stephen C Phillips.](http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/).
The script to control a tm1637 7-segment display from Python was written by [Richard IJzermans](https://raspberrytips.nl/tm1637-4-digit-led-display-raspberry-pi/).
