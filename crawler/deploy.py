#!/bin/python

import subprocess, json, sys, pystache
sys.path.append('../lib')
import config_hci
from shutil import copyfile
from contextlib import nested

config = config_hci.load_config()
if not config:
    exit()

# Copy LRU library from HCI lib/
print "Importing lru.py library from HCI /lib to hcicrawler..."
try:
    copyfile("../lib/lru.py", "hcicrawler/lru.py")
except IOError as e:
    print "Could not open either source or destination lru.py file"
    print "lib/lru.py", "crawler/hcicrawler/lru.py"
    print e
    exit()
 
# Render the proxy middleware settings (hcicrawler/middlewares.py) from template with mongo/scrapy proxy config from config.json when defined
print "Rendering hcicrawler/middlewares.py with proxy config values from config.json..."
proxyconf = {'host': '', 'port': 3128}
if "proxy_host" in config['mongo-scrapy']:
    proxyconf['host'] = config['mongo-scrapy']['proxy_host']
if "proxy_port" in config['mongo-scrapy']:
    proxyconf['port'] = config['mongo-scrapy']['proxy_port']
try:
    with nested(open("hcicrawler/middlewares-template.py", "r"), open("hcicrawler/middlewares.py", "w")) as (template, generated):
        generated.write(pystache.render(template.read(), proxyconf))
except IOError as e:
    print "Could not open either crawler/hcicrawler/middlewares-template.py file or crawler/hcicrawler/middlewares.py"
    print e
    exit()

# Render the settings py from template with mongo/scrapy config from config.json
print "Rendering settings.py with mongo-scrapy config values from config.json..."
try:
    with nested(open("hcicrawler/settings-template.py", "r"), open("hcicrawler/settings.py", "w")) as (template, generated):
        generated.write(pystache.render(template.read(), config['mongo-scrapy']))
except IOError as e:
    print "Could not open either crawler/hcicrawler/settings-template.py file or crawler/hcicrawler/settings.py"
    print e
    exit()

# Render the scrapy cfg from template with scrapy config from config.json
print "Rendering scrapy.cfg with scrapy config values from config.json..."
try:
    with nested(open("scrapy-template.cfg", "r"), open("scrapy.cfg", "w")) as (template, generated):
        generated.write(pystache.render(template.read(), config['mongo-scrapy']))
except IOError as e:
    print "Could not open either crawler/scrapy-template.cfg template file or crawler/scrapy.cfg"
    print e
    exit()

# Deploy the egg
print "Sending HCI's scrapy egg to scrapyd server..."
p = subprocess.Popen(['scrapy', 'deploy'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, errors = p.communicate()
print output, errors
try :
    output = json.loads(output)
    if output['status'] != "ok" :
        print "There was a problem sending the scrapy egg."
        print output, errors
        exit()
except ValueError:
    print "There was a problem sending the scrapy egg."
    print output, errors
    exit()
print "The egg was successfully sent to scrapyd server", config['mongo-scrapy']['host'], "on port", config['mongo-scrapy']['scrapy_port']
 
