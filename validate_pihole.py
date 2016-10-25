#!/usr/bin/env python3

import subprocess
import dns.resolver
import requests
import argparse
from pprint import pprint
import sys

pidns = dns.resolver.Resolver()
pidns.lifetime = 10
regdns = dns.resolver.Resolver()
regdns.lifetime = 10
regdns.nameservers = [ '8.8.8.8', '8.8.4.4' ]

def test_01_ping(args):
    """Probe existance via ping

    """

    ping = subprocess.Popen(
        ["ping", "-c", "4", args.IP],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    out, error = ping.communicate()
    if not ping.returncode:
        return ( True, "" )
    else:
        return ( False, "Host not pingable" )


def test_05_dns_good_site(args):
    """Query for www.google.com, should return IP that is not pihole
    """
    try:
        data = pidns.query('www.google.com')
        if data:
            return ( True, "www.google.com = %s"%(data[0])  )
    except dns.resolver.NXDOMAIN:
        return ( False, "Server doesn't know www.google.com, is this s real DNS?" )
    except dns.exception.DNSException as e:
        return ( False, "Query Failed, is DNS running and not firewalled?" )


def test_10_dns_bad_site(args):
    """Query to see if www.doubleclick.net returns pihole ip
    """

    try:
        data = pidns.query('www.doubleclick.net.')
        if data and data[0].to_text() == args.IP:
            return ( True, "%s == %s"%(data[0],args.IP)  )
        else:
            return ( False, "%s != %s"%(data[0],args.IP)  )
    except dns.resolver.NXDOMAIN:
        return ( False, "Server doesn't know pihole. Its' likely that this is a DNS server but not a pihole" )
    except dns.exception.DNSException as e:
        return ( False, "Query Failed, is DNS running and not firewalled?" )

def test_50_web_blocked(args):
    """Query a random js from site to see that it's return the static file
    """
    try:
        r = requests.get("http://%s/1.js"%(args.IP), timeout=5.0)
        if not r.status_code == requests.codes.ok:
            return ( False, "Get return http status code %i"%r.status_code )
        if 'var x = "Pi-hole: A black hole for Internet advertisements."' in r.text:
            return ( True, "")
    except:
        return ( False, "Error/Timeout in http request, make sure web server is operational and not firewalled" )

def test_55_api(args):
    """Test /admin/api.php to make sure it's responding
    """
    try:
        r = requests.get("http://%s/admin/api.php?summary"%(args.IP), timeout=5.0)
        if not r.status_code == requests.codes.ok:
            return ( False, "Get return http status code %i"%r.status_code )
        if r.json():
            return ( True, "Ad percentage today=%s"%(r.json()['ads_percentage_today']))
    except:
        return ( False, "Error/Timeout/json failure in http request, make sure web server is operational and not firewalled" )

def run_tests(args):
    for name,func in sorted( (name,func) for name, func in globals().items() if 'test_' in name and not args.__dict__[name]):
        test_str = func.__doc__.strip()
        if not args.quiet:
            print("%-50s ... "%test_str, end="", flush=True)
        (good, out  ) = func(args)
        if good and not args.quiet:
            print("PASS %s"%out)
        if not good:
            if args.quiet: print("%s "%test_str, end="")
            print("FAIL")
            if out and not args.quiet:
                print("OUTPUT:\n%s"%(out))
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Remote testing of pi-hole installation")
    parser.add_argument('-q','--quiet',action='count',help="Run quietly, only output the error on stderr. Add another and it will only return error codes only")
    parser.add_argument('IP', help="IP address to test")
    for name,func in ( (name,func) for name,func in globals().items() if 'test_' in name):
        alt = "--skip-%s"%(name.split('_', 2)[2].replace('_','-'))
        parser.add_argument(alt, action='store_true', dest=name, help="Skip: %s"%(func.__doc__.strip()))
    args = parser.parse_args()
    
    pidns.nameservers = [ args.IP ]
    if run_tests(args):
        if not args.quiet: print("All tests pass on %s"%(args.IP))
    else:
        print("Testing failed on %s"%(args.IP))
        sys.exit(-1)

if __name__ == "__main__": main()


