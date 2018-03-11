from feedparser import parse
from filecmp import cmp
from urllib.request import urlretrieve
from sdn_parser import parse_to_file
from subprocess import run
from os import path
from sys import argv

RSS_FEED_URL = 'https://www.treasury.gov/resource-center/sanctions/OFAC-Enforcement/Documents/ofac.xml'
SDN_XML_URL  = 'https://www.treasury.gov/ofac/downloads/sanctions/1.0/sdn_advanced.xml'
DIR          = path.dirname(path.realpath(__file__))
NEW_RSS_FILE = DIR + '/update_files/rss_new.txt'
OLD_RSS_FILE = DIR + '/update_files/rss_old.txt'
SDN_XML_FILE = DIR + '/update_files/sdn_advanced.xml'
SDN_JSON     = DIR + '/update_files/latest.json'
EXPORT_SDN   = DIR + '/export_sdn.js'
EXPORT_PRS   = DIR + '/export_prs.js'

def error(msg):
	# send Twilio text
	print(msg)
	quit()

def serialize_feed(feed, filename):
	try:
		with open(filename, 'w') as f:
			for item in feed['items']:
				f.write(str(item['published']) + '\n')
	except Exception as e:
		error(e)

def run_nodejs(filename, task):
	try:
		run(['node', filename])
	except Exception as e:
		error('ERROR: Failed to ' + task + ': ' + str(e))


#### SDN XML ####
feed = parse(RSS_FEED_URL)
serialize_feed(feed, NEW_RSS_FILE)

force_update = len(argv) > 1 and (argv[1] == '--force' or argv[1] == '-f')

try:
	unchanged = cmp(OLD_RSS_FILE, NEW_RSS_FILE)
except:
	unchanged = False

if unchanged and not force_update:
	quit()

print('Downloading new sanctions data...')
try:
	urlretrieve(SDN_XML_URL, SDN_XML_FILE)
	print('Downloaded!')
	print('Parsing...')
	parse_to_file(SDN_XML_FILE, SDN_JSON)
	print('Parsed!')
except Exception as e:
	error('Error while parsing: ' + str(e))

# By now, we have the new SDN data in JSON format.

run_nodejs(EXPORT_SDN, 'export SDN to Elastic')


#### Press Releases ####
# 3. Scrape latest press releases, placing into entries.json or some other intermediate file

# 4. Call export_prs.js, which consumes entries.json and imports into Elastic
run_nodejs(EXPORT_PRS, 'export PRs to Elastic')

# 5. Call the PR matching program, which downloads a list of names from Elastic,
#    matches with `content` entries in entries.json, and writes the result to the Elastic SDN index.


# If we've successfully made it this far, we write this for next time.
serialize_feed(feed, OLD_RSS_FILE)
