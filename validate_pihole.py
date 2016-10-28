#!/usr/bin/env python3
'''

Validation script for pi-hole to confirm external operation of all the parts.

Functions named test_* are automatically picked up and
run automatically based on their sortable value.  The system will
stop and return -1 on the first failure.

test_value_name are added to the command line with their doc string
  and an option to skip

opt_test_value_name are added as optional with a command line
  enable function


'''

import inspect
import subprocess
import dns.resolver
import requests
import argparse
import random
from contexttimer import Timer
from pprint import pprint
import sys

pidns = dns.resolver.Resolver()

##################
# some variables

hosts_spam = [
        'www.doubleclick.net',
        'www.googleadservices.com',
        'rad.msn.com',
        'ads.google.com',
        'ad5.liverail.com',
        ]

hosts_ham = [
        'www.google.com',
        'www.facebook.com',
        'www.yahoo.com',
    ]

def dns_responds( server, name, tcp=False ):
    """
    This return true if any valid records are returned
    """

    try:
        records = server.query( name, tcp=tcp )
        if records:
            return True, "DNS is Alive"
    except dns.exception.DNSException:
        return False, "Query Failed"

def dns_any( server, name, rtype="A", tcp=False ):
    '''
    Returns number of records. Timeouts 
    should throw an exception.  Useful for
    stress testing the DNS.
    '''  

    try:
        records = server.query( name, tcp=tcp )
        if records: return len(records)
    except dns.resolver.NXDOMAIN:
        return 0
    except dns.resolver.NoAnswer:
        return 0
    except dns.resolver.NoNameservers:
        return 0

def dns_NXDOMAIN( server, name, tcp=False ):
    '''
    Return true if server replies with NXDOMAIN
    '''

    try:
        records = server.query( name, tcp=tcp )
        if records:
            return False,  "%s != NXDOMAIN == %s"%(name, records[0])
        else:
            return True, "No records for %s"%name
    except dns.resolver.NXDOMAIN:
        return True, "%s == NXDOMAIN"%( name)
    except dns.exception.DNSException:
        pass
    return True, "Query failure"

def dns_equals( server, name, match, tcp=False ):
    ''' 
    Returns true is server replies equals match
    '''

    try:
        records = server.query( name, tcp=tcp )
        for rec in records:
            if rec.to_text() == match:
                return True, "%s == %s"%(name, match)
        return False, "%s != %s"%(name, match)
    except dns.exception.DNSException:
        return False, "Query failure"

def dns_not_equals( server, name, match, tcp=False ):
    ''' 
    Returns true is server replies does not equals match
    '''

    try:
        records = server.query( name, tcp=tcp )
        for rec in records:
            if rec.to_text() == match:
                return False, "(%s)%s == %s"%(name, rec.to_text(), match)
        return True, "(%s)%s != %s"%(name, records[0], match)
    except dns.exception.DNSException:
        return False, "Query failure"

def a1_test_ping(IP=None, ping_timeout=30, **kwargs):
    """
    Probe existance via ping
    """

    for i in range(ping_timeout):
        ping = subprocess.Popen(
            ["ping", "-c", "1", IP],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )

        out, error = ping.communicate()
        if not ping.returncode:
            return True, "Ping... pong!" 
    return False, "Host not pingable"

def a4_test_dns_self(IP=None, **kwargs):
    """
    DNS pi.hole should return own IP
    """
    (good, result) =  dns_equals(pidns, 'pi.hole', IP)
    if good:
        return True, result
    else:
        return False, "%s: Check to see that this is a pi-hole and not firewalled"%result


def a5_test_dns_good_site(IP=None, **kwargs):
    """
    DNS for good sites, should return IP that is not pihole
    """
    for host in hosts_ham:
        (good, result) =  dns_not_equals(pidns, host, IP)
        if not good:
            return False, "%s: check blacklists"%result
    return True, "%s GOOD"%(" ".join(hosts_ham))

