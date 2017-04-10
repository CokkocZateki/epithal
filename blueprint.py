#!/usr/bin/python

import json
import yaml

with open('blueprints.yaml') as yaml_data:
	blueprints=yaml.load(yaml_data)
	
	with open ('blueprints.json', 'w') as outfile:
			json.dump(blueprints,outfile)
			outfile.close()
	