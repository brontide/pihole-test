# pihole-test

**Testing framework for pihole installation**

Python3 validation testing of pi-hole installtion for
eventual CI.  Script will take an IP and return 0
for pass and -1 for failure.

## Tests

Planned tests include

- ~~ping~~ DONE
- ~~dns query www.google.com should return an ip~~ DONE 
- ~~dns query of bad name should return ip of host~~ DONE
- dns query of good name should return the same as
  a known good dns
- request of http://ip/1.js should show pi-hole 
  based redult
- admin?
- ssh based test of whitelisting/blacklisting?
