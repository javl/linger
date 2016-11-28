# Linger #
_(needs a better title)_

## short ##
Often smartphones remember every wifi network they have been 
connected to in the past. Your phone will call out the names of 
these know networks to see if it will get a response from a known
router, meaning it should be able to connect again.

This list broadcasted by your device can be seen by anyone who wants
to and can be used to identify indivuals as these data often contain
unique (combinations) of information. One of the uses for this is 
the tracking of costumers in shops (or people passing by within range).
It can be used for things like tracking the amount of visits made and 
the time spend inside (down to specific areas of the store).
Following the logic that these signals can be seen as a person, this 
script generates a large virtual crowd by collecting these messages 
from everyone who comes into range and resending them when they have 
left the area. The physical you might have left, but your digital 
version will stay forever.

## short (tech version)##
Linger listens for, and saves, probe requests coming from WIFI enabled 
devices. When these devices leave the area (determined by the time 
since their last probe request) it will start resending the saved 
probe requests, tricking other listeners into thinking the device 
is still there and creating a virtual crowd.

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
and grow around the transmitting device.
