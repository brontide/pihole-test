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


## Running

```
./validate_pihole.py --help
usage: validate_pihole.py [-h] [-q] [--skip-dns-good-site] [--skip-api]
                          [--skip-dns-bad-site] [--skip-web-blocked]
                          [--skip-ping]
                          IP

Remote testing of pi-hole installation

positional arguments:
  IP                    IP address to test

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           Run quietly, only output the error on stderr. Add
                        another and it will only return error codes only
  --skip-dns-good-site  Skip: Query for www.google.com, should return IP that
                        is not pihole
  --skip-api            Skip: Test /admin/api.php to make sure it's responding
  --skip-dns-bad-site   Skip: Query to see if www.doubleclick.net returns
                        pihole ip
  --skip-web-blocked    Skip: Query a random js from site to see that it's
                        return the static file
  --skip-ping           Skip: Probe existance via ping
```

Example run against a functional pihole

```

```
bash$ ./validate_pihole.py 10.195.42.239 
Probe existance via ping                           ... PASS 
Query for www.google.com, should return IP that is not pihole ... PASS www.google.com = 216.58.219.228
Query to see if www.doubleclick.net returns pihole ip ... PASS 10.195.42.239 == 10.195.42.239
Query a random js from site to see that it's return the static file ... PASS 
Test /admin/api.php to make sure it's responding   ... PASS Ad percentage today=36.4
All tests pass on 10.195.42.239
bash$ echo $?
0

Example against centos 6 with broken php

```
bash$ ./validate_pihole.py 10.195.42.176 --skip-ping
Query for www.google.com, should return IP that is not pihole ... PASS www.google.com = 216.58.219.228
Query to see if www.doubleclick.net returns pihole ip ... PASS 10.195.42.176 == 10.195.42.176
Query a random js from site to see that it's return the static file ... PASS 
Test /admin/api.php to make sure it's responding   ... FAIL
OUTPUT:
Get return http status code 500
Testing failed on 10.195.42.176
bash$ echo $?
255
```
