# pihole-test

**Testing framework for pihole installation**

Python3 validation testing of pi-hole installtion for
eventual CI.  Script will take an IP and return 0
for pass and -1 for failure.

**Requirements**

- dnspython3
- requests
- joblib

`pip3 install [--user] dnspython3 requests joblib`

## Tests

Planned tests include

- ~~ping~~ DONE
- ~~dns query www.google.com should return an ip~~ DONE 
- ~~dns query of bad name should return ip of host~~ DONE
- ~~dns over tcp~~
- ~~stress testing~~
- dns query of good name should return the same as
  a known good dns
- ~~request of http://ip/1.js should show pi-hole 
  based redult~~
- admin?
- ssh based test of whitelisting/blacklisting?
- v6 ( over v6 and v6 blocking )


## Running

```
bash$ ./validate_pihole.py -h
usage: validate_pihole.py [-h] [-q] [--skip-ping]
                          [--ping-timeout PING_TIMEOUT] [--skip-dns-good-site]
                          [--skip-dns-localhost] [--enable-stresstest]
                          [--stress-count STRESS_COUNT]
                          [--stress-threads STRESS_THREADS]
                          [--skip-dns-bad-site] [--skip-web-blocked]
                          [--skip-api] [--skip-api-data] [--skip-dns-self]
                          [--skip-admin-ok] [--skip-dns-good-tcp]
                          [--skip-dns-bad-tcp]
                          [--skip-dns-localhost-localdomain]
                          IP

Remote testing of pi-hole installation

positional arguments:
  IP                    IP address to test

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           Run quietly, only output the error on stderr. Add
                        another and it will only return error codes only
  --skip-ping           Skip: Probe existance via ping
  --ping-timeout PING_TIMEOUT
                        Default: 30
  --skip-dns-good-site  Skip: DNS for good sites, should return IP that is not
                        pihole
  --skip-dns-localhost  Skip: DNS localhost should not return IP (or
                        127.0.0.1)
  --enable-stresstest   Enable: Throw {stress_count} domains at the pihole via
                        {stress_threads} threads
  --stress-count STRESS_COUNT
                        Default: 2000
  --stress-threads STRESS_THREADS
                        Default: 50
  --skip-dns-bad-site   Skip: DNS query for known ad sites
  --skip-web-blocked    Skip: Query a random js from site to see that it's
                        return the static file
  --skip-api            Skip: Test /admin/api.php to make sure it's responding
  --skip-api-data       Skip: Test data dump to make sure it's responding
                        quickly
  --skip-dns-self       Skip: DNS pi.hole should return own IP
  --skip-admin-ok       Skip: Query admin/js/other/app.min.js and make sure
                        it's reasonable size
  --skip-dns-good-tcp   Skip: DNS for good sites over tcp
  --skip-dns-bad-tcp    Skip: DNS query for known ad sites over tcp
  --skip-dns-localhost-localdomain
                        Skip: DNS localhost.localdomain should be NXDOMAIN

```

Example run against a functional pihole

```
bash$ ./validate_pihole.py --enable-stresstest 10.195.42.2
Probe existance via ping                                                         ... PASS Ping... pong!
DNS pi.hole should return own IP                                                 ... PASS pi.hole == 10.195.42.2
DNS for good sites, should return IP that is not pihole                          ... PASS www.google.com www.facebook.com www.yahoo.com GOOD
DNS for good sites over tcp                                                      ... PASS www.google.com www.facebook.com www.yahoo.com GOOD
DNS localhost should not return IP (or 127.0.0.1)                                ... PASS pi.hole returning 127.0.0.1 for localhost
DNS localhost.localdomain should be NXDOMAIN                                     ... PASS NXDOMAIN
DNS query for known ad sites                                                     ... PASS www.doubleclick.net www.googleadservices.com rad.msn.com ads.google.com ad5.liverail.com BLOCKED
DNS query for known ad sites over tcp                                            ... PASS www.doubleclick.net www.googleadservices.com rad.msn.com ads.google.com ad5.liverail.com BLOCKED
Throw 2000 domains at the pihole via 50 threads                                  ... PASS 1988/12 min 0.63ms avg 220.00ms max 6746.62ms std 516.91ms
Query a random js from site to see that it's return the static file              ... PASS var x = "Pi-hole: A black hole for Internet advertisements."
Query admin/js/other/app.min.js and make sure it's reasonable size               ... PASS /*! AdminLTE app.js
Test /admin/api.php to make sure it's responding                                 ... PASS Ad percentage today=4.0
Test data dump to make sure it's responding quickly                              ... PASS Got 2190 queries
All tests pass on 10.195.42.2
bash$ echo $?
0
```

Example against centos 6 with broken php

```
bash$ ./validate_pihole.py --enable-stresstest 10.195.42.126
Probe existance via ping                                                         ... PASS Ping... pong!
DNS pi.hole should return own IP                                                 ... PASS pi.hole == 10.195.42.126
DNS for good sites, should return IP that is not pihole                          ... PASS www.google.com www.facebook.com www.yahoo.com GOOD
DNS for good sites over tcp                                                      ... PASS www.google.com www.facebook.com www.yahoo.com GOOD
DNS localhost should not return IP (or 127.0.0.1)                                ... PASS pi.hole returning 127.0.0.1 for localhost
DNS localhost.localdomain should be NXDOMAIN                                     ... PASS NXDOMAIN
DNS query for known ad sites                                                     ... PASS www.doubleclick.net www.googleadservices.com rad.msn.com ads.google.com ad5.liverail.com BLOCKED
DNS query for known ad sites over tcp                                            ... PASS www.doubleclick.net www.googleadservices.com rad.msn.com ads.google.com ad5.liverail.com BLOCKED
Throw 2000 domains at the pihole via 50 threads                                  ... PASS 1993/7 min 0.69ms avg 208.00ms max 10998.59ms std 512.38ms
Query a random js from site to see that it's return the static file              ... PASS var x = "Pi-hole: A black hole for Internet advertisements."
Query admin/js/other/app.min.js and make sure it's reasonable size               ... PASS /*! AdminLTE app.js
Test /admin/api.php to make sure it's responding                                 ... FAIL
OUTPUT:
Get return http status code 500
Testing failed on 10.195.42.126
bash$ echo $?
255
```
