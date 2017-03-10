#!/usr/bin/python

# EPITHAL
# Defines various functions for use in main loop.

import eveapi
import json
import os
import re

names={}

def showlogo():
	print
	print "	(E)ve"
	print "	(P)ython"
	print "	(I)ndustrial"
	print "	(T)ool"
	print "	(H)elper"
	print "	(A)nd"
	print "	(L)ogic"

	
def loaditems():
	# pull all market items from ESI
	json_file=eveapi.pullfromcache("markets/prices/",3600)
	with open(json_file) as json_data:
		items=json.load(json_data)
		return items

def loadnames():
	global names
	json_file=os.path.join("ep_data","names.json")
	with open(json_file) as json_data:
		names=json.load(json_data)
		return names
		
def showmainmenu():
	print
	print "(1) Define new product"
	print "(2) Market analysis on products"
	print "(3) Check sell orders for an item"
	print "(10) Quit"
	print

def loadtradehubs():
	hubsfile = os.path.join("ep_data","tradehubs.json")
	if not os.path.exists(hubsfile):
		print "No trade hubs defined."
		return 0
	else:
		with open(hubsfile) as hub_data:
			tradehubs=json.load(hub_data)
			return tradehubs

def getname(typeid):
	return names[typeid]
	
def gettypeid(name):
	i = 0
	while i < len(names):
		if name.lower() == names[i].lower():
			return i
		i+=1
	return -1
	
def takenameinput(prompt):
	partialmatches = []
	typeid = 0
	typename=raw_input(prompt)
	if len(typename) > 0:
		typeid = gettypeid(typename)
		return typeid
	if typeid<1:
		i = 0
		regpat = re.compile(typename)
		while i < len(names) and len(partialmatches)<40:
			if regpat.search(names[i].lower()):
				partialmatches.append(names[i])
			i+=1
		if len(partialmatches)>0:
			j=0
			print "Partial matches for ("+typename+")"
			for match in partialmatches:
				j+=1
				print str(j)+") "+match
			print
			matchid=raw_input("Choose a partial match: ")
			try:
				if not int(matchid):
					raise ValueError()
				else: 
					matchidi=int(matchid)-1
					if matchidi < j:
						return gettypeid(partialmatches[matchidi])
			except ValueError:
				return -1
			