def a5_test_dns_good_tcp(IP=None, **kwargs):
    """
    DNS for good sites over tcp
    """
    for host in hosts_ham:
        (good, result) =  dns_not_equals(pidns, host, IP, tcp=True)
        if not good:
            return False, "%s: check blacklists and firewall 53/tcp"%result
    return True, "%s GOOD"%(" ".join(hosts_ham))

def a8_test_dns_localhost(**kwargs):
    """
    DNS localhost should not return IP (or 127.0.0.1)
    """
    ( good, result ) = dns_NXDOMAIN( pidns, 'localhost.')
    if not good:
        ( good2, result2 ) = dns_equals( pidns, 'localhost.', '127.0.0.1')
        if good2:
            return True, "pi.hole returning 127.0.0.1 for localhost"
        else:
            return False, "%s: localhost should be NXDOMAIN"%result
    return True, "NXDOMAIN"

def a9_test_dns_localhost_localdomain(**kwargs):
    '''
    DNS localhost.localdomain should be NXDOMAIN
    '''
    ( good, result ) = dns_NXDOMAIN( pidns, 'localhost.localdomain.')
    if not good:
        return False, "%s: execute `pihole -w localhost.localdomain` to clear error"%result
    return True, "NXDOMAIN"

def b1_test_dns_bad_site(IP=None, **kwargs):
    """
    DNS query for known ad sites
    """
    for site in hosts_spam:
        ( good, result ) = dns_equals( pidns, site, IP )
        if not good:
            return False, "%s: Are blacklists setup?"%result
    return True, "%s BLOCKED"%(" ".join(hosts_spam))

def b1_test_dns_bad_tcp(IP=None, **kwargs):
    """
    DNS query for known ad sites over tcp
    """
    for site in hosts_spam:
        ( good, result ) = dns_equals( pidns, site, IP, tcp=False )
        if not good:
            return False, "%s: Are blacklists setup and firewall open?"%result
    return True, "%s BLOCKED"%(" ".join(hosts_spam))

def dns_stress(IP,host):
    mydns = dns.resolver.Resolver()
    mydns.nameservers=[IP]
    with Timer() as t:
        try:
            dns_any(mydns, host, tcp=(random.random())>0.5)
            return ('good', t.elapsed)
        except:        
            return ('bad', t.elapsed)

def h0_opt_test_stresstest(IP=None, stress_count=2000, stress_threads=50, **kwargs):
    '''
    Throw {stress_count} domains at the pihole via {stress_threads} threads
    '''

    from joblib import Parallel, delayed
    
    top_array = open('topsites.txt').read().splitlines()
    random.shuffle(top_array)
   
    results = Parallel(n_jobs=stress_threads, backend='threading' )(delayed(dns_stress)(IP, site) for site in top_array[:stress_count])
    good = sum( 1 for (a,b) in results if a == 'good' )
    numbers = [ b for (a,b) in results if a == 'good' ]
    bad = sum( 1 for (a,b) in results if a == 'bad' )
    vmin = min(numbers)*1000
    vmax = max(numbers)*1000
    vavg = sum(numbers)*1000//len(numbers)
    vstd = (sum(((n*1000) - vavg) ** 2 for n in numbers) / len(numbers)) ** .5

    return not bad or (good/bad)>0.05, "{good}/{bad} min {vmin:.2f}ms avg {vavg:.2f}ms max {vmax:.2f}ms std {vstd:.2f}ms".format(**locals())

def m0_test_web_blocked(IP=None, **kwargs):
    """
    Query a random js from site to see that it's return the static file
    """
    try:
        r = requests.get("http://%s/1.js"%(IP), timeout=1.0)
        if not r.status_code == requests.codes.ok:
            return False, "Got return http status code %i"%r.status_code 
        if 'var x = "Pi-hole: A black hole for Internet advertisements."' in r.text:
            return True, r.text.strip()
        else:
            return False, "Wrong answer from server, check lighttpd"
    except:
        return False, "Error/Timeout in http request, make sure web server is operational and not firewalled"

