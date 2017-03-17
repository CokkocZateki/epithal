#!/usr/bin/python

# EPITHAL
# Functions related to ESI API calls.

import time
import os
import sys
import urllib2

# Name is somewhat misleading
# Searches cache for a given APi result
# If it's missing or old, as defined by cachetime,
# Then pulls the data from ESI
def pullfromcache(urlstring,cachetime):
	cachestale=False
	cachefile=urlstring.replace("/","_").replace("?","_")
	cachedir="ep_cache"
	if not os.path.exists(cachedir):
		os.makedirs(cachedir)
	cachepath=os.path.join(cachedir,cachefile)
	if os.path.isfile(cachepath):
		if(cachetime>0):
			stats=os.stat(cachepath)
			mtime=int(stats.st_mtime)
			if(time.time() > mtime+cachetime):
#				print "Discarding stale cache for "+urlstring+
#				print mtime 
#				print time.time()
				cachestale=True
	else:
		cachestale=True
	if cachestale==True:
		try:
			url="https://esi.tech.ccp.is/latest/"+urlstring
			response=urllib2.urlopen(url)
			web_data=response.read()
			clean_data=web_data.replace("\u2018","'")
			clean_data=clean_data.replace("\u2013","-")
			clean_data=clean_data.replace("\u2019","'")
			clean_data=clean_data.replace("\u201c","'")
			clean_data=clean_data.replace("\u201d","'")
			with open(cachepath,"w") as outfile:
				outfile.write(clean_data)
				outfile.close()
		except URLError:
			print "Fatal Error: Cannot connect to ESI API."
			sys.exit()
			
	return cachepath