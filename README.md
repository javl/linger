# Linger #

## short ##
Linger listens for, and saves, probe requests coming from other
WIFI enabled devices. When these devices leave the area (determined
by the time since their last probe request) it will start resending
the saved probe request, tricking other listeners into thinking the
device is still around.

## long ##
Most WIFI enabled devices remember the names of all wireless
networks they have been connected to in the past. Whenever
your device is on, but not connected to a network (or sometimes
even when connected), it will broadcast the names of these known
networks (so called probe requests). In theory, when a router
notices a device calling out its name, it will respond by saying
it's there and a connection will be set up.

In practice, this broadcasting of networks names is not needed.
Routers often broadcast their own presence as well, to every
device in reach. So instead of asking for known networks, your
device canalso wait and listen to find out if a known router
is nearby.

The problem with actively sending out probe request is that those
messages contain a 'unique' device number and the name of the network
your device wants to connect to. This can act as a fingerprint to
your device, and by using one of many geolocation databases with 
network names, it is trivial to find out where a device (and so, 
its user) has been before - a tactic uses by shops and other 
commercial parties to track people.

Linger listens for, and saves, probe requests coming from all WIFI
enabled devices that are within reach. When these devices leave
the area (determined by the time since their last probe request)
it will start resending the saved probe requests, tricking others
that might be listening into thinking the other device is still there.

The more devices linger sees, the larger its collection of saved probe
requests will become. This way, a virtual crowd of people will linger 
and grow around the transmitting device.
