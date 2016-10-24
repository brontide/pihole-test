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


def test_05_dns_home(args):
    """Is the DNS responding

    """
    try:
        data = pidns.query('www.google.com')
        if data:
            return ( True, "www.google.com = %s"%(data[0])  )
    except dns.resolver.NXDOMAIN:
        return ( False, "Server doesn't know www.google.com, is this s real DNS?" )
    except dns.exception.DNSException as e:
        return ( False, "Query Failed, is DNS running and not firewalled?" )


def test_10_dns_pihole(args):
    """Does it block www.doubleclick.net?
    
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

def run_tests(args):
    for name,func in sorted( (name,func) for name, func in globals().items() if 'test_' in name):
        test_str = func.__doc__.strip()
        if not args.quiet:
            print("%-50s ... "%test_str, end="", flush=True)
        (good, out  ) = func(args)
        if good:
            print("PASS %s"%out)
        else:
            print("FAIL")
            if out and not args.quiet:
                print("OUTPUT:\n%s"%(out))
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Remote testing of pi-hole installation")
    parser.add_argument('-q','--quiet',action='count',help="Run quietly, only output the error on stderr. Add another and it will only return error codes only")
    parser.add_argument('IP', help="IP address to test")
    args = parser.parse_args()
    
    pidns.nameservers = [ args.IP ]
    if run_tests(args):
        print("All tests pass on %s"%(args.IP))
    else:
        print("Testing failed on %s"%(args.IP))
        sys.exit(-1)

if __name__ == "__main__": main()