def m1_test_admin_ok(IP=None, **kwargs):
    """
    Query admin/js/other/app.min.js and make sure it's reasonable size
    """
    try:
        r = requests.get("http://%s/admin/js/other/app.min.js"%(IP), timeout=4.0)
        if not r.status_code == requests.codes.ok:
            return ( False, "Got return http status code %i"%r.status_code )
        if len(r.text)>300:
            return  True, r.text.splitlines()[0].strip()
        else:
            return  False, "Wrong answer from server, check lighttpd" 
    except:
        return False, "Error/Timeout in http request, make sure web server is operational and not firewalled"

def m5_test_api(IP=None, **kwargs):
    """
    Test /admin/api.php to make sure it's responding
    """
    try:
        with Timer() as t:
            r = requests.get("http://%s/admin/api.php?summary"%(IP), timeout=2.0, headers={'host':'pi.hole'})
            if not r.status_code == requests.codes.ok:
                return False, "Get return http status code %i"%r.status_code 
            if r.json():
                return True, "Ad percentage today={} in {:.2f}ms".format(r.json()['ads_percentage_today'],t.elapsed*1000)
            else:
                return  False, "Malformed json %s"%r.text 
    except:
        return  False, "Error/Timeout/json failure in http request, make sure web server is operational and not firewalled" 

def m6_test_api_data(IP=None, **kwargs):
    """
    Test data dump to make sure it's responding quickly
    """
    try:
        with Timer() as t:
            r = requests.get("http://%s/admin/api.php?getAllQueries"%(IP), timeout=4.0, headers={'host':'pi.hole'})
            if not r.status_code == requests.codes.ok:
                return False, "Get return http status code %i"%r.status_code 
            if r.json():
                return True, "Got {} queries in {:.2f}ms".format(len(r.json()['data']), t.elapsed*1000)
            else:
                return  False, "Malformed json %s"%r.text 
    except:
        return  False, "Error/Timeout/json failure in http request, make sure web server is operational and not firewalled" 




#############################################################################################################################
# Functions below do not need to be changed when adding or removing tests

def run_tests(**kwargs):
    """
    This function does the bulk of the processing, walking the list of functions in the module
    and running them if they have not been excluded
    """
    for name,func in sorted( (name,func) for name, func in globals().items() if 'test_' in name and not kwargs[name]):
        test_str = inspect.getdoc(func).format(**kwargs)
        if not kwargs['quiet']:
            print("%-80s ... "%test_str, end="", flush=True)
        (good, out ) = func(**kwargs)
        if good and not kwargs['quiet']:
            print("PASS %s"%out)
        if not good:
            if kwargs['quiet']: print("%s "%test_str, end="")
            print("FAIL")
            if out and not kwargs['quiet']:
                print("OUTPUT:\n%s"%(out))
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Remote testing of pi-hole installation")
    parser.add_argument('-q','--quiet',action='count',help="Run quietly, only output the error on stderr. Add another and it will only return error codes only")
    parser.add_argument('IP', help="IP address to test")
    for name,func in [ (name,func) for name,func in globals().items() if 'test_' in name]:
        if 'opt_' in name:
            alt = "--enable-%s"%(name.split('_', 3)[3].replace('_','-'))
            parser.add_argument(alt, action='store_false', dest=name, help="Enable: %s"%(inspect.getdoc(func)))
        else:
            alt = "--skip-%s"%(name.split('_', 2)[2].replace('_','-'))
            parser.add_argument(alt, action='store_true', dest=name, help="Skip: %s"%(inspect.getdoc(func)))
        argspec = inspect.getargspec(func)
        for ( number, name ) in enumerate(argspec.args):
            if not name == "IP":
                alt = "--%s"%(name.replace('_','-'))
                if isinstance(argspec.defaults[number], int):
                    parser.add_argument(alt, action='store', type=int, dest=name, help="Default: {}".format(argspec.defaults[number]), default=argspec.defaults[number])
                else:
                    parser.add_argument(alt, action='store', dest=name, default=argspec.defaults[number])
    args = parser.parse_args()
    
    pidns.nameservers = [ args.IP ]
    if run_tests(**args.__dict__):
        if not args.quiet: print("All tests pass on %s"%(args.IP))
    else:
        print("Testing failed on %s"%(args.IP))
        sys.exit(-1)

if __name__ == "__main__": main()


