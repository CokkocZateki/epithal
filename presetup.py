#!/usr/bin/python

# EPITHAL
# pre-setup functions
# These were used to build the names.json included with EPTITHAL
# It will likely not be needed to use these until CCP adds more
# items to EvE industry.

import json
import os
import eveapi

def inititemandnames():
	# pull all market items from ESI
	json_file=eveapi.pullfromcache("markets/prices/")
	with open(json_file) as json_data:
		data=json.load(json_data)

	# above list comes with no human-readable names, make an array to hold those
	names = [""]*50000

	# we must sadly pull each name from API individually
	for item in data:
		item.setdefault("adjusted_price",-1.0)
		json_file2=eveapi.pullfromcache("universe/types/"+str(item["type_id"]),-1)
		typeid=item["type_id"]
		with open(json_file2) as json_data2:
			data2=json.load(json_data2)
			names[typeid] = data2["name"]

	# finally, save the resulting array of names
	if not os.path.exists("ep_data"):
		os.makedirs("ep_data")

	namesfile=os.path.join("ep_data","names.json")

	with open (namesfile, 'w') as outfile:
		json.dump(names,outfile)
		outfile.close()