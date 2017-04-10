#!/usr/bin/python

import json
import os

with open('blueprints.json') as json_data:
	blueprints=json.load(json_data)
	
	i=0
	
	while i < 50000:
		try:
			blueprint = blueprints[str(i)]
			outpath=os.path.join("ep_data","blueprints","blueprint_"+str(i)+".json")
			with open(outpath,'w') as outfile:
				json.dump(blueprint,outfile)
				outfile.close()
		except KeyError:
			print "skipping"
		i+=1
		#raw_input("Enter for next")