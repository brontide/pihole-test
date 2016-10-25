#!/usr/bin/env python3

import subprocess
import dns.resolver
import requests
import argparse
from pprint import pprint
import sys

pidns = dns.resolver.Resolver()
pidns.lifetime = 10

def dns_responds( server, name, rtype='A' ):
    """ This return true if any valid records are returned
    """

    try:
        records = server.query( name, rtype )
        if records:
            return True, "DNS is Alive"
    except dns.exception.DNSException:
        return False, "Query Failed"
  

def dns_NXDOMAIN( server, name, rtype='A' ):
    '''Return true if server replies with NXDOMAIN
    '''

    try:
        records = server.query( name, rtype )
        if records:
            return False,  "%s: %s != NXDOMAIN == %s"%(rtype, name, records[0])
        else:
            return True, "No records for %s"%name
    except dns.resolver.NXDOMAIN:
        return True, "%s: %s == NXDOMAIN"%(rtype, name)
    except dns.exception.DNSException:
        pass
    return True, "Query failure"

def dns_equals( server, name, match, rtype='A' ):
    ''' Returns true is server replies equals match
    '''

    try:
        records = server.query( name, rtype )
        for rec in records:
            if rec.to_text() == match:
                return True, "%s: %s == %s"%(rtype, name, match)
        return False, "%s: %s != %s"%(rtype, name, match)
    except dns.exception.DNSException:
        return False, "Query failure"

def dns_not_equals( server, name, match, rtype='A' ):
    ''' Returns true is server replies does not equals match
    '''

    try:
        records = server.query( name, rtype )
        for rec in records:
            if rec.to_text() == match:
                return False, "%s: %s == %s"%(rtype, name, match)
        return True, "%s: %s != %s"%(rtype, name, match)
    except dns.exception.DNSException:
        return False, "Query failure"

def opt_test_01_ping(args):
    """Probe existance via ping

    """

    ping = subprocess.Popen(
        ["ping", "-c", "4", args.IP],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    out, error = ping.communicate()
    if not ping.returncode:
        return True, "" 
    else:
        return False, "Host not pingable"

def test_04_dns_self(args):
    """DNS pi.hole should return own IP
    """
    (good, result) =  dns_equals(pidns, 'pi.hole', args.IP)
    if good:
        return True, result
    else:
        return False, "%s: Check to see that this is a pi-hole and not firewalled"%result


def test_05_dns_good_site(args):
    """DNS for www.google.com, should return IP that is not pihole
    """
    (good, result) =  dns_not_equals(pidns, 'www.google.com', args.IP)
    if good:
        return True, result
    else:
        return False, "%s: check blacklists"%result

def test_08_dns_localhost(args):
    """DNS localhost should not return IP (or 127.0.0.1)
    """
    ( good, result ) = dns_NXDOMAIN( pidns, 'localhost.')
    ( good2, result2 ) = dns_equals( pidns, 'localhost.', '127.0.0.1')
    if not good:
        if good2:
            return True, "pi.hole returning 127.0.0.1 for localhost"
        else:
            return False, "%s: localhost should be NXDOMAIN"%result
    return True, "NXDOMAIN"

def test_09_dns_localhost_localdomain(args):
    '''DNS localhost.localdomain should be NXDOMAIN
    '''
    ( good, result ) = dns_NXDOMAIN( pidns, 'localhost.localdomain.')
    if not good:
        return False, "%s: should whitelist"%result
    return True, "NXDOMAIN"

def test_10_dns_bad_site(args):
    """DNS query for known ad sites
    """
    sites = [
        'www.doubleclick.net',
        'www.googleadservices.com',
        ]
    for site in sites:
        ( good, result ) = dns_equals( pidns, site, args.IP )
        if not good:
            return False, "%s: Are blacklists setup?"%result
    return True, "Returning pi.hole IP"

def test_50_web_blocked(args):
    """Query a random js from site to see that it's return the static file
    """
    try:
        r = requests.get("http://%s/1.js"%(args.IP), timeout=5.0)
        if not r.status_code == requests.codes.ok:
            return False, "Got return http status code %i"%r.status_code 
        if 'var x = "Pi-hole: A black hole for Internet advertisements."' in r.text:
            return True, r.text.strip()
        else:
            return False, "Wrong answer from server, check lighttpd"
    except:
        return False, "Error/Timeout in http request, make sure web server is operational and not firewalled"

def test_51_admin_ok(args):
    """Query admin/js/other/app.min.js and make sure it's reasonable size
    """
    try:
        r = requests.get("http://%s/admin/js/other/app.min.js"%(args.IP), timeout=5.0)
        if not r.status_code == requests.codes.ok:
            return ( False, "Got return http status code %i"%r.status_code )
        if len(r.text)>300:
            return  True, r.text.splitlines()[0].strip()
        else:
            return  False, "Wrong answer from server, check lighttpd" 
    except:
        return False, "Error/Timeout in http request, make sure web server is operational and not firewalled"

def test_55_api(args):
    """Test /admin/api.php to make sure it's responding
    """
    try:
        r = requests.get("http://%s/admin/api.php?summary"%(args.IP), timeout=5.0, headers={'host':'pi.hole'})
        if not r.status_code == requests.codes.ok:
            return False, "Get return http status code %i"%r.status_code 
        if r.json():
            return True, "Ad percentage today=%s"%(r.json()['ads_percentage_today'])
        else:
            return  False, "Malformed json %s"%r.text 
    except:
        return  False, "Error/Timeout/json failure in http request, make sure web server is operational and not firewalled" 

def run_tests(args):
    for name,func in sorted( (name,func) for name, func in globals().items() if 'test_' in name and not args.__dict__[name]):
        test_str = func.__doc__.strip()
        if not args.quiet:
            print("%-80s ... "%test_str, end="", flush=True)
        (good, out ) = func(args)
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
        if 'opt_' in name:
            alt = "--enable-%s"%(name.split('_', 3)[3].replace('_','-'))
            parser.add_argument(alt, action='store_false', dest=name, help="Enable: %s"%(func.__doc__.strip()))
        else:
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


